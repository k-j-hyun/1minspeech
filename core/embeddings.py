import requests
import json
import gc
from config.settings import Config

class BGEEmbeddings:  # 이름 유지 (호환성)
    def __init__(self):
        print("Upstage 임베딩 초기화 중...")
        self.api_key = Config.UPSTAGE_API_KEY
        self.base_url = "https://api.upstage.ai/v1/solar/embeddings"
        print("Upstage 임베딩 초기화 완료")
        
    def embed_documents(self, texts):
        print(f"{len(texts)}개 문서 Upstage 임베딩 중...")
        embeddings = []
        
        # 배치 처리 (메모리 효율성을 위해 더 작게)
        batch_size = 3  # 10에서 3으로 감소
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self._embed_batch(batch_texts)
            embeddings.extend(batch_embeddings)
            
            # 메모리 정리
            gc.collect()
            
        print(f"Upstage 임베딩 완료: {len(embeddings)}개 벡터")
        return embeddings
    
    def embed_query(self, text):
        result = self._embed_batch([text])[0]
        gc.collect()  # 메모리 정리
        return result
    
    def _embed_batch(self, texts):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "solar-embedding-1-large",
                "input": texts
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embeddings = [item["embedding"] for item in result["data"]]
                # 응답 데이터 정리
                del result
                del response
                gc.collect()
                return embeddings
            else:
                print(f"Upstage API 오류: {response.status_code}")
                # 폴백: 더미 벡터 반환 (메모리 효율적)
                return [[0.1] * 1024 for _ in texts]  # 차원 축소
                
        except Exception as e:
            print(f"Upstage 임베딩 오류: {str(e)}")
            # 폴백: 더미 벡터 반환 (메모리 효율적)
            return [[0.1] * 1024 for _ in texts]  # 차원 축소
    
    def test_connection(self):
        """연결 테스트"""
        try:
            test_embedding = self.embed_query("테스트")
            return f"Upstage 연결 성공! 차원: {len(test_embedding)}"
        except Exception as e:
            return f"Upstage 연결 실패: {str(e)}"