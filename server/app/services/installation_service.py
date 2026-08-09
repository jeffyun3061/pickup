from __future__ import annotations

import json
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.ids import new_id
from app.models.entities import DeviceToken, Installation
from app.repositories.installation_repository import InstallationRepository
from app.schemas.common import (
    DeviceTokenOut,
    DeviceTokenUpsert,
    InstallationCreateOut,
    InstallationPreferencesIn,
    InstallationPreferencesOut,
    NotificationPrefsIn,
)
from app.security import hash_password, verify_password


class InstallationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InstallationRepository(db)

    def register(self) -> InstallationCreateOut:
        installation_id = new_id("inst")
        secret = secrets.token_urlsafe(32)
        item = Installation(
            id=installation_id,
            secret_hash=hash_password(secret),
            game_ids_json="[]",
            notify_selected_game_news=True,
            notify_event_ending=True,
            notify_service_notices=True,
        )
        self.repo.add(item)
        return InstallationCreateOut(installation_id=installation_id, secret=secret)

    def authenticate(self, installation_id: str, secret: str) -> Installation:
        item = self.repo.get_active(installation_id)
        if item is None or not verify_password(secret, item.secret_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid installation credentials",
            )
        return item

    def upsert_device_token(self, installation: Installation, body: DeviceTokenUpsert) -> DeviceTokenOut:
        existing = self.repo.get_token_by_value(body.token)
        if existing and existing.installation_id != installation.id:
            # 토큰은 기기 단위 — 이전 설치에서 이전
            existing.installation_id = installation.id
            existing.platform = body.platform
            self.repo.save_token(existing)
            return DeviceTokenOut(platform=existing.platform, token=existing.token, updated=True)

        if existing:
            existing.platform = body.platform
            self.repo.save_token(existing)
            return DeviceTokenOut(platform=existing.platform, token=existing.token, updated=True)

        token = DeviceToken(
            id=new_id("dt"),
            installation_id=installation.id,
            platform=body.platform,
            token=body.token,
        )
        self.repo.add_token(token)
        return DeviceTokenOut(platform=token.platform, token=token.token, updated=False)

    def update_preferences(
        self,
        installation: Installation,
        body: InstallationPreferencesIn,
    ) -> InstallationPreferencesOut:
        unique_ids = []
        seen: set[str] = set()
        for game_id in body.game_ids:
            cleaned = game_id.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                unique_ids.append(cleaned)

        installation.game_ids_json = json.dumps(unique_ids, ensure_ascii=False)
        installation.notify_selected_game_news = body.notifications.selected_game_news
        installation.notify_event_ending = body.notifications.event_ending
        installation.notify_service_notices = body.notifications.service_notices
        self.repo.save(installation)
        return self._prefs_out(installation)

    def get_preferences(self, installation: Installation) -> InstallationPreferencesOut:
        return self._prefs_out(installation)

    def _prefs_out(self, installation: Installation) -> InstallationPreferencesOut:
        try:
            raw = json.loads(installation.game_ids_json or "[]")
            game_ids = [x for x in raw if isinstance(x, str)]
        except json.JSONDecodeError:
            game_ids = []
        return InstallationPreferencesOut(
            game_ids=game_ids,
            notifications=NotificationPrefsIn(
                selected_game_news=installation.notify_selected_game_news,
                event_ending=installation.notify_event_ending,
                service_notices=installation.notify_service_notices,
            ),
        )
