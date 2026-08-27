from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.ids import new_id
from app.domain.push_targeting import (
    NotificationPrefs,
    should_notify_content_publish,
    should_notify_event_ending,
    should_notify_service_announcement,
)
from app.domain.quiet_hours import resolve_available_at
from app.models.entities import Announcement, Content, Installation, PushOutbox, PushOutboxStatus
from app.repositories.installation_repository import InstallationRepository
from app.repositories.push_outbox_repository import PushOutboxRepository
from app.schemas.common import PushDispatchOut
from app.services import expo_push

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_MAX_GROUPED_CONTENTS = 20

# Expo는 HTTP 200이어도 메시지별 ticket 오류를 반환할 수 있다. 토큰 오류는
# 해당 토큰만 삭제하고, 페이로드·자격증명 오류는 영구 실패로 보관한다.
_EXPO_TOKEN_ERRORS = (
    "devicenotregistered",
    "deviceisnotregistered",
    "invaliddevicetoken",
)
_EXPO_HARD_TICKET_ERRORS = (
    "messagetoobig",
    "invalidcredentials",
    "mismatchsenderid",
    "invalidprovidertoken",
)

_CHANNEL_TITLE = {
    "content_published": "피키의 게임 소식!",
    "event_ending": "피키의 이벤트 알림",
    "service_notice": "피키 공지",
}


def _short_notification_text(value: object, *, fallback: str) -> str:
    """알림 미리보기에서만 쓸 짧은 텍스트를 만든다."""
    if not isinstance(value, str):
        return fallback
    text = " ".join(value.split()).strip()
    return text[:120] if text else fallback


def _notification_copy(channel: str, payload: dict) -> tuple[str, str]:
    """채널별 공통 브랜드 제목과 사용자에게 보일 한 줄 본문."""
    title = _CHANNEL_TITLE.get(channel, "피키 알림")
    game_name = _short_notification_text(payload.get("game_name"), fallback="내 게임")

    if channel == "content_published":
        count = payload.get("content_count")
        if isinstance(count, int) and count > 1:
            return title, f"{game_name}에 새 소식 {count}건이 올라왔어요"
        content_title = _short_notification_text(payload.get("title"), fallback="새 소식")
        return title, f"{game_name} · {content_title}"

    if channel == "event_ending":
        content_title = _short_notification_text(payload.get("title"), fallback="기간 콘텐츠")
        return title, f"{game_name} · {content_title} 종료가 가까워요"

    notice_title = _short_notification_text(payload.get("title"), fallback="서비스 공지가 도착했어요")
    return title, notice_title


def _is_invalid_expo_token_error(error: str | None) -> bool:
    """Expo의 영구 토큰 오류만 삭제 대상으로 분류한다."""
    normalized = (error or "").replace(" ", "").lower()
    return any(marker in normalized for marker in _EXPO_TOKEN_ERRORS)


def _is_transient_expo_ticket_error(error: str | None) -> bool:
    """HTTP 200 ticket 오류 중 다음 주기에 재시도할 오류를 판별한다."""
    normalized = (error or "").replace(" ", "").lower()
    if not normalized:
        return False
    return not any(
        marker in normalized for marker in (*_EXPO_TOKEN_ERRORS, *_EXPO_HARD_TICKET_ERRORS)
    )


def _prefs_from_installation(item: Installation) -> NotificationPrefs:
    try:
        raw = json.loads(item.game_ids_json or "[]")
        game_ids = tuple(x for x in raw if isinstance(x, str))
    except json.JSONDecodeError:
        game_ids = ()
    return NotificationPrefs(
        game_ids=game_ids,
        selected_game_news=item.notify_selected_game_news,
        event_ending=item.notify_event_ending,
        service_notices=item.notify_service_notices,
    )


