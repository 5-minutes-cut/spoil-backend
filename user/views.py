import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer, KakaoUserSerializer

User = get_user_model()


class RegisterView(APIView):
    """
    회원가입 API

    ---
    ### 요청 본문
    - username: 사용자 아이디
    - email: 이메일 주소
    - nickname: 닉네임
    - password: 비밀번호 (최소 8자)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        새로운 사용자를 생성합니다.
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    """
    로그인 API

    ---
    ### 요청 본문
    - username: 사용자 아이디
    - password: 비밀번호
    
    ### 응답
    - access: JWT 액세스 토큰
    - refresh: JWT 리프레시 토큰
    """
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """
    로그아웃 API

    ---
    ### 요청 본문
    - refresh: 현재 사용 중인 JWT 리프레시 토큰
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        제공된 리프레시 토큰을 블랙리스트에 추가하여 로그아웃합니다.
        """
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'detail': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class KakaoLoginView(APIView):
    """
    카카오 로그인 시작 API

    ---
    카카오 로그인 페이지로 리다이렉트합니다.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        카카오 OAuth 인증 페이지로 리다이렉트합니다.
        """
        client_id = settings.KAKAO_REST_API_KEY
        redirect_uri = settings.KAKAO_REDIRECT_URI
        kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
        return redirect(kakao_auth_url)


class SocialAccountView(APIView):
    """
    소셜 계정 관리 API

    ---
    ### 응답 (GET)
    - is_kakao_user: 카카오 계정으로 가입한 사용자 여부
    - kakao_connected: 카카오 계정 연동 여부

    ### 응답 (DELETE)
    - message: 성공/실패 메시지
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        현재 사용자의 소셜 계정 연동 상태를 조회합니다.
        """
        return Response({
            'is_kakao_user': request.user.is_kakao_user,
            'kakao_connected': bool(request.user.kakao_id),
        })

    def delete(self, request):
        """소셜 계정 연동 해제"""
        user = request.user
        if not user.kakao_id:
            return Response({'error': '연동된 카카오 계정이 없습니다.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # 순수 카카오 로그인 사용자는 연동 해제 불가
        if user.is_kakao_user and not user.has_usable_password():
            return Response(
                {'error': '카카오로만 로그인하는 계정은 연동을 해제할 수 없습니다. 먼저 비밀번호를 설정해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 카카오 연동 해제
        user.kakao_id = None
        user.is_kakao_user = False
        user.save()
        
        return Response({'message': '카카오 계정 연동이 해제되었습니다.'})


class KakaoCallbackView(APIView):
    """
    카카오 로그인 콜백 API

    ---
    ### Query Parameters
    - code: 카카오 인증 코드

    ### 응답
    - user: 사용자 정보
        - id: 사용자 ID
        - username: 사용자 아이디
        - email: 이메일
        - nickname: 닉네임
        - profile_image: 프로필 이미지 URL
    - access: JWT 액세스 토큰
    - refresh: JWT 리프레시 토큰
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        카카오 OAuth 인증 완료 후 콜백을 처리하고 JWT 토큰을 발급합니다.
        """
        code = request.GET.get('code')
        if not code:
            return Response({'error': 'Authorization code not provided'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # 액세스 토큰 받기
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            'grant_type': 'authorization_code',
            'client_id': settings.KAKAO_REST_API_KEY,
            'client_secret': settings.KAKAO_CLIENT_SECRET,
            'redirect_uri': settings.KAKAO_REDIRECT_URI,
            'code': code,
        }
        
        token_response = requests.post(token_url, data=data)
        if not token_response.ok:
            return Response({'error': 'Failed to get access token'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        access_token = token_response.json().get('access_token')

        # 카카오 사용자 정보 받기
        user_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        
        user_response = requests.get(user_url, headers=headers)
        if not user_response.ok:
            return Response({'error': 'Failed to get user info'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        user_data = user_response.json()
        kakao_id = str(user_data.get('id'))
        kakao_account = user_data.get('kakao_account', {})
        
        # 프로필 및 계정 정보 가져오기
        nickname = kakao_account.get('profile', {}).get('nickname', f'kakao_{kakao_id}')
        email = kakao_account.get('email', f'{kakao_id}@kakao.user')
        profile_image = kakao_account.get('profile', {}).get('profile_image_url')

        # 프로필 이미지 다운로드 함수
        def download_profile_image(url):
            if not url:
                return None
            try:
                response = requests.get(url)
                if response.ok:
                    from django.core.files.base import ContentFile
                    from io import BytesIO
                    img_temp = BytesIO(response.content)
                    return ContentFile(img_temp.getvalue(), name=f'kakao_profile_{kakao_id}.jpg')
            except Exception as e:
                print(f"프로필 이미지 다운로드 실패: {e}")
            return None

        # 이메일로 기존 사용자 확인
        existing_email_user = None
        if email and email != f'{kakao_id}@kakao.user':
            try:
                existing_email_user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass

        # 카카오 ID로 사용자 확인
        try:
            user = User.objects.get(kakao_id=kakao_id)
            # 프로필 정보 업데이트
            user.nickname = nickname
            if profile_image:
                img_file = download_profile_image(profile_image)
                if img_file:
                    user.profile_image = img_file
            user.save()
        except User.DoesNotExist:
            # 이메일 중복 사용자가 있는 경우
            if existing_email_user:
                # 기존 계정에 카카오 연동
                existing_email_user.kakao_id = kakao_id
                existing_email_user.is_kakao_user = True
                if profile_image:
                    img_file = download_profile_image(profile_image)
                    if img_file:
                        existing_email_user.profile_image = img_file
                existing_email_user.save()
                user = existing_email_user
            else:
                # 새 사용자 생성
                username = f'kakao_{kakao_id}'
                user = User.objects.create(
                    username=username,
                    email=email,
                    nickname=nickname,
                    kakao_id=kakao_id,
                    is_kakao_user=True
                )
                # 프로필 이미지 설정
                if profile_image:
                    img_file = download_profile_image(profile_image)
                    if img_file:
                        user.profile_image = img_file
                # 랜덤 비밀번호 설정
                user.set_unusable_password()
                user.save()

        # JWT 토큰 생성
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })