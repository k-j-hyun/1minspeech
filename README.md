# FlowMate - Simple RAG System

Upstage Embeddings와 Groq LLM을 사용한 간단한 RAG(Retrieval-Augmented Generation) 시스템입니다.

## 주요 기능

- 문서 업로드 (PDF, DOCX, TXT 지원)
- 임베딩 기반 문서 검색
- AI 챗봇과 대화
- AI 보고서 생성 및 다운로드
- 컨텍스트 기반 답변 생성

## 시스템 구성

- **Frontend**: HTML, CSS, JavaScript (Bootstrap)
- **Backend**: Flask (Python)
- **Embeddings**: Upstage Solar-large-3
- **LLM**: Groq LLaMA-3.1-8b-instant
- **Vector Store**: Pinecone
- **File Processing**: PyPDF2, python-docx

## 설치 및 실행

### 1. 환경 설정

```bash
# 가상환경 생성 (권장)
python -m venv sooc
source sooc/bin/activate  # Windows: sooc\\Scripts\\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정

`.env` 파일이 이미 설정되어 있습니다. 필요시 다음 키들을 확인하세요:

```env
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
UPSTAGE_API_KEY=your_upstage_api_key
SECRET_KEY=your_secret_key
```

### 3. 실행

#### 방법 1: 직접 실행
```bash
python app.py
```

#### 방법 2: 실행 스크립트 사용
```bash
python run_app.py
```

#### 방법 3: 테스트 후 실행
```bash
# 먼저 테스트 실행
python test/test_app.py

# 문제없으면 앱 실행
python app.py
```

### 4. 사용법

1. 브라우저에서 `http://localhost:5000` 접속
2. 문서 파일 업로드 (PDF, DOCX, TXT)
3. 업로드 완료 후 질문 입력
4. AI와 대화하거나 보고서 생성

## 문제 해결

### 파일 업로드가 안되는 경우

1. **파일 형식 확인**: PDF, DOCX, DOC, TXT 파일만 지원
2. **파일 크기 확인**: 16MB 이하만 가능
3. **폴더 권한 확인**: uploads, downloads 폴더 쓰기 권한 필요
4. **API 키 확인**: UPSTAGE_API_KEY와 PINECONE_API_KEY 설정 확인

### 일반적인 오류 해결

```bash
# 테스트 스크립트로 문제 진단
python test/test_app.py

# 누락된 패키지 설치
pip install -r requirements.txt

# 폴더 권한 문제 해결 (Windows)
# 관리자 권한으로 실행하거나 폴더 권한 변경
```

### API 연결 오류

1. `.env` 파일의 API 키들이 정확한지 확인
2. 인터넷 연결 상태 확인
3. API 키 유효성 및 잔액 확인

## 폴더 구조

```
flowmate/
├── app.py                 # 메인 Flask 애플리케이션
├── run_app.py            # 실행 스크립트
├── requirements.txt      # 의존성 목록
├── .env                 # 환경 변수
├── config/
│   └── settings.py      # 설정 파일
├── core/
│   ├── embeddings.py    # Upstage 임베딩
│   ├── vector_store.py  # Pinecone 벡터 스토어
│   ├── llm_handler.py   # Groq LLM 핸들러
│   └── memory.py        # 대화 메모리
├── utils/
│   ├── file_parser.py   # 파일 텍스트 추출
│   ├── chunking.py      # 텍스트 분할
│   ├── docx_generator.py # DOCX 보고서 생성
│   └── txt_generator.py # TXT 보고서 생성
├── templates/
│   ├── base.html        # 기본 템플릿
│   └── index.html       # 메인 페이지
├── static/
│   ├── css/style.css    # 스타일시트
│   └── js/main.js       # JavaScript
├── uploads/             # 업로드된 파일
├── downloads/           # 생성된 보고서
└── test/
    └── test_app.py      # 테스트 스크립트
```

## 개발자 정보

- **임베딩**: Upstage Solar-large-3 (4096 차원)
- **모델**: Groq LLaMA-3.1-8b-instant
- **프레임워크**: Flask 2.3.3
- **벡터 DB**: Pinecone

## 라이선스

MIT License

## 업데이트 내역

### v1.1.0 (현재)
- 파일 업로드 에러 처리 개선
- 중복 파일명 자동 처리
- 파일 크기 및 형식 검증 강화
- 더 나은 사용자 피드백
- 테스트 스크립트 추가
- 실행 스크립트 추가

### v1.0.0
- 기본 RAG 시스템 구현
- 파일 업로드 및 텍스트 추출
- AI 챗봇 기능
- 보고서 생성 기능
"# 1minspeech" 
