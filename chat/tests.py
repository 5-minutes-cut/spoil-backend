from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='tester', password='pass12345')

    def test_create_session_and_post_message(self):
        # 로그인
        self.client.force_authenticate(self.user)
        # Conversation 생성
        resp = self.client.post(reverse('conversations'), {'summary': 'test conversation'})
        self.assertEqual(resp.status_code, 201)
        conv_id = resp.data['id']

        # 질문 등록 (QAPair 생성 및 자동 답변 채워짐)
        q_url = reverse('conversation-qapairs', kwargs={'conversation_id': conv_id})
        resp2 = self.client.post(q_url, {'question': '이 시리즈에 대해 질문이 있습니다.'})
        self.assertEqual(resp2.status_code, 201)
        self.assertIn('question_text', resp2.data)
        self.assertIn('answer_text', resp2.data)
