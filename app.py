from flask import Flask, render_template, request, jsonify, send_file, session
import os
import sys
import uuid
import gc
from werkzeug.utils import secure_filename

from config.settings import Config
from core.embeddings import BGEEmbeddings
from core.vector_store import PineconeVectorStore
from core.llm_handler import GroqLLM  # 변경됨
from core.memory import BufferMemory
from utils.file_parser import extract_text_from_file
from utils.chunking import simple_text_splitter
from utils.docx_generator import generate_docx_report
from utils.txt_generator import generate_txt_report

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# 메모리 최적화 설정
os.environ['PYTHONHASHSEED'] = '0'  # 해시 시드 고정

# 절대 경로로 폴더 설정
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

print("메모리 최적화 모드로 시작")

# 설정 검증
try:
    Config.validate_config()
    print("모든 API 키가 설정되어 있습니다.")
except ValueError as e:
    print(f"설정 오류: {e}")
    print(".env 파일을 확인하고 애플리케이션을 다시 시작하세요.")
    sys.exit(1)

# 전역 객체 초기화
embeddings = BGEEmbeddings()
vector_store = PineconeVectorStore(embeddings)
llm = GroqLLM()  # 변경됨

# 오래된 인덱스 정리 (시작 시)
print("🧹 오래된 Pinecone 인덱스 정리 중...")
vector_store.cleanup_old_indexes()

# 메모리 저장소 (간단한 세션 기반)
memories = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """파일 업로드 및 벡터화"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '파일이 없습니다.'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '파일이 선택되지 않았습니다.'})
        
        # 파일 확장자 검사
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'message': f'지원하지 않는 파일 형식입니다. 지원 형식: {list(allowed_extensions)}'})
        
        # 파일 크기 검사 (16MB 제한)
        if len(file.read()) > app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024):
            return jsonify({'success': False, 'message': '파일 크기가 너무 큽니다. (16MB 제한)'})
        
        # 파일 포인터 리셋
        file.seek(0)
        
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({'success': False, 'message': '유효하지 않은 파일 이름입니다.'})
        
        # 중복 파일명 처리
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        counter = 1
        original_name, ext = os.path.splitext(filename)
        while os.path.exists(file_path):
            filename = f"{original_name}_{counter}{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            counter += 1
        
        file.save(file_path)
        
        # 텍스트 추출 및 청킹
        print(f"파일 처리 시작: {filename}")
        text = extract_text_from_file(file_path)
        
        if not text or len(text.strip()) < 10:
            os.remove(file_path)  # 실패한 파일 삭제
            return jsonify({'success': False, 'message': '파일에서 충분한 텍스트를 추출할 수 없습니다.'})
        
        print(f"텍스트 추출 완료: {len(text)} 문자")
        chunks = simple_text_splitter(text)
        
        # 메모리 정리
        del text
        gc.collect()
        
        if not chunks:
            os.remove(file_path)
            return jsonify({'success': False, 'message': '텍스트를 청크로 분할할 수 없습니다.'})
        
        print(f"청크 분할 완료: {len(chunks)}개")
        chunks_count = len(chunks)  # 청크 수 저장
        
        # 벡터스토어에 저장 (세션 ID 전달)
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        
        metadatas = [{'source': filename, 'chunk_id': i, 'total_chunks': chunks_count, 'session_id': session_id} for i in range(chunks_count)]
        vector_store.add_documents(chunks, metadatas, session_id=session_id)
        
        # 메모리 정리
        del chunks
        del metadatas
        gc.collect()
        
        print(f"벡터 스토어 추가 완료: {filename} (인덱스: {vector_store.index_name})")
        
        # 세션에 파일 정보 저장
        session['uploaded_file'] = filename
        
        return jsonify({
            'success': True, 
            'message': f'{filename} 업로드 완료 ({chunks_count}개 청크 생성)',
            'file_path': filename,
            'chunks_count': chunks_count
        })
        
    except Exception as e:
        # 오류 때 파일 정리
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return jsonify({'success': False, 'message': f'처리 오류: {str(e)}'})

@app.route('/chat', methods=['POST'])
def chat():
    """RAG 기반 채팅 (파일 업로드 없이도 일반 대화 가능)"""
    data = request.json
    query = data.get('query', '')
    
    # 세션 기반 메모리 관리
    session_id = session.get('session_id', str(uuid.uuid4()))
    session['session_id'] = session_id
    
    if session_id not in memories:
        memories[session_id] = BufferMemory()
    
    memory = memories[session_id]
    
    try:
        # 관련 문서 검색 (업로드된 파일이 있는 경우에만)
        relevant_docs = []
        context = ""
        has_uploaded_file = bool(session.get('uploaded_file'))
        
        if has_uploaded_file:
            try:
                relevant_docs = vector_store.similarity_search(query, k=3)
                context = "\n\n".join(relevant_docs)
            except Exception as search_error:
                print(f"문서 검색 오류: {search_error}")
                # 검색 오류가 있어도 일반 대화는 계속 진행
        
        # 대화 히스토리
        history = memory.get_formatted_history()
        
        # 프롬프트 구성 (문서 유무에 따라 다르게)
        if context:
            # 문서가 있는 경우: RAG 기반 답변
            prompt = f"""
