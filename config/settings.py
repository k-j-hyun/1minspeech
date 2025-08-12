import os
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에서)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-flowmate-2024'
    PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    UPSTAGE_API_KEY = os.environ.get('UPSTAGE_API_KEY')
    
    # 폴더 설정 (상대 경로)
    UPLOAD_FOLDER = 'uploads'
    DOWNLOAD_FOLDER = 'downloads'
    
    # 파일 업로드 제한
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 지원하는 파일 확장자
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
    
    @classmethod
    def validate_config(cls):
        """설정 검증"""
        missing_keys = []
        
        if not cls.GROQ_API_KEY:
            missing_keys.append('GROQ_API_KEY')
        if not cls.PINECONE_API_KEY:
            missing_keys.append('PINECONE_API_KEY')
        if not cls.UPSTAGE_API_KEY:
            missing_keys.append('UPSTAGE_API_KEY')
            
        if missing_keys:
            raise ValueError(f"다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_keys)}")
        
        return True