class PushService:
    """발행 시 outbox enqueue + 디스패치 (EXPO_PUSH_ENABLED면 실발송, 아니면 스텁)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.installations = InstallationRepository(db)
        self.outbox = PushOutboxRepository(db)

    def _available_at(self) -> datetime:
        settings = get_settings()
        return resolve_available_at(
            datetime.now(timezone.utc),
            start_hour=settings.quiet_hours_start,
            end_hour=settings.quiet_hours_end,
            utc_offset_hours=settings.quiet_hours_utc_offset,
        )

    def _enqueue(self, installation_id: str, channel: str, payload: dict) -> None:
        self.outbox.add(
            PushOutbox(
                id=new_id("po"),
                installation_id=installation_id,
                channel=channel,
                payload_json=json.dumps(payload, ensure_ascii=False),
                status=PushOutboxStatus.pending,
                available_at=self._available_at(),
            )
        )

    def enqueue_content_published(self, content: Content) -> int:
        game_name = content.game.name if content.game is not None else content.game_id
        payload = {
            "channel": "content_published",
            "content_id": content.id,
            "content_ids": [content.id],
            "content_count": 1,
            "game_id": content.game_id,
            "game_name": game_name,
            "kind": content.kind.value,
            "title": content.title,
        }
        count = 0
        for installation in self.installations.list_active_with_tokens():
            if not installation.device_tokens:
                continue
            prefs = _prefs_from_installation(installation)
            if not should_notify_content_publish(
                prefs,
                game_id=content.game_id,
                kind=content.kind.value,
            ):
                continue
            if self._merge_pending_content(installation.id, payload):
                continue
            self._enqueue(installation.id, "content_published", payload)
            count += 1
        return count

    def _merge_pending_content(self, installation_id: str, payload: dict) -> bool:
        """같은 게임의 대기 중 새 소식을 한 건의 알림으로 묶는다.

        발행 요청은 콘텐츠별로 들어오지만, 짧은 시간에 여러 공지가 올라오면
        기기에는 ``게임명 새 소식 N건`` 한 번만 보낸다. 이미 발송된 행은
        건드리지 않아 재시도·감사 이력은 그대로 유지한다.
        """
        game_id = payload.get("game_id")
        content_id = payload.get("content_id")
        if not isinstance(game_id, str) or not isinstance(content_id, str):
            return False

        rows = self.db.scalars(
            select(PushOutbox).where(
                PushOutbox.installation_id == installation_id,
                PushOutbox.channel == "content_published",
                PushOutbox.status == PushOutboxStatus.pending,
            )
        ).all()
        for row in rows:
            try:
                existing = json.loads(row.payload_json)
            except json.JSONDecodeError:
                continue
            if not isinstance(existing, dict) or existing.get("game_id") != game_id:
                continue

            old_ids = existing.get("content_ids")
            if not isinstance(old_ids, list):
                old_id = existing.get("content_id")
                old_ids = [old_id] if isinstance(old_id, str) else []
            ids = [item for item in old_ids if isinstance(item, str)]
            if content_id not in ids:
                ids.append(content_id)

            old_titles = existing.get("content_titles")
            if not isinstance(old_titles, list):
                old_title = existing.get("title")
                old_titles = [old_title] if isinstance(old_title, str) else []
            titles = [item for item in old_titles if isinstance(item, str)]
            incoming_title = payload.get("title")
            if isinstance(incoming_title, str) and incoming_title not in titles:
                titles.append(incoming_title)

            old_count = existing.get("content_count")
            count = max(old_count if isinstance(old_count, int) else 0, len(ids))
            game_name = existing.get("game_name") or payload.get("game_name") or game_id
            single_title = titles[0] if titles else "새 소식"
            existing.update(
                {
                    "content_id": ids[0] if ids else content_id,
                    "content_ids": ids[:_MAX_GROUPED_CONTENTS],
                    "content_titles": titles[:_MAX_GROUPED_CONTENTS],
                    "content_count": count,
                    "game_name": game_name,
                    "title": f"{game_name} 새 소식 {count}건" if count > 1 else single_title,
                }
            )
            row.payload_json = json.dumps(existing, ensure_ascii=False)
            self.outbox.save(row)
            return True
        return False

    def enqueue_event_ending(self, content: Content) -> int:
        """이벤트 마감 임박 리마인더 (주기 러너에서 호출)."""
        game_name = content.game.name if content.game is not None else content.game_id
        payload = {
            "channel": "event_ending",
            "content_id": content.id,
            "game_id": content.game_id,
            "game_name": game_name,
            "kind": content.kind.value,
            "title": content.title,
        }
        count = 0
        for installation in self.installations.list_active_with_tokens():
            if not installation.device_tokens:
                continue
            prefs = _prefs_from_installation(installation)
            if not should_notify_event_ending(prefs, game_id=content.game_id):
                continue
            self._enqueue(installation.id, "event_ending", payload)
            count += 1
        return count

    def enqueue_announcement_published(self, announcement: Announcement) -> int:
        payload = {
            "channel": "service_notice",
            "announcement_id": announcement.id,
            "title": announcement.title,
        }
        count = 0
        for installation in self.installations.list_active_with_tokens():
            if not installation.device_tokens:
                continue
            prefs = _prefs_from_installation(installation)
            if not should_notify_service_announcement(prefs):
                continue
            self._enqueue(installation.id, "service_notice", payload)
            count += 1
        return count

    def dispatch_pending(self, *, limit: int = 100) -> PushDispatchOut:
        settings = get_settings()
        pending = self.outbox.list_pending(limit=limit)
        sent = 0
        failed = 0
        for row in pending:
            row.attempts += 1
            tokens = self.installations.list_tokens(row.installation_id)
            if not tokens:
                row.status = PushOutboxStatus.failed
                row.last_error = "no device token"
                failed += 1
            elif not settings.expo_push_enabled:
                # 스텁: 토큰·페이로드를 로그로만 남기고 sent 처리 (개발 모드)
                logger.info(
                    "push_stub_send installation=%s channel=%s tokens=%s payload=%s",
                    row.installation_id,
                    row.channel,
                    [t.token[:12] for t in tokens],
                    row.payload_json,
                )
                row.status = PushOutboxStatus.sent
                row.last_error = None
                sent += 1
            else:
                if self._send_via_expo(row, [t.token for t in tokens]):
                    sent += 1
                else:
                    failed += 1
            self.outbox.save(row)
        return PushDispatchOut(processed=len(pending), sent=sent, failed=failed)

    def _send_via_expo(self, row: PushOutbox, tokens: list[str]) -> bool:
        """토큰 중 하나라도 성공하면 sent. 전송 예외는 최대 3회까지 pending 유지."""
        try:
            payload = json.loads(row.payload_json)
        except json.JSONDecodeError:
            payload = {}
        title, body = _notification_copy(row.channel, payload)

        expo_tokens = [t for t in tokens if expo_push.is_expo_token(t)]
        if not expo_tokens:
            row.status = PushOutboxStatus.failed
            row.last_error = "no expo push token"
            return False

        messages = [
            {
                "to": token,
                "title": title,
                "body": body,
                "data": payload,
                "sound": "default",
                "channelId": "default",
            }
            for token in expo_tokens
        ]
        try:
            errors = expo_push.send_messages(messages)
        except Exception as exc:  # 네트워크/Expo 5xx — 재시도 대상
            if row.attempts >= _MAX_ATTEMPTS:
                row.status = PushOutboxStatus.failed
                row.last_error = f"send error: {exc}"
                return False
            row.status = PushOutboxStatus.pending
            row.last_error = f"retrying: {exc}"
            return False

        # 앱 삭제·토큰 만료로 영구 폐기된 주소는 다음 발송부터 제외한다.
        for token, error in zip(expo_tokens, errors):
            if not _is_invalid_expo_token_error(error):
                continue
            token_row = self.installations.get_token_by_value(token)
            if token_row is not None:
                self.installations.delete_token(token_row)

        delivered = [e for e in errors if e is None]
        if delivered:
            row.status = PushOutboxStatus.sent
            row.last_error = None
            return True

        # Expo의 rate limit·일시 장애·미완성 ticket 응답은 HTTP 예외가
        # 아니므로 여기까지 도달한다. 영구 오류만 섞인 경우는 실패로
        # 보관하고, 일시 오류만 남은 경우에는 최대 시도 횟수까지 재시도한다.
        ticket_errors = [e for e in errors if e]
        transient_errors = [
            error for error in ticket_errors if _is_transient_expo_ticket_error(error)
        ]
        hard_errors = [
            error
            for error in ticket_errors
            if not _is_transient_expo_ticket_error(error)
            and not _is_invalid_expo_token_error(error)
        ]
        if transient_errors and not hard_errors and row.attempts < _MAX_ATTEMPTS:
            row.status = PushOutboxStatus.pending
            row.last_error = f"retrying: {'; '.join(transient_errors)[:450]}"
            return False
        row.status = PushOutboxStatus.failed
        row.last_error = "; ".join(ticket_errors)[:500] or "unknown expo error"
        return False
