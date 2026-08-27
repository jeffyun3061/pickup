"""Expo Push API 클라이언트 — outbox 디스패처에서 사용."""

from __future__ import annotations

import logging

import httpx

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
_TIMEOUT = httpx.Timeout(10.0)

logger = logging.getLogger(__name__)


def is_expo_token(token: str) -> bool:
    return token.startswith("ExponentPushToken[") or token.startswith("ExpoPushToken[")


def send_messages(messages: list[dict]) -> list[str | None]:
    """
    메시지 목록을 발송하고 메시지별 오류(None=성공)를 순서대로 돌려준다.
    네트워크 실패 등 전체 실패 시 예외를 그대로 올린다.
    """
    if not messages:
        return []
    with httpx.Client(timeout=_TIMEOUT) as client:
        res = client.post(EXPO_PUSH_URL, json=messages)
        res.raise_for_status()
        body = res.json()
    tickets = body.get("data", [])
    errors: list[str | None] = []
    for i, _message in enumerate(messages):
        ticket = tickets[i] if i < len(tickets) else None
        if not isinstance(ticket, dict):
            errors.append("no ticket returned")
        elif ticket.get("status") == "ok":
            errors.append(None)
        else:
            detail = ticket.get("message") or str(ticket.get("details") or "unknown error")
            errors.append(detail)
    return errors
