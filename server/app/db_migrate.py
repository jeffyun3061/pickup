"""
경량 스키마 마이그레이션.

Alembic 없이 운영하는 소규모 배포용: create_all 이후 기존 테이블에 새 컬럼만 추가한다.
컬럼 삭제·타입 변경이 필요해지면 그때 Alembic으로 승격한다 (ADR-012).
"""

from __future__ import annotations

import logging
import json

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 테이블 → (컬럼명, 방언 중립 DDL)
_MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "games": [
        ("image_source_url", "VARCHAR(500)"),
        ("image_rights_status", "VARCHAR(20) NOT NULL DEFAULT 'unverified'"),
        ("fallback_image_key", "VARCHAR(64) NOT NULL DEFAULT 'coverTactical'"),
    ],
    "contents": [
        ("raw_text", "TEXT"),
        ("analysis_json", "TEXT NOT NULL DEFAULT '{}'"),
        ("summary_status", "VARCHAR(12) NOT NULL DEFAULT 'none'"),
        ("summarized_at", "TIMESTAMP"),
        # ORM의 DateTime(timezone=True)와 동일하게 유지한다. 기존 DB에
        # 추가되는 컬럼도 UTC offset을 잃지 않아 예약 발행·마감 알림이
        # 새 DB와 마이그레이션 DB에서 같은 방식으로 동작한다.
        ("origin_published_at", "TIMESTAMP WITH TIME ZONE"),
        ("source_id", "VARCHAR(64)"),
        ("image_source_url", "VARCHAR(500)"),
        ("image_rights_status", "VARCHAR(20) NOT NULL DEFAULT 'unverified'"),
        ("needs_review_reason", "VARCHAR(200)"),
        ("scheduled_publish_at", "TIMESTAMP WITH TIME ZONE"),
        ("link_broken", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("edited_after_ingest", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("auto_published", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("event_reminder_sent_at", "TIMESTAMP WITH TIME ZONE"),
    ],
    "ingest_sources": [
        ("auto_publish", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("http_cache_json", "TEXT NOT NULL DEFAULT '{}'"),
        ("consecutive_empty_runs", "INTEGER NOT NULL DEFAULT 0"),
        ("stat_approved", "INTEGER NOT NULL DEFAULT 0"),
        ("stat_edited", "INTEGER NOT NULL DEFAULT 0"),
        ("stat_retracted", "INTEGER NOT NULL DEFAULT 0"),
    ],
    "ingest_runs": [
        ("not_modified", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ],
}


def ensure_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _MIGRATIONS.items():
            if table not in tables:
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, ddl in columns:
                if name in existing:
                    continue
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                logger.info("schema migrated: %s.%s", table, name)

    _backfill_installation_games(engine)


def _backfill_installation_games(engine: Engine) -> None:
    """구버전 JSON 관심 목록을 정규화 테이블로 한 번 채운다.

    설치 데이터가 이미 있는 배포에서 랭킹이 0으로 되돌아가지 않도록
    서버 시작 때 멱등적으로 수행한다. 존재하지 않는 게임 ID는 무시한다.
    """
    from sqlalchemy import select

    from app.models.entities import Game, Installation, InstallationGame

    with Session(engine) as db:
        game_ids = set(db.scalars(select(Game.id)).all())
        existing = set(
            db.execute(
                select(InstallationGame.installation_id, InstallationGame.game_id)
            ).all()
        )
        changed = False
        for installation in db.scalars(select(Installation)).all():
            try:
                raw_ids = json.loads(installation.game_ids_json or "[]")
            except json.JSONDecodeError:
                raw_ids = []
            if not isinstance(raw_ids, list):
                continue
            for game_id in raw_ids[:8]:
                key = (installation.id, game_id)
                if isinstance(game_id, str) and game_id in game_ids and key not in existing:
                    db.add(InstallationGame(installation_id=installation.id, game_id=game_id))
                    existing.add(key)
                    changed = True
        if changed:
            db.commit()
            logger.info("backfilled installation_games from legacy preferences")
