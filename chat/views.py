from django.conf import settings
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Conversation, QAPair
from .serializers import (
    ConversationSerializer,
    QAPairSerializer,
    CreateQuestionSerializer,
)
from series.models import Series
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()


class ConversationListCreateView(APIView):
    """
    Conversation 목록 조회 및 새 Conversation 생성

    GET: 모든 Conversation 목록 반환
    POST: 새 Conversation 생성 (summary, series)
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    

    @swagger_auto_schema(
        operation_summary="Conversation 목록 조회",
        operation_description="모든 Conversation(대화 세션)을 생성일 역순으로 반환합니다.",
        responses={200: ConversationSerializer(many=True)}
    )
    def get(self, request):
        conversations = Conversation.objects.all().order_by('-created_at')
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="새 대화 생성",
        operation_description="새로운 Conversation(대화 세션)을 생성합니다. `summary`와 `series`(옵션) 필드를 지원합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'summary': openapi.Schema(type=openapi.TYPE_STRING, description='대화 요약', max_length=1024),
                'series': openapi.Schema(type=openapi.TYPE_INTEGER, description='관련 시리즈 ID (선택)')
            }
        ),
        responses={201: ConversationSerializer(), 400: '잘못된 요청'}
    )
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

    

    @swagger_auto_schema(
        operation_summary="Conversation의 QAPair 목록 조회",
        operation_description="주어진 Conversation ID에 연결된 모든 QAPair를 생성일 순으로 반환합니다.",
        manual_parameters=[
            openapi.Parameter('conversation_id', openapi.IN_PATH, description='대화 ID', type=openapi.TYPE_INTEGER)
        ],
        responses={200: QAPairSerializer(many=True), 404: 'Conversation 없음'}
    )
    def get(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id)
        qas = conv.qapairs.all()
        serializer = QAPairSerializer(qas, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="질문 등록 및 자동 응답 생성",
        operation_description="Conversation에 질문을 등록하면 QAPair가 생성되고 간단한 자동응답이 채워져 반환됩니다.",
        manual_parameters=[
            openapi.Parameter('conversation_id', openapi.IN_PATH, description='대화 ID', type=openapi.TYPE_INTEGER)
        ],
        request_body=CreateQuestionSerializer,
        responses={201: QAPairSerializer(), 400: '잘못된 요청', 404: 'Conversation 없음'}
    )
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

from .channelio import (
    report_bug_with_member_id,
    ChannelIoUserNotFound,
    ChannelIoError,
)

class ChannelBugReportView(APIView):
    @csrf_exempt  # 실제 서비스면 CSRF 토큰 처리 추천
    @require_POST
    def channel_bug_report(request):
        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "invalid_json"}, status=400)

        member_id = str(body.get("memberId") or "").strip()
        query = body.get("query") or ""
        answer_text = body.get("answerText") or ""
        answer_id = body.get("answerId")
        extra_info = body.get("extraInfo")

        if not member_id or not query or not answer_text:
            return JsonResponse(
                {"error": "memberId, query, answerText 는 필수입니다."},
                status=400,
            )

        try:
            result = report_bug_with_member_id(
                member_id=member_id,
                query=query,
                answer_text=answer_text,
                answer_id=answer_id,
                extra_info=extra_info,
            )
        except ChannelIoUserNotFound:
            # 프론트에서 아직 ChannelIO('boot') 를 안 했을 가능성
            return JsonResponse(
                {"error": "channel_user_not_found", "detail": "Channel member 가 없습니다."},
                status=404,
            )
        except ChannelIoError as e:
            return JsonResponse(
                {"error": "channel_io_error", "detail": str(e)},
                status=502,
            )

        return JsonResponse({"ok": True, "channel": result}, status=201)