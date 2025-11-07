from rest_framework import serializers
from .models import Conversation, QAPair
from django.contrib.auth import get_user_model

User = get_user_model()


class QAPairSerializer(serializers.ModelSerializer):
    """질문-답변 쌍 시리얼라이저"""

    class Meta:
        model = QAPair
        fields = ('id', 'conversation', 'question_text', 'answer_text', 'created_at')
        read_only_fields = ('id', 'created_at')


class ConversationSerializer(serializers.ModelSerializer):
    """대화(Conversation)와 포함된 QAPair들을 반환하는 시리얼라이저"""
    qapairs = QAPairSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Conversation
        fields = ('id', 'user', 'series', 'summary', 'created_at', 'qapairs')
        read_only_fields = ('id', 'created_at', 'qapairs')


class CreateQuestionSerializer(serializers.Serializer):
    """질문 생성 요청 본문 검증용 시리얼라이저"""
    question = serializers.CharField(help_text='질문 내용', max_length=2000)
