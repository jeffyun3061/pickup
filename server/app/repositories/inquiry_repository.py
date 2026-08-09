from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Inquiry


class InquiryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Inquiry]:
        stmt = select(Inquiry).order_by(Inquiry.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get(self, inquiry_id: str) -> Inquiry | None:
        return self.db.get(Inquiry, inquiry_id)

    def add(self, item: Inquiry) -> Inquiry:
        self.db.add(item)
        self.db.flush()
        return item

    def save(self, item: Inquiry) -> Inquiry:
        self.db.add(item)
        self.db.flush()
        return item
