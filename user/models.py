from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    사용자 모델
    """
    nickname = models.CharField(max_length=50, unique=True, help_text="사용자의 닉네임")
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True, help_text="프로필 이미지")
    
    # 소셜 로그인 필드
    kakao_id = models.CharField(max_length=100, null=True, blank=True, unique=True, help_text="카카오 소셜 ID")
    is_kakao_user = models.BooleanField(default=False, help_text="카카오 로그인 사용자 여부")

    class Meta:
        db_table = 'user'
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'

class WatchingStatus(models.Model):
    """
    사용자의 애니메이션 시청 현황
    """
    STATUS_CHOICES = [
        ('watching', '시청중'),
        ('completed', '시청완료'),
        ('plan_to_watch', '시청예정'),
        ('dropped', '시청중단')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watching_status', help_text="사용자")
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE, related_name='watchers', help_text="애니메이션")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, help_text="시청 상태")
    current_episode = models.IntegerField(default=0, help_text="현재 시청 중인 에피소드")
    last_watched = models.DateTimeField(auto_now=True, help_text="마지막 시청일")
    rating = models.IntegerField(null=True, blank=True, help_text="평점 (1-10)")
    
    class Meta:
        db_table = 'watching_status'
        verbose_name = '시청 현황'
        verbose_name_plural = '시청 현황들'
        unique_together = ('user', 'anime')  # 한 사용자가 같은 애니메이션에 대해 중복 상태를 가질 수 없음
