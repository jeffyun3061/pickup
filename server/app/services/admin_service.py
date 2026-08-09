from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.content_status import ContentStatusMachine, InvalidTransitionError
from app.domain.ids import new_id
from app.models.entities import (
    Announcement,
    Content,
    ContentKind,
    ContentStatus,
    Game,
    InquiryStatus,
)
from app.repositories.announcement_repository import AnnouncementRepository
from app.repositories.content_repository import ContentRepository
from app.repositories.game_repository import GameRepository
from app.repositories.inquiry_repository import InquiryRepository
from app.schemas.common import (
    AnnouncementCreate,
    AnnouncementOut,
    ContentCreate,
    ContentOut,
    ContentUpdate,
    GameCreate,
    GameOut,
    GameUpdate,
    InquiryOut,
    LoginIn,
    TokenOut,
)
from app.security import create_access_token, verify_password
from app.services.mappers import (
    announcement_to_out,
    content_to_out,
    game_to_out,
    inquiry_to_out,
)


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.games = GameRepository(db)
        self.contents = ContentRepository(db)
        self.announcements = AnnouncementRepository(db)
        self.inquiries = InquiryRepository(db)
        self.settings = get_settings()

    def login(self, body: LoginIn) -> TokenOut:
        if body.username != self.settings.admin_username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(body.password, self.settings.admin_password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return TokenOut(access_token=create_access_token(body.username))

    def list_games(self) -> list[GameOut]:
        return [game_to_out(g) for g in self.games.list_all()]

    def create_game(self, body: GameCreate) -> GameOut:
        game_id = body.id or new_id("g")
        if self.games.get(game_id):
            raise HTTPException(status_code=409, detail="Game id already exists")
        game = Game(
            id=game_id,
            name=body.name,
            initial=body.initial or body.name[:1],
            genre=body.genre,
            color=body.color,
            interest_count=body.interest_count,
            image_url=body.image_url,
            is_active=body.is_active,
        )
        return game_to_out(self.games.add(game))

    def update_game(self, game_id: str, body: GameUpdate) -> GameOut:
        game = self.games.get(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(game, key, value)
        return game_to_out(self.games.save(game))

    def delete_game(self, game_id: str) -> None:
        game = self.games.get(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        self.games.delete(game)

    def list_contents(self, status_filter: str | None = None) -> list[ContentOut]:
        status_enum = ContentStatus(status_filter) if status_filter else None
        return [content_to_out(c, include_status=True) for c in self.contents.list_all(status_enum)]

    def create_content(
        self,
        body: ContentCreate,
        *,
        force_draft: bool = False,
        idempotency_key: str | None = None,
    ) -> ContentOut:
        if idempotency_key:
            existing = self.contents.get_by_idempotency_key(idempotency_key)
            if existing:
                return content_to_out(existing, include_status=True)

        if not self.games.get(body.game_id):
            raise HTTPException(status_code=400, detail="Unknown game_id")

        content_id = body.id or new_id("c")
        if self.contents.get(content_id):
            raise HTTPException(status_code=409, detail="Content id already exists")

        if force_draft:
            status_value = ContentStatus.draft
        else:
            # 생성 시 draft 또는 reviewed만 허용. published는 전이로만.
            if body.status == "published":
                status_value = ContentStatus.draft
                # 생성과 동시에 발행하려면 draft→reviewed→published
                content = self._build_content(content_id, body, ContentStatus.draft, idempotency_key)
                saved = self.contents.add(content)
                return self._apply_status_chain(saved.id, ["reviewed", "published"])
            status_value = ContentStatus(body.status)

        content = self._build_content(content_id, body, status_value, idempotency_key)
        if status_value == ContentStatus.published:
            content.published_at = datetime.now(timezone.utc)
        saved = self.contents.add(content)
        loaded = self.contents.get(saved.id)
        assert loaded is not None
        return content_to_out(loaded, include_status=True)

    def _build_content(
        self,
        content_id: str,
        body: ContentCreate,
        status_value: ContentStatus,
        idempotency_key: str | None,
    ) -> Content:
        return Content(
            id=content_id,
            game_id=body.game_id,
            kind=ContentKind(body.kind),
            status=status_value,
            title=body.title,
            summary_points_json=json.dumps(body.summary_points, ensure_ascii=False),
            official_url=body.official_url,
            image_url=body.image_url,
            place=body.place,
            reservation_url=body.reservation_url,
            starts_at=body.starts_at,
            ends_at=body.ends_at,
            idempotency_key=idempotency_key,
        )

    def _apply_status_chain(self, content_id: str, targets: list[str]) -> ContentOut:
        out: ContentOut | None = None
        for target in targets:
            out = self.update_content(content_id, ContentUpdate(status=target))  # type: ignore[arg-type]
        assert out is not None
        return out

    def update_content(self, content_id: str, body: ContentUpdate) -> ContentOut:
        content = self.contents.get(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        data = body.model_dump(exclude_unset=True)
        if "game_id" in data and data["game_id"] and not self.games.get(data["game_id"]):
            raise HTTPException(status_code=400, detail="Unknown game_id")

        if "summary_points" in data and data["summary_points"] is not None:
            content.summary_points_json = json.dumps(data.pop("summary_points"), ensure_ascii=False)
        if "kind" in data and data["kind"] is not None:
            content.kind = ContentKind(data.pop("kind"))

        if "status" in data and data["status"] is not None:
            previous = content.status.value
            target = data.pop("status")
            try:
                next_status = ContentStatusMachine.transition(previous, target)
            except InvalidTransitionError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            content.status = ContentStatus(next_status)
            if ContentStatusMachine.requires_published_at(previous, next_status):
                content.published_at = datetime.now(timezone.utc)

        for key, value in data.items():
            setattr(content, key, value)

        self.contents.save(content)
        loaded = self.contents.get(content_id)
        assert loaded is not None
        return content_to_out(loaded, include_status=True)

    def delete_content(self, content_id: str) -> None:
        content = self.contents.get(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        self.contents.delete(content)

    def list_announcements(self) -> list[AnnouncementOut]:
        return [announcement_to_out(a) for a in self.announcements.list_all()]

    def create_announcement(self, body: AnnouncementCreate) -> AnnouncementOut:
        item = Announcement(
            id=body.id or new_id("a"),
            title=body.title,
            body=body.body,
            is_published=body.is_published,
            published_at=datetime.now(timezone.utc),
        )
        return announcement_to_out(self.announcements.add(item))

    def delete_announcement(self, announcement_id: str) -> None:
        item = self.announcements.get(announcement_id)
        if not item:
            raise HTTPException(status_code=404, detail="Announcement not found")
        self.announcements.delete(item)

    def list_inquiries(self) -> list[InquiryOut]:
        return [inquiry_to_out(i) for i in self.inquiries.list_all()]

    def close_inquiry(self, inquiry_id: str) -> InquiryOut:
        item = self.inquiries.get(inquiry_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inquiry not found")
        item.status = InquiryStatus.closed
        return inquiry_to_out(self.inquiries.save(item))
