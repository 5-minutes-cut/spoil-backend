from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    사용자 정보 시리얼라이저
    """
    id = serializers.IntegerField(read_only=True, help_text="사용자 ID")
    username = serializers.CharField(help_text="사용자 아이디")
    email = serializers.EmailField(help_text="이메일 주소")
    nickname = serializers.CharField(help_text="닉네임")
    profile_image = serializers.ImageField(help_text="프로필 이미지", required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'nickname', 'profile_image')


class RegisterSerializer(serializers.ModelSerializer):
    """
    회원가입 시리얼라이저
    """
    username = serializers.CharField(help_text="사용자 아이디")
    email = serializers.EmailField(help_text="이메일 주소")
    nickname = serializers.CharField(help_text="닉네임")
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="비밀번호 (최소 8자 이상)"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'nickname', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class KakaoUserSerializer(serializers.Serializer):
    """
    카카오 로그인 시리얼라이저
    """
    code = serializers.CharField(
        write_only=True,
        help_text="카카오 인증 코드"
    )
    error = serializers.CharField(
        read_only=True,
        help_text="에러 메시지"
    )
    access = serializers.CharField(
        read_only=True,
        help_text="JWT 액세스 토큰"
    )
    refresh = serializers.CharField(
        read_only=True,
        help_text="JWT 리프레시 토큰"
    )
