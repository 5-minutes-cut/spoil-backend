# app/utils/channelio.py

from __future__ import annotations
import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = getattr(settings, "CHANNEL_OPEN_BASE_URL", "https://api.channel.io/open/v5")


class ChannelIoError(Exception):
    """기본 채널톡 에러"""


class ChannelIoUserNotFound(ChannelIoError):
    """memberId로 유저를 찾지 못했을 때"""


def _auth_headers() -> dict:
    if not settings.CHANNEL_OPEN_ACCESS_KEY or not settings.CHANNEL_IO_ACCESS_SECRET:
        raise ChannelIoError("CHANNEL_IO_ACCESS_KEY / SECRET 이 설정되지 않았습니다.")

    return {
        "x-access-key": settings.CHANNEL_OPEN_ACCESS_KEY,
        "x-access-secret": settings.CHANNEL_OPEN_ACCESS_SECRET,
        "accept": "application/json",
        "Content-Type": "application/json",
    }


# 1) memberId -> channel userId 조회
def get_channel_user_id(member_id: str) -> str:
    """
    GET /open/v5/users/{memberId}
    응답의 user.id 가 channel userId
    """
    url = f"{BASE_URL}/users/{member_id}"
    headers = _auth_headers()

    resp = requests.get(url, headers=headers, timeout=5)

    # memberId 를 못 찾으면 422 notFoundError
    if resp.status_code == 422:
        raise ChannelIoUserNotFound(f"Channel user not found for memberId={member_id}")

    try:
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.exception("Failed to get channel user: %s", e)
        raise ChannelIoError(str(e))

    data = resp.json()
    # 실제 필드명: {"user": {"id": "...", "memberId": "...", ...}}
    user = data.get("user") or data
    user_id = user.get("id")
    if not user_id:
        raise ChannelIoError(f"user.id 가 응답에 없습니다: {data}")

    return user_id


# 2) userId 기준으로 userChatId 가져오기 (없으면 생성)
def get_or_create_user_chat_id(user_id: str) -> str:
    """
    1) GET /open/v5/users/{userId}/user-chats 로 목록 조회
    2) 없으면 POST /open/v5/users/{userId}/user-chats 로 새 채팅 생성
    """
    headers = _auth_headers()

    # 2-1. 기존 user chat 목록 조회
    list_url = f"{BASE_URL}/users/{user_id}/user-chats"
    resp = requests.get(list_url, headers=headers, timeout=5)
    try:
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.exception("Failed to list user chats: %s", e)
        raise ChannelIoError(str(e))

    data = resp.json()
    # 실제 스펙에 맞게 필드명 확인 필요 (userChats / chats / data 등)
    chats = data.get("userChats") or data.get("chats") or data.get("data") or []

    # 이미 열린 채팅이 있으면 그걸 재사용
    if chats:
        # 상태 필드(state)가 있으면 open 인 것만 골라도 됨
        open_chat = next(
            (c for c in chats if c.get("state") != "closed"),
            chats[0],
        )
        return open_chat["id"]

    # 2-2. 없으면 새 user chat 생성
    create_resp = requests.post(list_url, headers=headers, json={}, timeout=5)
    try:
        create_resp.raise_for_status()
    except requests.RequestException as e:
        logger.exception("Failed to create user chat: %s", e)
        raise ChannelIoError(str(e))

    created = create_resp.json()
    # 응답 구조 예: {"userChat": {"id": "...", ...}}
    user_chat = created.get("userChat") or created
    user_chat_id = user_chat.get("id")
    if not user_chat_id:
        raise ChannelIoError(f"userChat.id 를 찾을 수 없습니다: {created}")

    return user_chat_id


# 3) userChatId 로 버그 리포트 메시지 전송
def send_bug_report_message(
    user_chat_id: str,
    query: str,
    answer_text: str,
    answer_id: Optional[str] = None,
    extra_info: Optional[dict] = None,
):
    """
    POST /open/v5/user-chats/{userChatId}/messages
    blocks 로 텍스트 메시지 전송
    """
    headers = _auth_headers()
    url = f"{BASE_URL}/user-chats/{user_chat_id}/messages"

    lines = [
        "[BUG REPORT] 애니스포방지 검색 응답 오류 신고",
        "",
        "질문:",
        query,
        "",
        "응답:",
        answer_text,
    ]

    if answer_id:
        lines.extend(["", f"(answerId: {answer_id})"])

    if extra_info:
        lines.extend(["", f"extra: {extra_info}"])

    payload = {
        "blocks": [
            {
                "type": "text",
                "value": "\n".join(lines),
            }
        ]
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=5)
    try:
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.exception("Failed to send bug report message: %s", e)
        raise ChannelIoError(str(e))

    return resp.json()


# 4) memberId 하나만 받아서 전체 플로우 실행하는 헬퍼
def report_bug_with_member_id(
    member_id: str,
    query: str,
    answer_text: str,
    answer_id: Optional[str] = None,
    extra_info: Optional[dict] = None,
):
    """
    memberId 기준 전체 플로우:
    - memberId -> userId
    - userId -> userChatId (get_or_create)
    - userChatId 로 버그 리포트 메시지 전송
    """
    user_id = get_channel_user_id(member_id)
    user_chat_id = get_or_create_user_chat_id(user_id)
    return send_bug_report_message(
        user_chat_id=user_chat_id,
        query=query,
        answer_text=answer_text,
        answer_id=answer_id,
        extra_info=extra_info,
    )