당신은 친절한 AI 어시스턴트입니다. 업로드된 문서를 참고하여 사용자의 질문에 답변해주세요.

대화 히스토리:
{history}

참고 문서:
{context}

사용자 질문: {query}

답변:"""
        else:
            # 문서가 없는 경우: 일반 AI 어시스턴트로 동작
            prompt = f"""
당신은 친절하고 도움이 되는 AI 어시스턴트입니다. 사용자의 질문에 정확하고 유용한 답변을 제공해주세요.

대화 히스토리:
{history}

사용자 질문: {query}

답변:"""
        
        # LLM 응답 생성
        response = llm.generate(prompt, max_tokens=1024)
        
        # 메모리에 저장
        memory.append(query, response)
        
        return jsonify({
            'success': True,
            'response': response,
            'has_context': bool(relevant_docs),
            'has_uploaded_file': has_uploaded_file
        })
        
    except Exception as e:
        print(f"채팅 처리 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'처리 오류: {str(e)}'})

@app.route('/generate_report', methods=['POST'])
def generate_report():
    """보고서 생성 - 1분 스피치 형태"""
    data = request.json
    query = data.get('query', '업로드된 문서를 바탕으로 1분 스피치를 작성해주세요. 단, 반드시 바이어들이 하는 말로 작성을 해주세요.')
    format_type = data.get('format', 'docx')  # docx 또는 txt
    
    try:
        print(f"보고서 생성 시작: {query}")
        
        # 관련 문서 검색 (더 많은 문서)
        relevant_docs = vector_store.similarity_search(query, k=5)
        
        if not relevant_docs:
            # 업로드된 파일이 있는지 확인
            uploaded_file = session.get('uploaded_file')
            if uploaded_file:
                # 기본 검색어로 다시 시도
                relevant_docs = vector_store.similarity_search("문서 내용 요약", k=5)
        
        context = "\n\n".join(relevant_docs) if relevant_docs else "업로드된 문서 내용을 찾을 수 없습니다."
        
        print(f"참고 문서 {len(relevant_docs)}개 발견")
        
        # 1분 스피치에 맞는 보고서 생성 프롬프트
        prompt = f"""다음 문서를 바탕으로 1분 스피치를 작성해주세요.

참고 문서:
{context}

요청사항: {query}

1분 스피치 작성 가이드라인:
- 반드시 바이어들이 하는말로 작성
- 대략 200-250단어 (한글 300-400자)
- 명확한 주제와 결론
- 간결하고 인상적인 메시지
- 청중의 관심을 끄는 시작
- 기억에 남는 마무리

1분 스피치:
"""
        
        # LLM으로 보고서 생성
        print("보고서 내용 생성 중...")
        report_content = llm.generate(prompt, max_tokens=1024)
        
        if not report_content or len(report_content.strip()) < 50:
            # 폴백 보고서 생성
            report_content = f"""주간 회의 1분 스피치

안녕하세요, 여러분.

오늘은 업로드된 문서 '{session.get('uploaded_file', '문서')}'를 바탕으로 말씨드리겠습니다.

주요 내용:
{context[:200] if context else '문서 내용을 분석 중입니다.'}

결론적으로, 이 내용을 바탕으로 향후 계획을 수립하도록 하겠습니다.

