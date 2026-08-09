from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.ids import new_id
from app.domain.push_targeting import (
    NotificationPrefs,
    should_notify_content_publish,
    should_notify_service_announcement,
)
from app.models.entities import Announcement, Content, Installation, PushOutbox, PushOutboxStatus
from app.repositories.installation_repository import InstallationRepository
from app.repositories.push_outbox_repository import PushOutboxRepository
from app.schemas.common import PushDispatchOut

logger = logging.getLogger(__name__)


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
    """발행 시 outbox enqueue + 스텁 디스패치(실 FCM은 워커 교체)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.installations = InstallationRepository(db)
        self.outbox = PushOutboxRepository(db)

    def enqueue_content_published(self, content: Content) -> int:
        payload = {
            "channel": "content_published",
            "content_id": content.id,
            "game_id": content.game_id,
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
            self.outbox.add(
                PushOutbox(
                    id=new_id("po"),
                    installation_id=installation.id,
                    channel="content_published",
                    payload_json=json.dumps(payload, ensure_ascii=False),
                    status=PushOutboxStatus.pending,
                    available_at=datetime.now(timezone.utc),
                )
            )
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
            self.outbox.add(
                PushOutbox(
                    id=new_id("po"),
                    installation_id=installation.id,
                    channel="service_notice",
                    payload_json=json.dumps(payload, ensure_ascii=False),
                    status=PushOutboxStatus.pending,
                    available_at=datetime.now(timezone.utc),
                )
            )
            count += 1
        return count

    def dispatch_pending(self, *, limit: int = 100) -> PushDispatchOut:
        """
        인프라(FCM) 없이 outbox 계약을 검증하는 스텁 발송기.
        프로덕션에서는 동일 메서드에서 실제 PushSender로 교체한다.
        """
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
            else:
                # 스텁: 토큰·페이로드를 로그로만 남기고 sent 처리
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
            self.outbox.save(row)
        return PushDispatchOut(processed=len(pending), sent=sent, failed=failed)
