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
from django.test import TestCase

# Create your tests here.
