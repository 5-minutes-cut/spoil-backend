from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversation(models.Model):
    """
    Conversation represents a chat session for a series (ERD's Conversation table).

    Fields:
    - user: FK to user who started the conversation (nullable for anonymous)
    - series (anime): FK to the related series
    - summary: short text summary (optional)
    - created_at: timestamp
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text='대화를 시작한 사용자 (익명 가능)'
    )
    series = models.ForeignKey(
        'anime.Anime',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text='관련된 시리즈(애니메이션)'
    )
    summary = models.CharField(max_length=1024, blank=True, help_text='대화 요약(선택)')
    created_at = models.DateTimeField(default=timezone.now, help_text='생성 시각')

    class Meta:
        db_table = 'conversation'
        verbose_name = '대화 세션'
        verbose_name_plural = '대화 세션들'

    def __str__(self):
        return f"Conversation:{self.id} - {self.summary[:40] or 'untitled'}"


class QAPair(models.Model):
    """
    질문-답변 쌍 (ERD의 QApair / QA pair table).

    Fields:
    - conversation: FK to Conversation
    - question_text
    - answer_text
    - created_at
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='qapairs',
        help_text='연결된 대화(Conversation)'
    )
    question_text = models.TextField(help_text='질문 내용')
    answer_text = models.TextField(blank=True, null=True, help_text='답변 내용')
    created_at = models.DateTimeField(default=timezone.now, help_text='생성 시각')

    class Meta:
        db_table = 'qapair'
        verbose_name = '질문-답변 쌍'
        verbose_name_plural = '질문-답변 쌍들'
        ordering = ('created_at',)

    def __str__(self):
        return f"Q{self.id}: {self.question_text[:40]}"