감사합니다."""
        
        print(f"보고서 내용 생성 완료: {len(report_content)}문자")
        
        # 파일 생성
        file_id = str(uuid.uuid4())[:8]  # 짧은 ID
        if format_type == 'docx':
            filename = f"1분_스피치_{file_id}.docx"
            file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
            generate_docx_report(report_content, file_path)
        else:
            filename = f"1분_스피치_{file_id}.txt"
            file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
            generate_txt_report(report_content, file_path)
        
        print(f"보고서 파일 생성 완료: {filename}")
        
        # 메모리 정리
        del relevant_docs, context, prompt
        gc.collect()
        
        return jsonify({
            'success': True,
            'content': report_content,
            'download_url': f'/download/{filename}',
            'filename': filename
        })
        
    except Exception as e:
        print(f"보고서 생성 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'보고서 생성 오류: {str(e)}'})

@app.route('/cleanup_session', methods=['POST'])
def cleanup_session():
    """세션 종료 시 Pinecone 인덱스 정리"""
    try:
        # 현재 인덱스 삭제
        if vector_store.index_name:
            vector_store.delete_current_index()
            print(f"세션 종료: Pinecone 인덱스 삭제 완료")
        
        # 세션 데이터 정리
        session.clear()
        
        # 메모리 정리
        gc.collect()
        
        return jsonify({'success': True, 'message': '세션이 정리되었습니다.'})
        
    except Exception as e:
        print(f"세션 정리 오류: {e}")
        return jsonify({'success': False, 'message': f'세션 정리 오류: {str(e)}'})

@app.route('/restart_session', methods=['POST'])
def restart_session():
    """새로운 세션 시작 (기존 인덱스 삭제 후)"""
    try:
        # 기존 인덱스 삭제
        if vector_store.index_name:
            old_index = vector_store.index_name
            vector_store.delete_current_index()
            print(f"새 세션 시작: 기존 인덱스 {old_index} 삭제")
        
        # 세션 데이터 초기화
        session.clear()
        
        # 새 세션 ID 생성
        new_session_id = str(uuid.uuid4())
        session['session_id'] = new_session_id
        
        # 메모리 정리
        gc.collect()
        
        return jsonify({
            'success': True, 
            'message': '새로운 세션이 시작되었습니다.',
            'session_id': new_session_id
        })
        
    except Exception as e:
        print(f"세션 재시작 오류: {e}")
        return jsonify({'success': False, 'message': f'세션 재시작 오류: {str(e)}'})

@app.route('/download/<filename>')
def download_file(filename):
    """파일 다운로드"""
    file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

if __name__ == '__main__':
    # 메모리 최적화 모드 안내
    print("FlowMate 메모리 최적화 모드")
    print("주요 개선사항:")
    print("   - 임베딩 배치 크기: 10 → 3")
    print("   - 임베딩 차원: 4096 → 1024")
    print("   - 청크 크기: 1000 → 500")
    print("   - 최대 청크 수: 무제한 → 20개")
    print("   - 1분 스피치 전용 보고서")
    print("   - 강화된 메모리 관리")
    print("   - 파일 업로드 없이도 일반 대화 가능")
    print("Pinecone 무료 버전 최적화:")
    print("   - 세션별 임시 인덱스 생성")
    print("   - 파일 업로드 시 기존 인덱스 삭제")
    print("   - 세션 종료 시 자동 인덱스 정리")
    print("   - 오래된 인덱스 자동 삭제 (1시간 후)")
    print()
    
    # 필요한 폴더 생성
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Download folder: {DOWNLOAD_FOLDER}")
    
    # 초기화 테스트
    try:
        print("\n=== 초기화 테스트 ===\n")
        print(embeddings.test_connection())
        print(llm.test_connection())
        print("\n=== 서버 시작 ===")
        print("브라우저에서 http://localhost:5000 접속")
        print("Pinecone 무료 버전: 세션별 인덱스 자동 관리")
        print("새로운 파일 업로드 시 기존 데이터 자동 삭제")
        print("종료하려면 Ctrl+C")
        print()
    except Exception as e:
        print(f"초기화 오류: {e}")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n애플리케이션 종료 중...")
        # 종료 시 Pinecone 인덱스 정리
        try:
            if vector_store.index_name:
                print(f"종료 시 Pinecone 인덱스 삭제: {vector_store.index_name}")
                vector_store.delete_current_index()
        except Exception as cleanup_error:
            print(f"인덱스 정리 오류: {cleanup_error}")
        
        print("애플리케이션이 안전하게 종료되었습니다.")