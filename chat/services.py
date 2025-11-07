from typing import List
import openai
from django.conf import settings

class GPTService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4.1"  
        
    def summarize_question(self, question: str) -> str:
        """
        질문을 간단하게 요약합니다.
        
        Args:
            question (str): 요약할 질문
            
        Returns:
            str: 요약된 내용 (최대 200자)
        """
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "주어진 질문을 30자에서 50자 사이로 간단히 요약해주세요. 핵심 키워드를 포함하되, 너무 자세하지 않게 요약합니다."
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                temperature=0.3,  # 더 일관된 요약을 위해 temperature를 낮게 설정
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error in summarizing question: {str(e)}")
            # 에러 발생 시 질문의 앞부분을 잘라서 반환
            return question[:50] + "..."

    def generate_response(self, prompt: str, additional_context: List[str] = None) -> str:
        """
        GPT API를 호출하여 응답을 생성합니다.
        
        Args:
            prompt (str): 사용자가 입력한 프롬프트
            additional_context (List[str]): DB에서 가져온 추가 컨텍스트 목록
            
        Returns:
            str: GPT가 생성한 응답
        """
        messages = []
        
        # 시스템 메시지 추가
        messages.append({
            "role": "system",
            "content": "You are a helpful assistant that provides information about anime and movies."
        })
        
        # 추가 컨텍스트가 있다면 추가
        if additional_context:
            context_message = "\n".join(additional_context)
            messages.append({
                "role": "system",
                "content": f"Here is some additional context about the anime/movie:\n{context_message}"
            })
        
        # 사용자 프롬프트 추가
        messages.append({
            "role": "user",
            "content": prompt
        })

        try:
            # GPT API 호출
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            # 응답 텍스트 반환
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # 에러 발생 시 로깅하고 기본 메시지 반환
            print(f"Error in GPT API call: {str(e)}")
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."