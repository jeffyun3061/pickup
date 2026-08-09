from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Announcement


class AnnouncementRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_published(self) -> list[Announcement]:
        stmt = (
            select(Announcement)
            .where(Announcement.is_published.is_(True))
            .order_by(Announcement.published_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_all(self) -> list[Announcement]:
        stmt = select(Announcement).order_by(Announcement.published_at.desc())
        return list(self.db.scalars(stmt).all())

    def get(self, announcement_id: str) -> Announcement | None:
        return self.db.get(Announcement, announcement_id)

    def add(self, item: Announcement) -> Announcement:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def save(self, item: Announcement) -> Announcement:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: Announcement) -> None:
        self.db.delete(item)
        self.db.commit()
