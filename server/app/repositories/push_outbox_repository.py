from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import PushOutbox, PushOutboxStatus


class PushOutboxRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, item: PushOutbox) -> PushOutbox:
        self.db.add(item)
        self.db.flush()
        return item

    def list_pending(self, *, limit: int = 100) -> list[PushOutbox]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(PushOutbox)
            .where(
                PushOutbox.status == PushOutboxStatus.pending,
                PushOutbox.available_at <= now,
            )
            .order_by(PushOutbox.created_at.asc())
            .limit(limit)
            # 관리자 수동 발송과 스케줄러가 겹쳐도 같은 알림을 두 번
            # 외부 provider로 보내지 않도록 PostgreSQL 행 잠금을 사용한다.
            # skip_locked는 이미 다른 실행기가 처리 중인 행을 건너뛰어
            # 대기열 전체가 막히지 않게 한다.
            .with_for_update(skip_locked=True)
        )
        return list(self.db.scalars(stmt).all())

    def save(self, item: PushOutbox) -> PushOutbox:
        self.db.add(item)
        self.db.flush()
        return item

    def count_by_status(self, status: PushOutboxStatus) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(PushOutbox).where(PushOutbox.status == status)
        return int(self.db.scalar(stmt) or 0)
