from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView,
    KakaoLoginView, KakaoCallbackView, SocialAccountView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='user-register'),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='user-logout'),
    
    # 카카오 로그인
    path('kakao/login/', KakaoLoginView.as_view(), name='kakao-login'),
    path('kakao/callback/', KakaoCallbackView.as_view(), name='kakao-callback'),
    path('social/account/', SocialAccountView.as_view(), name='social-account'),
]
