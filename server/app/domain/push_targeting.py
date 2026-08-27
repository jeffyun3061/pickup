"""
푸시 타겟팅 규칙 (순수 도메인).

ADR-003 알림 3종과 동일 키를 서버에서도 강제한다.
"""

from __future__ import annotations

from dataclasses import dataclass


# 팝업·굿즈는 뉴스 피드의 별도 탐색 영역이다. 사용자가 고른 게임의
# 새 소식 알림에는 게임 업데이트와 인게임 이벤트만 포함해 알림 피로를 줄인다.
_GAME_NEWS_KINDS = frozenset({"update", "event"})


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
    """선택 게임의 업데이트·인게임 이벤트 게시 알림 여부를 판정한다.

    ``event_ending``은 스케줄러가 종료 임박 시점에 보내는 별도 알림이므로,
    이벤트 게시 순간에는 이 토글을 재사용하지 않는다. 팝업·굿즈는
    탐색 피드에만 표시하고 게시 푸시를 보내지 않는다.
    """
    return (
        prefs.selected_game_news
        and game_id in prefs.game_ids
        and kind in _GAME_NEWS_KINDS
    )


def should_notify_service_announcement(prefs: NotificationPrefs) -> bool:
    return prefs.service_notices


def should_notify_event_ending(prefs: NotificationPrefs, *, game_id: str) -> bool:
    """마이픽 게임의 이벤트 마감 임박 리마인더."""
    return prefs.event_ending and game_id in prefs.game_ids
