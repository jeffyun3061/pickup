"""
푸시 타겟팅 규칙 (순수 도메인).

ADR-003 알림 3종과 동일 키를 서버에서도 강제한다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NotificationPrefs:
    game_ids: tuple[str, ...]
    selected_game_news: bool
    event_ending: bool
    service_notices: bool


def should_notify_content_publish(
    prefs: NotificationPrefs,
    *,
    game_id: str,
    kind: str,
) -> bool:
    """선택된 게임의 새 소식. event 종류는 event_ending 토글도 인정."""
    if game_id not in prefs.game_ids:
        return False
    if prefs.selected_game_news:
        return True
    if kind == "event" and prefs.event_ending:
        return True
    return False


def should_notify_service_announcement(prefs: NotificationPrefs) -> bool:
    return prefs.service_notices
