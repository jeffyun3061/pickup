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
