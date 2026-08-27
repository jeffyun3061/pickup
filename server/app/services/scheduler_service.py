"""
주기 작업 러너 — 이벤트 마감 리마인더 · 예약 발행 · 데드링크 감지.

FastAPI lifespan에서 asyncio 태스크로 SCHEDULER_INTERVAL_SECONDS마다 실행된다.
각 작업은 짧고 멱등해서 중복 실행에도 안전하다.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.source_url import UnsafeSourceUrlError, validate_public_http_url
from app.models.entities import Content, ContentKind, ContentStatus

logger = logging.getLogger(__name__)

_REMINDER_WINDOW_HOURS = 24
_LINK_CHECK_INTERVAL = timedelta(hours=24)
_LINK_CHECK_BATCH = 50
# 앱의 "이벤트 기간"에 노출되는 기간 한정 콘텐츠. update는 종료일이
# 있더라도 일반 공지로 취급하고, 실제 마감 알림 대상에서는 제외한다.
_TIME_BOUND_KINDS = (ContentKind.event, ContentKind.popup, ContentKind.goods)

# 프로세스 단위 데드링크 검사 시각 (일 1회)
_last_link_check: datetime | None = None


class SchedulerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_cycle(self) -> dict[str, int]:
        """한 사이클: 리마인더 → 예약 발행 → (하루 1회) 데드링크."""
        global _last_link_check
        now = datetime.now(timezone.utc)

        reminders = self.send_event_ending_reminders(now)
        scheduled = self.publish_scheduled(now)

        broken = 0
        if _last_link_check is None or now - _last_link_check >= _LINK_CHECK_INTERVAL:
            broken = self.check_dead_links()
            _last_link_check = now

        if reminders or scheduled or broken:
            logger.info(
                "scheduler cycle: reminders=%d scheduled_published=%d broken_links=%d",
                reminders,
                scheduled,
                broken,
            )
        return {"reminders": reminders, "scheduled": scheduled, "broken_links": broken}

    def send_event_ending_reminders(self, now: datetime) -> int:
        """마감 24시간 내 발행 이벤트 → 마이픽 유저에게 리마인더 enqueue (1회만)."""
        from app.services.push_service import PushService

        window_end = now + timedelta(hours=_REMINDER_WINDOW_HOURS)
        stmt = select(Content).where(
            Content.status == ContentStatus.published,
            Content.kind.in_(_TIME_BOUND_KINDS),
            Content.ends_at.is_not(None),
            Content.ends_at > now,
            Content.ends_at <= window_end,
            Content.event_reminder_sent_at.is_(None),
        ).with_for_update(skip_locked=True)
        push = PushService(self.db)
        total = 0
        for content in self.db.scalars(stmt):
            total += push.enqueue_event_ending(content)
            content.event_reminder_sent_at = now
        return total

    def publish_scheduled(self, now: datetime) -> int:
        """예약 시각이 지난 검수 완료 소식을 발행한다."""
        from app.schemas.common import ContentUpdate
        from app.services.admin_service import AdminService

        stmt = select(Content.id).where(
            Content.status == ContentStatus.reviewed,
            Content.scheduled_publish_at.is_not(None),
            Content.scheduled_publish_at <= now,
        )
        admin = AdminService(self.db)
        count = 0
        for content_id in list(self.db.scalars(stmt)):
            admin.update_content(
                content_id, ContentUpdate(status="published"), actor="scheduler"
            )
            count += 1
        return count

    def check_dead_links(self) -> int:
        """발행 소식 원문 URL을 확인해 404/410이면 플래그만 남긴다 (자동 회수 없음)."""
        stmt = (
            select(Content)
            .where(
                Content.status == ContentStatus.published,
                Content.official_url != "",
                Content.link_broken.is_(False),
            )
            .order_by(Content.published_at.desc())
            .limit(_LINK_CHECK_BATCH)
        )
        broken = 0
        # 원문 URL은 관리자/수집 데이터가 섞이는 경계다. 매번 공개 IP로
        # 재검증하고, redirect를 따라가 내부 주소로 우회 요청하지 않는다.
        with httpx.Client(timeout=httpx.Timeout(8.0), follow_redirects=False) as client:
            for content in self.db.scalars(stmt):
                try:
                    validate_public_http_url(content.official_url)
                    res = client.head(content.official_url)
                    if res.status_code in {404, 410}:
                        content.link_broken = True
                        broken += 1
                except (UnsafeSourceUrlError, httpx.HTTPError):
                    # 사설/예약 주소와 네트워크 오류는 서버가 요청하지 않고
                    # 링크 상태도 오판하지 않는다. 운영자가 원문을 검수한다.
                    continue
        return broken


def run_scheduler_cycle() -> None:
    """lifespan 태스크 진입점 — 독립 세션에서 한 사이클 실행 + 대기 푸시 발송."""
    from app.db import SessionLocal
    from app.services.push_service import PushService

    db = SessionLocal()
    try:
        SchedulerService(db).run_cycle()
        PushService(db).dispatch_pending(limit=500)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("scheduler cycle failed")
    finally:
        db.close()
