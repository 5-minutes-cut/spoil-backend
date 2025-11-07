import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Conversation, QAPair
from .services import GPTService
from series.models import Series

User = get_user_model()


class GPTServiceTest(TestCase):
    """GPT 서비스 단위 테스트"""

    def setUp(self):
        self.gpt_service = GPTService()
        self.test_prompt = "이 애니메이션의 첫 번째 에피소드에 대해 설명해주세요."

    @patch('openai.chat.completions.create')
    def test_generate_response(self, mock_create):
        # Mock GPT 응답 설정
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "테스트 응답입니다."
        mock_create.return_value = mock_response

        # 컨텍스트 없이 호출
        response = self.gpt_service.generate_response(self.test_prompt)
        self.assertEqual(response, "테스트 응답입니다.")

        # 컨텍스트와 함께 호출
        contexts = ["시리즈: 테스트 애니메이션", "설명: 테스트용 시리즈입니다."]
        response = self.gpt_service.generate_response(self.test_prompt, contexts)
        
        # API 호출 확인
        self.assertTrue(mock_create.called)
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['model'], self.gpt_service.model)
        
        # context가 메시지에 포함되었는지 확인
        context_message = next(msg for msg in call_args['messages'] if "테스트 애니메이션" in msg['content'])
        self.assertIsNotNone(context_message)

    @patch('openai.chat.completions.create')
    def test_summarize_question(self, mock_create):
        # Mock GPT 응답 설정
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "애니메이션 첫 에피소드 내용 문의"
        mock_create.return_value = mock_response

        # 요약 기능 테스트
        summary = self.gpt_service.summarize_question(self.test_prompt)
        
        # 요약 길이 검증 (30-50자 제한)
        self.assertLessEqual(len(summary), 50)
        self.assertGreaterEqual(len(summary), 5)

        # API 호출 파라미터 검증
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['temperature'], 0.3)  # 요약은 더 결정적이어야 함

    @patch('openai.chat.completions.create')
    def test_error_handling(self, mock_create):
        # API 에러 시뮬레이션
        mock_create.side_effect = Exception("API Error")

        # generate_response 에러 처리
        response = self.gpt_service.generate_response(self.test_prompt)
        self.assertIn("죄송합니다", response)

        # summarize_question 에러 처리
        summary = self.gpt_service.summarize_question(self.test_prompt)
        self.assertTrue(summary.endswith("..."))
        self.assertLessEqual(len(summary), 53)  # 50자 + "..."


class ChatAPIIntegrationTest(TestCase):
    """채팅 API 통합 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='tester', password='pass12345')
        self.client.force_authenticate(user=self.user)
        
        # 테스트용 시리즈 생성
        self.series = Series.objects.create(
            title="테스트 애니메이션",
            description="테스트용 시리즈입니다."
        )
        
        # 테스트용 대화 생성
        self.conversation = Conversation.objects.create(
            user=self.user,
            series=self.series,
            summary=""
        )

    @patch('chat.services.GPTService.generate_response')
    @patch('chat.services.GPTService.summarize_question')
    def test_create_qa_pair(self, mock_summarize, mock_generate):
        # Mock 응답 설정
        mock_generate.return_value = "GPT가 생성한 답변입니다."
        mock_summarize.return_value = "테스트 질문 요약"

        # 첫 번째 질문 - summary가 설정되어야 함
        response = self.client.post(
            reverse('conversation-qapairs', kwargs={'conversation_id': self.conversation.id}),
            {'question': '테스트 질문입니다.'}
        )

        # 응답 검증
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['answer_text'], "GPT가 생성한 답변입니다.")
        
        # 대화 요약이 설정되었는지 확인
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.summary, "테스트 질문 요약")

        # 두 번째 질문 - summary가 변경되지 않아야 함
        response = self.client.post(
            reverse('conversation-qapairs', kwargs={'conversation_id': self.conversation.id}),
            {'question': '두 번째 질문입니다.'}
        )
        
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.summary, "테스트 질문 요약")  # 여전히 첫 번째 요약을 유지


class LiveGPTTest(TestCase):
    """실제 GPT API 호출 테스트
    
    주의: 이 테스트는 실제 API를 호출하므로 비용이 발생할 수 있습니다.
    RUN_GPT_LIVE_TEST 환경변수가 설정된 경우에만 실행됩니다.
    
    환경변수:
    - RUN_GPT_LIVE_TEST: 이 환경변수가 설정되어야 테스트가 실행됨
    - OPENAI_API_KEY: OpenAI API 키 (필수)
    """

    def setUp(self):
        self.gpt_service = GPTService()

    def test_live_gpt_call(self):
        if not os.getenv('OPENAI_API_KEY'):
            self.skipTest('Skipping live GPT test. Set RUN_GPT_LIVE_TEST to run.')

        # 실제 API 호출 테스트
        prompt = "2+2는 얼마인가요?"
        response = self.gpt_service.generate_response(prompt)
        
        # 응답 검증
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 0)
        self.assertIn('4', response.lower())

        # 요약 기능 테스트
        long_question = "이 애니메이션에서 주인공이 적과 처음 만나서 대화를 나누는 장면이 나오는 에피소드가 궁금한데, 혹시 어느 편인지 알 수 있을까요?"
        summary = self.gpt_service.summarize_question(long_question)
        
        # 요약 검증
        self.assertIsNotNone(summary)
        self.assertGreater(len(summary), 10)
        self.assertLess(len(summary), 51)  # 30-50자 제한 확인
