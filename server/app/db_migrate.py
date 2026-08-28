"""
경량 스키마 마이그레이션.

Alembic 없이 운영하는 소규모 배포용: create_all 이후 기존 테이블에 새 컬럼만 추가한다.
컬럼 삭제·타입 변경이 필요해지면 그때 Alembic으로 승격한다 (ADR-012).
"""

from __future__ import annotations

import logging
import json
from datetime import datetime, timedelta, timezone

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
    _backdate_demo_contents(engine)


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


def _backdate_demo_contents(engine: Engine) -> None:
    """발표용 목업 소식을 과거 기록으로 유지한다.

    목업은 화면을 채우기 위한 데이터이므로 오늘 발행된 운영 소식과 같은
    날짜에 보이면 발표 시연을 가린다. 화면을 채우는 ``c_demo_`` ID만
    대상으로 하며, ``c_test_news_``는 관리자가 오늘 발행할 테스트 소식이므로
    현재 시각을 유지한다. 이미 충분히 오래된 행은 건드리지 않아 매 부팅에도
    멱등적이다.
    """
    from sqlalchemy import select

    from app.models.entities import Content, ContentStatus

    # 발표용 데이터는 최소 일주일 전 기록으로 보이게 한다. 날짜를 고정하지
    # 않고 매 부팅 현재 시각 기준으로 계산하므로 시간이 지나도 홈의 오늘
    # 소식으로 되돌아오지 않는다.
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    with Session(engine) as db:
        rows = db.scalars(
            select(Content).where(
                Content.id.like("c_demo_%"),
                Content.status == ContentStatus.published,
            ).order_by(Content.id.asc())
        ).all()
        logger.info("presentation demo contents checked: %d", len(rows))
        changed = False
        for index, content in enumerate(rows):
            historical_at = cutoff - timedelta(minutes=index)
            published_at = content.published_at
            if published_at is not None and published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
            if published_at is not None and published_at <= cutoff:
                continue
            content.published_at = historical_at
            created_at = content.created_at
            if created_at is not None and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            updated_at = content.updated_at
            if updated_at is not None and updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            if created_at is None or created_at > historical_at:
                content.created_at = historical_at
            if updated_at is None or updated_at > historical_at:
                content.updated_at = historical_at
            changed = True
        if changed:
            db.commit()
            logger.info("backdated presentation demo contents")
