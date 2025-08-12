"""
FlowMate 애플리케이션 테스트 스크립트
"""
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """모든 필요한 모듈들이 정상적으로 import되는지 테스트"""
    print("=== Import 테스트 ===")
    
    try:
        from config.settings import Config
        print("✅ Config import 성공")
    except Exception as e:
        print(f"❌ Config import 실패: {e}")
        return False
    
    try:
        from core.embeddings import BGEEmbeddings
        print("✅ BGEEmbeddings import 성공")
    except Exception as e:
        print(f"❌ BGEEmbeddings import 실패: {e}")
        return False
    
    try:
        from core.vector_store import PineconeVectorStore
        print("✅ PineconeVectorStore import 성공")
    except Exception as e:
        print(f"❌ PineconeVectorStore import 실패: {e}")
        return False
    
    try:
        from core.llm_handler import GroqLLM
        print("✅ GroqLLM import 성공")
    except Exception as e:
        print(f"❌ GroqLLM import 실패: {e}")
        return False
    
    try:
        from core.memory import BufferMemory
        print("✅ BufferMemory import 성공")
    except Exception as e:
        print(f"❌ BufferMemory import 실패: {e}")
        return False
    
    try:
        from utils.file_parser import extract_text_from_file
        print("✅ file_parser import 성공")
    except Exception as e:
        print(f"❌ file_parser import 실패: {e}")
        return False
    
    return True

def test_config():
    """설정 파일 테스트"""
    print("\n=== Config 테스트 ===")
    
    try:
        from config.settings import Config
        
        # 필수 설정값 확인
        if hasattr(Config, 'SECRET_KEY') and Config.SECRET_KEY:
            print("✅ SECRET_KEY 설정됨")
        else:
            print("❌ SECRET_KEY 누락")
            
        if hasattr(Config, 'GROQ_API_KEY') and Config.GROQ_API_KEY:
            print("✅ GROQ_API_KEY 설정됨")
        else:
            print("❌ GROQ_API_KEY 누락")
            
        if hasattr(Config, 'PINECONE_API_KEY') and Config.PINECONE_API_KEY:
            print("✅ PINECONE_API_KEY 설정됨")
        else:
            print("❌ PINECONE_API_KEY 누락")
            
        if hasattr(Config, 'UPSTAGE_API_KEY') and Config.UPSTAGE_API_KEY:
            print("✅ UPSTAGE_API_KEY 설정됨")
        else:
            print("❌ UPSTAGE_API_KEY 누락")
            
        return True
    except Exception as e:
        print(f"❌ Config 테스트 실패: {e}")
        return False

def test_folders():
    """필요한 폴더들이 존재하는지 확인"""
    print("\n=== 폴더 존재 확인 ===")
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    folders_to_check = [
        'uploads',
        'downloads',
        'templates',
        'static',
        'static/css',
        'static/js',
        'core',
        'utils',
        'config'
    ]
    
    all_exists = True
    for folder in folders_to_check:
        folder_path = os.path.join(base_dir, folder)
        if os.path.exists(folder_path):
            print(f"✅ {folder} 폴더 존재")
        else:
            print(f"❌ {folder} 폴더 누락")
            all_exists = False
    
    return all_exists

def test_dependencies():
    """필요한 패키지들이 설치되어 있는지 확인"""
    print("\n=== 패키지 의존성 확인 ===")
    
    required_packages = [
        'flask',
        'pinecone',
        'requests',
        'docx',
        'PyPDF2',
        'dotenv',
        'huggingface_hub',
        'werkzeug'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} 설치됨")
        except ImportError:
            print(f"❌ {package} 누락")
            all_installed = False
    
    return all_installed

def test_file_parser():
    """파일 파서 테스트"""
    print("\n=== 파일 파서 테스트 ===")
    
    try:
        from utils.file_parser import extract_text_from_file
        
        # 테스트 텍스트 파일 생성
        test_file_path = os.path.join(os.path.dirname(__file__), 'test.txt')
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write("이것은 테스트 파일입니다.")
        
        # 텍스트 추출 테스트
        extracted_text = extract_text_from_file(test_file_path)
        if "테스트 파일" in extracted_text:
            print("✅ 텍스트 파일 추출 성공")
        else:
            print("❌ 텍스트 파일 추출 실패")
        
        # 테스트 파일 삭제
        os.remove(test_file_path)
        
        return True
    except Exception as e:
        print(f"❌ 파일 파서 테스트 실패: {e}")
        return False

def main():
    """전체 테스트 실행"""
    print("FlowMate 애플리케이션 테스트를 시작합니다...\n")
    
    tests = [
        test_imports,
        test_config,
        test_folders,
        test_dependencies,
        test_file_parser
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"=== 테스트 결과 ===")
    print(f"통과: {passed}/{total}")
    
    if passed == total:
        print("✅ 모든 테스트 통과! 애플리케이션 실행 준비 완료")
        return True
    else:
        print("❌ 일부 테스트 실패. 문제를 해결한 후 다시 시도하세요.")
        return False

if __name__ == "__main__":
    main()
