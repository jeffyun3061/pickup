from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import Content, ContentStatus, Game


class ContentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_published(
        self,
        game_ids: list[str] | None = None,
        *,
        limit: int = 100,
    ) -> list[Content]:
        stmt = (
            select(Content)
            .options(joinedload(Content.game))
            .join(Game, Game.id == Content.game_id)
            .where(Content.status == ContentStatus.published)
            # 비활성 카탈로그의 발행 기록은 관리자 감사용으로 보존하되
            # 모바일 공개 피드에서는 노출하지 않는다.
            .where(Game.is_active.is_(True))
            .order_by(Content.published_at.desc())
        )
        if game_ids:
            stmt = stmt.where(Content.game_id.in_(game_ids))
        stmt = stmt.limit(max(1, min(limit, 200)))
        return list(self.db.scalars(stmt).unique().all())

    def list_all(self, status: ContentStatus | None = None) -> list[Content]:
        stmt = select(Content).options(joinedload(Content.game)).order_by(Content.updated_at.desc())
        if status:
            stmt = stmt.where(Content.status == status)
        return list(self.db.scalars(stmt).unique().all())

    def get(self, content_id: str) -> Content | None:
        stmt = (
            select(Content)
            .options(joinedload(Content.game))
            .where(Content.id == content_id)
        )
        return self.db.scalars(stmt).unique().first()

    def filter_existing_idempotency_keys(self, keys: list[str]) -> set[str]:
        if not keys:
            return set()
        stmt = select(Content.idempotency_key).where(Content.idempotency_key.in_(keys))
        return {key for key in self.db.scalars(stmt).all() if key}

    def get_by_idempotency_key(self, key: str) -> Content | None:
        stmt = (
            select(Content)
            .options(joinedload(Content.game))
            .where(Content.idempotency_key == key)
        )
        return self.db.scalars(stmt).unique().first()

    def add(self, content: Content) -> Content:
        self.db.add(content)
        self.db.flush()
        return content

    def save(self, content: Content) -> Content:
        self.db.add(content)
        self.db.flush()
        return content

    def delete(self, content: Content) -> None:
        self.db.delete(content)
        self.db.flush()
