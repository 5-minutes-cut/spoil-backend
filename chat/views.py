from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Conversation, QAPair
from .serializers import (
    ConversationSerializer,
    QAPairSerializer,
    CreateQuestionSerializer,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class ConversationListCreateView(APIView):
    """
    Conversation 목록 조회 및 새 Conversation 생성

    GET: 모든 Conversation 목록 반환
    POST: 새 Conversation 생성 (summary, series)
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        conversations = Conversation.objects.all().order_by('-created_at')
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        summary = data.get('summary', '')
        series = data.get('series', None)

        conv = Conversation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            series_id=series,
            summary=summary,
        )

        serializer = ConversationSerializer(conv)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QAPairListCreateView(APIView):
    """
    Conversation에 연결된 QAPair 목록 조회 및 질문 등록

    POST: 질문을 등록하면 QAPair 레코드를 생성하고 answer_text를 채워 반환합니다.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id)
        qas = conv.qapairs.all()
        serializer = QAPairSerializer(qas, many=True)
        return Response(serializer.data)

    def post(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id)
        serializer = CreateQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data['question']
        summary = serializer.validated_data.get('summary')

        # conversation summary 업데이트(선택적)
        if summary:
            conv.summary = summary
            conv.save()

        # QAPair 생성 (초기에는 answer_text 비워두고 생성)
        qa = QAPair.objects.create(conversation=conv, question_text=question)

        # TODO: 실제 답변 생성(LLM/검색 연동 등)
        answer = f"[자동응답] 질문을 받았습니다: {question[:200]}"
        qa.answer_text = answer
        qa.save()

        return Response(QAPairSerializer(qa).data, status=status.HTTP_201_CREATED)
