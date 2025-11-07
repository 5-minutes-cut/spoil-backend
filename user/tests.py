from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/user/register/'
        self.login_url = '/api/user/login/'
        self.refresh_url = '/api/user/token/refresh/'
        self.logout_url = '/api/user/logout/'

        self.user_data = {
            'username': 'tester',
            'email': 'tester@example.com',
            'nickname': 'tester',
            'password': 'strong-password-123'
        }

    def test_register_login_logout_flow(self):
        # Register
        resp = self.client.post(self.register_url, data=self.user_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('username', resp.data)

        # Login
        login_data = {'username': self.user_data['username'], 'password': self.user_data['password']}
        resp = self.client.post(self.login_url, data=login_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

        access = resp.data['access']
        refresh = resp.data['refresh']

        # Refresh token should work
        resp = self.client.post(self.refresh_url, data={'refresh': refresh}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

        # Logout (blacklist refresh token) - must be authenticated with access token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.post(self.logout_url, data={'refresh': refresh}, format='json')
        self.assertIn(resp.status_code, (status.HTTP_205_RESET_CONTENT, status.HTTP_200_OK))

        # Using the same refresh token again should fail (blacklisted)
        resp = self.client.post(self.refresh_url, data={'refresh': refresh}, format='json')
        # Expect non-200 (usually 401) when refresh token is blacklisted
        self.assertNotEqual(resp.status_code, status.HTTP_200_OK)

    def test_login_with_wrong_credentials(self):
        resp = self.client.post(self.login_url, data={'username': 'nope', 'password': 'bad'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


from unittest import skipUnless
import os
from unittest.mock import patch
from django.urls import reverse
from .models import User


@skipUnless(os.getenv('RUN_KAKAO_INTEGRATION_TEST') == '1', 'Run integration tests that hit Kakao only when RUN_KAKAO_INTEGRATION_TEST=1')
class KakaoIntegrationTest(TestCase):
    """Integration test that performs a real Kakao OAuth callback flow.

    This test calls the local `/api/user/kakao/callback/` view which in turn
    exchanges the authorization code with Kakao and fetches the user profile.

    Requirements to run locally:
    - Set environment variable RUN_KAKAO_INTEGRATION_TEST=1
    - Set environment variable KAKAO_TEST_CODE to a valid authorization code
      obtained by visiting the Kakao OAuth authorize URL in a browser:
        https://kauth.kakao.com/oauth/authorize?client_id=<YOUR_CLIENT_ID>&redirect_uri=<YOUR_REDIRECT_URI>&response_type=code
    - Ensure `KAKAO_REST_API_KEY`, `KAKAO_CLIENT_SECRET`, and `KAKAO_REDIRECT_URI`
      are set in your running environment so `config.settings` picks them up.

    Note: This test makes network calls to Kakao. It is skipped by default.
    """

    def setUp(self):
        self.client = APIClient()

    def test_kakao_callback_integration(self):
        code = os.getenv('KAKAO_TEST_CODE')
        self.assertTrue(code, 'Set KAKAO_TEST_CODE environment variable with a valid Kakao OAuth code')

        # Call the local callback endpoint which will perform token exchange and userinfo fetch
        callback_url = reverse('kakao-callback') + f'?code={code}'
        resp = self.client.get(callback_url)

        # Expect 200 and tokens in response
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        self.assertIn('user', resp.data)

        # Clean up: if a user was created with kakao_id, remove it to avoid polluting local DB
        try:
            kakao_id = resp.data.get('user', {}).get('kakao_id')
            if kakao_id:
                User.objects.filter(kakao_id=str(kakao_id)).delete()
        except Exception:
            pass