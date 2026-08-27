from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.ids import new_id
from app.models.entities import DeviceToken, Installation, InstallationGame
from app.repositories.game_repository import GameRepository
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

MAX_SELECTED_GAMES = 8


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

        if len(unique_ids) > MAX_SELECTED_GAMES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"You can select up to {MAX_SELECTED_GAMES} games",
            )

        # 공개 카탈로그에서 비활성화된 게임은 구버전 클라이언트가 보내도
        # 선택 목록에 남기지 않는다. 그래야 홈·랭킹·알림 대상이 일치한다.
        active_ids = GameRepository(self.db).list_active_ids()
        selected_ids = [game_id for game_id in unique_ids if game_id in active_ids]

        installation.game_ids_json = json.dumps(selected_ids, ensure_ascii=False)
        installation.notify_selected_game_news = body.notifications.selected_game_news
        installation.notify_event_ending = body.notifications.event_ending
        installation.notify_service_notices = body.notifications.service_notices

        # JSON은 구버전 클라이언트 응답 호환용으로 유지하고, 집계 원천은
        # 정규화 테이블로 동기화한다. 비활성·삭제된 게임 ID는 JSON과 관계
        # 테이블 모두에서 제외해 오래된 클라이언트도 안전하게 정리한다.
        self.db.query(InstallationGame).filter(
            InstallationGame.installation_id == installation.id
        ).delete(synchronize_session=False)
        for game_id in selected_ids:
            if game_id in active_ids:
                self.db.add(
                    InstallationGame(
                        installation_id=installation.id,
                        game_id=game_id,
                    )
                )
        self.repo.save(installation)
        return self._prefs_out(installation)

    def get_preferences(self, installation: Installation) -> InstallationPreferencesOut:
        return self._prefs_out(installation)

    def revoke(self, installation: Installation) -> None:
        """설치 해지: 푸시 토큰·관심 게임을 즉시 발송 대상에서 제거한다."""
        self.db.query(DeviceToken).filter(
            DeviceToken.installation_id == installation.id
        ).delete(synchronize_session=False)
        self.db.query(InstallationGame).filter(
            InstallationGame.installation_id == installation.id
        ).delete(synchronize_session=False)
        installation.game_ids_json = "[]"
        installation.notify_selected_game_news = False
        installation.notify_event_ending = False
        installation.notify_service_notices = False
        installation.revoked_at = datetime.now(timezone.utc)
        self.repo.save(installation)

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
