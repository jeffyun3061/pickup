from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import Content, ContentStatus


class ContentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_published(self, game_ids: list[str] | None = None) -> list[Content]:
        stmt = (
            select(Content)
            .options(joinedload(Content.game))
            .where(Content.status == ContentStatus.published)
            .order_by(Content.published_at.desc())
        )
        if game_ids:
            stmt = stmt.where(Content.game_id.in_(game_ids))
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
