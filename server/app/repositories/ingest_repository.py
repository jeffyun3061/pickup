from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.entities import IngestRun, IngestRunStatus, IngestSource


class IngestRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_sources(self) -> list[IngestSource]:
        stmt = select(IngestSource).order_by(IngestSource.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_source(self, source_id: str) -> IngestSource | None:
        return self.db.get(IngestSource, source_id)

    def add_source(self, source: IngestSource) -> IngestSource:
        self.db.add(source)
        self.db.flush()
        return source

    def save_source(self, source: IngestSource) -> IngestSource:
        self.db.add(source)
        self.db.flush()
        return source

    def delete_source(self, source: IngestSource) -> None:
        self.db.delete(source)
        self.db.flush()

    def list_runs(self, limit: int = 50) -> list[IngestRun]:
        stmt = (
            select(IngestRun)
            .options(joinedload(IngestRun.source))
            .order_by(IngestRun.queued_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_run(self, run_id: str) -> IngestRun | None:
        stmt = (
            select(IngestRun)
            .options(joinedload(IngestRun.source))
            .where(IngestRun.id == run_id)
        )
        return self.db.scalars(stmt).unique().first()

    def add_run(self, run: IngestRun) -> IngestRun:
        self.db.add(run)
        self.db.flush()
        return run

    def save_run(self, run: IngestRun) -> IngestRun:
        self.db.add(run)
        self.db.flush()
        return run

    def next_pending_run(self) -> IngestRun | None:
        # PG는 outer join(eager load)에 FOR UPDATE를 허용하지 않으므로
        # runs 행만 잠그고(of=IngestRun) source는 selectinload로 따로 읽는다
        stmt = (
            select(IngestRun)
            .options(selectinload(IngestRun.source))
            .where(IngestRun.status == IngestRunStatus.pending)
            .order_by(IngestRun.queued_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True, of=IngestRun)
        )
        return self.db.scalars(stmt).unique().first()

    def stale_running_runs(self, cutoff: datetime) -> list[IngestRun]:
        """정상 완료 신호를 받지 못한 collector 작업을 잠가서 회수한다."""
        stmt = (
            select(IngestRun)
            .options(selectinload(IngestRun.source))
            .where(
                IngestRun.status == IngestRunStatus.running,
                IngestRun.started_at.is_not(None),
                IngestRun.started_at <= cutoff,
            )
            .order_by(IngestRun.started_at.asc())
            .with_for_update(skip_locked=True, of=IngestRun)
        )
        return list(self.db.scalars(stmt).unique().all())

    def next_due_source(self, now: datetime) -> IngestSource | None:
        stmt = (
            select(IngestSource)
            .where(
                IngestSource.enabled.is_(True),
                IngestSource.next_run_at.is_not(None),
                IngestSource.next_run_at <= now,
            )
            .order_by(IngestSource.next_run_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        return self.db.scalars(stmt).first()
