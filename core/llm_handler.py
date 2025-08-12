import requests
import json
from config.settings import Config

class GroqLLM:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
    def generate(self, prompt, max_tokens=512):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "model": "llama-3.1-8b-instant",  # Qwen2.5:7b와 비슷한 성능
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "top_p": 1,
                "stream": False
            }
            
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Groq API 오류: {response.status_code} - {response.text}"
                
        except requests.exceptions.Timeout:
            return "요청 시간 초과. 다시 시도해주세요."
        except Exception as e:
            return f"LLM 오류: {str(e)}"
    
    def test_connection(self):
        """연결 테스트"""
        try:
            test_response = self.generate("안녕하세요", max_tokens=50)
            return "연결 성공!" if "오류" not in test_response else test_response
        except Exception as e:
            return f"연결 실패: {str(e)}"