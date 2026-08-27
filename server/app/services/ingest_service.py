from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.ids import new_id
from app.domain.source_schedule import next_source_run, resolve_active_run_at
from app.domain.source_url import UnsafeSourceUrlError, validate_public_http_url
from app.models.entities import (
    AuditLog,
    IngestRun,
    IngestRunStatus,
    IngestSource,
    IngestSourceType,
)
from app.repositories.game_repository import GameRepository
from app.repositories.ingest_repository import IngestRepository
from app.schemas.common import (
    IngestJobOut,
    IngestRunComplete,
    IngestRunOut,
    IngestSourceCreate,
    IngestSourceOut,
    IngestSourceUpdate,
)


class IngestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = IngestRepository(db)
        self.games = GameRepository(db)

    def _audit(
        self,
        action: str,
        entity_id: str,
        detail: str = "",
        *,
        actor: str = "admin",
    ) -> None:
        """수집 소스 제어면의 변경 이력도 콘텐츠와 같은 감사 로그에 기록한다."""
        self.db.add(
            AuditLog(
                id=new_id("al"),
                actor=actor,
                action=action,
                entity="ingest_source",
                entity_id=entity_id,
                detail=detail[:500],
            )
        )

    def list_sources(self) -> list[IngestSourceOut]:
        return [self._source_out(source) for source in self.repo.list_sources()]

    def get_source(self, source_id: str) -> IngestSource:
        source = self.repo.get_source(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Ingest source not found")
        return source

    def create_source(self, body: IngestSourceCreate, *, actor: str = "admin") -> IngestSourceOut:
        self._validate_game(body.game_id)
        endpoint_url = self._validate_url(body.endpoint_url)
        now = datetime.now(timezone.utc)
        config = body.config or {}
        source = IngestSource(
            id=new_id("src"),
            name=body.name,
            source_type=IngestSourceType(body.source_type),
            game_id=body.game_id,
            endpoint_url=endpoint_url,
            interval_minutes=body.interval_minutes,
            enabled=body.enabled,
            auto_publish=body.auto_publish,
            config_json=json.dumps(config, ensure_ascii=False),
            secret_env_name=body.secret_env_name,
            next_run_at=resolve_active_run_at(now, config) if body.enabled else None,
        )
        saved = self.repo.add_source(source)
        self._audit("수집 소스 등록", saved.id, saved.name, actor=actor)
        return self._source_out(saved)

    def update_source(
        self,
        source_id: str,
        body: IngestSourceUpdate,
        *,
        actor: str = "admin",
    ) -> IngestSourceOut:
        source = self.get_source(source_id)
        data = body.model_dump(exclude_unset=True)
        if data.get("game_id"):
            self._validate_game(data["game_id"])
        if data.get("endpoint_url"):
            data["endpoint_url"] = self._validate_url(data["endpoint_url"])
        if "source_type" in data and data["source_type"]:
            data["source_type"] = IngestSourceType(data["source_type"])
        if "config" in data:
            data["config_json"] = json.dumps(data.pop("config") or {}, ensure_ascii=False)
        for key, value in data.items():
            setattr(source, key, value)
        if "enabled" in data or "config_json" in data:
            source.next_run_at = (
                resolve_active_run_at(
                    datetime.now(timezone.utc), self._source_config(source)
                )
                if source.enabled
                else None
            )
        saved = self.repo.save_source(source)
        changed = ", ".join(sorted(data)) or "변경 없음"
        self._audit("수집 소스 수정", saved.id, f"{saved.name}: {changed}", actor=actor)
        return self._source_out(saved)

    def delete_source(self, source_id: str, *, actor: str = "admin") -> None:
        source = self.get_source(source_id)
        self._audit("수집 소스 삭제", source.id, source.name, actor=actor)
        self.repo.delete_source(source)

    def enqueue_run(self, source_id: str) -> IngestRunOut:
        source = self.get_source(source_id)
        run = IngestRun(
            id=new_id("run"),
            source_id=source.id,
            status=IngestRunStatus.pending,
        )
        saved = self.repo.add_run(run)
        saved.source = source
        return self._run_out(saved)

    def list_runs(self, limit: int = 50) -> list[IngestRunOut]:
        return [self._run_out(run) for run in self.repo.list_runs(limit)]

    def claim_job(self) -> IngestJobOut | None:
        now = datetime.now(timezone.utc)
        self._recover_stale_runs(now)
        run = self.repo.next_pending_run()
        if run is None:
            source = self._next_due_active_source(now)
            if source is None:
                return None
            run = self.repo.add_run(
                IngestRun(
                    id=new_id("run"),
                    source_id=source.id,
                    status=IngestRunStatus.pending,
                    attempt=source.consecutive_failures + 1,
                )
            )
            run.source = source

        run.status = IngestRunStatus.running
        run.started_at = now
        source = run.source
        source.next_run_at = next_source_run(
            now, source.interval_minutes, self._source_config(source)
        )
        self.repo.save_source(source)
        self.repo.save_run(run)
        return IngestJobOut(
            run=self._run_out(run),
            source=self._source_out(source),
            http_cache=self._http_cache(source),
        )

    def _recover_stale_runs(self, now: datetime) -> int:
        """collector 중단으로 남은 running 작업을 실패 처리하고 재시도 예약한다."""
        from app.config import get_settings

        cutoff = now - timedelta(minutes=get_settings().ingest_stale_after_minutes)
        recovered = 0
        for run in self.repo.stale_running_runs(cutoff):
            source = run.source
            run.status = IngestRunStatus.failed
            run.error = "collector heartbeat timed out; scheduled for retry"
            run.completed_at = now
            source.last_run_at = now
            source.last_status = IngestRunStatus.failed.value
            source.consecutive_failures += 1
            retry_minutes = min(5 * (2 ** (source.consecutive_failures - 1)), 360)
            source.next_run_at = (
                next_source_run(now, retry_minutes, self._source_config(source))
                if source.enabled
                else None
            )
            self.repo.save_source(source)
            self.repo.save_run(run)
            recovered += 1
        return recovered

    def complete_run(self, run_id: str, body: IngestRunComplete) -> IngestRunOut:
        run = self.repo.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Ingest run not found")
        if run.status != IngestRunStatus.running:
            raise HTTPException(status_code=409, detail="Only running jobs can be completed")

        now = datetime.now(timezone.utc)
        run.status = IngestRunStatus(body.status)
        run.items_seen = body.items_seen
        run.items_created = body.items_created
        run.not_modified = body.not_modified
        run.error = body.error
        run.completed_at = now

        source = run.source
        source.last_run_at = now
        source.last_status = body.status
        if body.http_cache is not None:
            source.http_cache_json = json.dumps(body.http_cache, ensure_ascii=False)
        if run.status == IngestRunStatus.succeeded:
            source.consecutive_failures = 0
            source.next_run_at = next_source_run(
                now, source.interval_minutes, self._source_config(source)
            )
            # 셀렉터 깨짐 감지: 페이지가 바뀌었는데(0건 파싱) 연속되면 quiet 경고
            if body.not_modified:
                pass  # 변화 없음은 정상 — 카운터 유지
            elif body.items_seen == 0:
                source.consecutive_empty_runs += 1
            else:
                source.consecutive_empty_runs = 0
        else:
            source.consecutive_failures += 1
            retry_minutes = min(5 * (2 ** (source.consecutive_failures - 1)), 360)
            source.next_run_at = next_source_run(
                now, retry_minutes, self._source_config(source)
            )
        self.repo.save_source(source)
        return self._run_out(self.repo.save_run(run))

    def assert_source_exists(self, source_id: str) -> IngestSource:
        return self.get_source(source_id)

    def _validate_game(self, game_id: str) -> None:
        if not self.games.get(game_id):
            raise HTTPException(status_code=400, detail="Unknown game_id")

    @staticmethod
    def _validate_url(value: str) -> str:
        try:
            return validate_public_http_url(value)
        except UnsafeSourceUrlError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @staticmethod
    def _http_cache(source: IngestSource) -> dict[str, str]:
        try:
            cache = json.loads(source.http_cache_json or "{}")
        except json.JSONDecodeError:
            return {}
        if not isinstance(cache, dict):
            return {}
        return {str(k): str(v) for k, v in cache.items()}

    @staticmethod
    def _source_config(source: IngestSource) -> dict[str, object]:
        try:
            config = json.loads(source.config_json or "{}")
        except json.JSONDecodeError:
            return {}
        return config if isinstance(config, dict) else {}

    def _next_due_active_source(self, now: datetime) -> IngestSource | None:
        """기존 due 값이 야간이면 다음 활성시간으로 옮기고 다른 due 소스를 계속 찾는다."""
        while source := self.repo.next_due_source(now):
            allowed_at = resolve_active_run_at(now, self._source_config(source))
            if allowed_at <= now:
                return source
            source.next_run_at = allowed_at
            self.repo.save_source(source)
        return None

    @staticmethod
    def _health(source: IngestSource) -> str:
        if source.consecutive_failures >= 3:
            return "failing"
        if source.consecutive_empty_runs >= 5:
            return "quiet"
        return "ok"

    def _source_out(self, source: IngestSource) -> IngestSourceOut:
        game = self.games.get(source.game_id)
        config = self._source_config(source)
        return IngestSourceOut(
            id=source.id,
            name=source.name,
            source_type=source.source_type.value,
            game_id=source.game_id,
            game_name=game.name if game else source.game_id,
            endpoint_url=source.endpoint_url,
            interval_minutes=source.interval_minutes,
            enabled=source.enabled,
            auto_publish=source.auto_publish,
            config=config if isinstance(config, dict) else {},
            secret_env_name=source.secret_env_name,
            next_run_at=source.next_run_at,
            last_run_at=source.last_run_at,
            last_status=source.last_status,
            consecutive_failures=source.consecutive_failures,
            consecutive_empty_runs=source.consecutive_empty_runs,
            health=self._health(source),
            created_at=source.created_at,
            stat_approved=source.stat_approved,
            stat_edited=source.stat_edited,
            stat_retracted=source.stat_retracted,
            # 무수정 승인 20건 이상 + 수정/회수 0건이면 자동 발행 승격 제안
            promote_suggested=(
                not source.auto_publish
                and source.stat_approved >= 20
                and source.stat_edited == 0
                and source.stat_retracted == 0
            ),
        )

    @staticmethod
    def _run_out(run: IngestRun) -> IngestRunOut:
        return IngestRunOut(
            id=run.id,
            source_id=run.source_id,
            source_name=run.source.name,
            status=run.status.value,
            attempt=run.attempt,
            items_seen=run.items_seen,
            items_created=run.items_created,
            not_modified=run.not_modified,
            error=run.error,
            queued_at=run.queued_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )
