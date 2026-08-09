from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import DeviceToken, Installation


class InstallationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, installation_id: str) -> Installation | None:
        return self.db.get(Installation, installation_id)

    def get_active(self, installation_id: str) -> Installation | None:
        item = self.get(installation_id)
        if item is None or item.revoked_at is not None:
            return None
        return item

    def list_active_with_tokens(self) -> list[Installation]:
        stmt = (
            select(Installation)
            .options(joinedload(Installation.device_tokens))
            .where(Installation.revoked_at.is_(None))
        )
        return list(self.db.scalars(stmt).unique().all())

    def add(self, item: Installation) -> Installation:
        self.db.add(item)
        self.db.flush()
        return item

    def save(self, item: Installation) -> Installation:
        self.db.add(item)
        self.db.flush()
        return item

    def get_token_by_value(self, token: str) -> DeviceToken | None:
        stmt = select(DeviceToken).where(DeviceToken.token == token)
        return self.db.scalars(stmt).first()

    def list_tokens(self, installation_id: str) -> list[DeviceToken]:
        stmt = select(DeviceToken).where(DeviceToken.installation_id == installation_id)
        return list(self.db.scalars(stmt).all())

    def add_token(self, token: DeviceToken) -> DeviceToken:
        self.db.add(token)
        self.db.flush()
        return token

    def save_token(self, token: DeviceToken) -> DeviceToken:
        self.db.add(token)
        self.db.flush()
        return token
