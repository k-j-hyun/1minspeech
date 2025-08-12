from pinecone import Pinecone, ServerlessSpec
from config.settings import Config
import uuid
import gc
import time

class PineconeVectorStore:
    def __init__(self, embeddings):
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.embeddings = embeddings
        # 세션별 유니크 인덱스 이름 (무료 버전 최적화)
        self.index_name = None
        self.index = None
    
    def create_new_index(self, session_id=None):
        """새로운 인덱스 생성 (Pinecone 무료 버전용)"""
        # 기존 인덱스 삭제
        if self.index_name:
            self.delete_current_index()
        
        # 새 인덱스 이름 생성
        timestamp = str(int(time.time()))
        session_part = session_id[:8] if session_id else str(uuid.uuid4())[:8]
        self.index_name = f"temp-{session_part}-{timestamp}"
        
        print(f"🆕 새 Pinecone 인덱스 생성: {self.index_name}")
        
        try:
            # 인덱스 생성
            self.pc.create_index(
                name=self.index_name,
                dimension=1024,  # 메모리 효율성을 위해 차원 축소
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            
            # 인덱스 준비될 때까지 대기
            while self.index_name not in [idx.name for idx in self.pc.list_indexes()]:
                time.sleep(1)
            
            self.index = self.pc.Index(self.index_name)
            print(f"✅ Pinecone 인덱스 준비 완료: {self.index_name}")
            return True
            
        except Exception as e:
            print(f"❌ Pinecone 인덱스 생성 실패: {e}")
            return False
    
    def delete_current_index(self):
        """현재 인덱스 삭제 (Pinecone 무료 버전 비용 절약)"""
        if not self.index_name:
            return True
            
        try:
            print(f"🗑️ Pinecone 인덱스 삭제 중: {self.index_name}")
            
            # 인덱스 삭제
            self.pc.delete_index(self.index_name)
            
            # 삭제 완료될 때까지 대기
            while self.index_name in [idx.name for idx in self.pc.list_indexes()]:
                time.sleep(1)
            
            print(f"✅ Pinecone 인덱스 삭제 완료: {self.index_name}")
            
            self.index_name = None
            self.index = None
            return True
            
        except Exception as e:
            print(f"⚠️ Pinecone 인덱스 삭제 실패 (무시): {e}")
            return False
    
    def cleanup_old_indexes(self):
        """오래된 임시 인덱스들 정리"""
        try:
            indexes = self.pc.list_indexes()
            current_time = int(time.time())
            
            for idx in indexes:
                if idx.name.startswith('temp-'):
                    # 인덱스 이름에서 타임스탬프 추출
                    parts = idx.name.split('-')
                    if len(parts) >= 3:
                        try:
                            index_time = int(parts[-1])
                            # 1시간 이상 오래된 인덱스 삭제
                            if current_time - index_time > 3600:
                                print(f"🧨 오래된 인덱스 삭제: {idx.name}")
                                self.pc.delete_index(idx.name)
                        except ValueError:
                            continue
        except Exception as e:
            print(f"⚠️ 인덱스 정리 실패: {e}")
    
    def add_documents(self, texts, metadatas=None, session_id=None):
        """문서 추가 (새 인덱스 생성 후)"""
        # 새 인덱스 생성
        if not self.create_new_index(session_id):
            raise Exception("Pinecone 인덱스 생성 실패")
        
        print(f"{len(texts)}개 문서를 벡터 스토어에 추가 중...")
        
        # 메모리 효율적 처리를 위해 작은 배치로 처리
        batch_size = 5
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size] if metadatas else [{}] * len(batch_texts)
            
            embeddings = self.embeddings.embed_documents(batch_texts)
            vectors = []
            
            for j, (text, embedding) in enumerate(zip(batch_texts, embeddings)):
                vector_id = str(uuid.uuid4())
                metadata = batch_metadatas[j] if batch_metadatas else {}
                metadata['text'] = text[:1000]  # 텍스트 길이 제한
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # 배치 업로드
            self.index.upsert(vectors)
            
            # 메모리 정리
            del vectors
            del embeddings
            gc.collect()
            
            print(f"배치 {i//batch_size + 1} 완료")
        
        print("벡터 스토어 추가 완료")
    
    def similarity_search(self, query, k=5):
        """유사도 검색"""
        if not self.index:
            print("⚠️ Pinecone 인덱스가 없습니다. 먼저 문서를 업로드해주세요.")
            return []
            
        try:
            query_embedding = self.embeddings.embed_query(query)
            results = self.index.query(
                vector=query_embedding,
                top_k=min(k, 5),  # 최대 5개로 제한
                include_metadata=True
            )
            
            docs = [match['metadata']['text'] for match in results['matches']]
            
            # 메모리 정리
            del query_embedding
            del results
            gc.collect()
            
            return docs
        except Exception as e:
            print(f"검색 오류: {e}")
            return []
