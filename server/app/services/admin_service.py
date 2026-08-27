from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.content_status import ContentStatusMachine, InvalidTransitionError
from app.domain.ids import new_id
from app.models.entities import (
    Announcement,
    AuditLog,
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
    ContentFromUrlIn,
    ContentOut,
    ContentUpdate,
    GameCreate,
    GameOut,
    GameUpdate,
    InquiryOut,
    LoginIn,
    PushDispatchOut,
    TokenOut,
)
from app.security import create_access_token, verify_password
from app.services.mappers import (
    announcement_to_out,
    content_to_out,
    game_to_out,
    inquiry_to_out,
)
from app.services.push_service import PushService


def _validate_http_url(value: str | None, field_name: str, *, required: bool = False) -> None:
    value = (value or "").strip()
    if not value:
        if required:
            raise HTTPException(status_code=400, detail=f"{field_name} is required")
        return
    parsed = urlparse(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise HTTPException(status_code=400, detail=f"{field_name} must be an HTTP(S) URL")


def _validate_image_url(value: str | None) -> None:
    """공용 HTTP(S) 주소 또는 API가 제공한 로컬 media 경로만 허용한다."""
    value = (value or "").strip()
    if not value:
        return
    if value.startswith("/media/") and "\\" not in value and ".." not in value:
        return
    _validate_http_url(value, "image_url")


def _validate_image_rights(
    image_url: str | None,
    source_url: str | None,
    rights_status: str,
) -> None:
    _validate_image_url(image_url)
    if source_url:
        _validate_http_url(source_url, "image_source_url")
    if rights_status == "unverified":
        return
    if not image_url:
        raise HTTPException(status_code=400, detail="Approved image requires image_url")
    if rights_status in {"official", "licensed"} and not source_url:
        raise HTTPException(
            status_code=400,
            detail="Official or licensed image requires image_source_url",
        )


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.games = GameRepository(db)
        self.contents = ContentRepository(db)
        self.announcements = AnnouncementRepository(db)
        self.inquiries = InquiryRepository(db)
        self.push = PushService(db)
        self.settings = get_settings()

    def _audit(
        self,
        action: str,
        entity: str,
        entity_id: str,
        detail: str = "",
        *,
        actor: str = "admin",
    ) -> None:
        self.db.add(
            AuditLog(
                id=new_id("al"),
                actor=actor,
                action=action,
                entity=entity,
                entity_id=entity_id,
                detail=detail[:500],
            )
        )

    def login(self, body: LoginIn) -> TokenOut:
        if body.username != self.settings.admin_username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(body.password, self.settings.admin_password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        # 성공한 관리자 로그인도 운영 감사 로그에 남긴다. 비밀번호·토큰·IP는 저장하지 않는다.
        self._audit("관리자 로그인", "admin", body.username, actor=body.username)
        return TokenOut(access_token=create_access_token(body.username))

    def list_games(self) -> list[GameOut]:
        return [game_to_out(g, count) for g, count in self.games.list_all_with_interest_counts()]

    def create_game(self, body: GameCreate) -> GameOut:
        _validate_image_rights(
            body.image_url, body.image_source_url, body.image_rights_status
        )
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
            image_source_url=body.image_source_url,
            image_rights_status=body.image_rights_status,
            fallback_image_key=body.fallback_image_key,
            is_active=body.is_active,
        )
        saved = self.games.add(game)
        self._audit("게임 등록", "game", saved.id, saved.name)
        return game_to_out(saved)

    def update_game(self, game_id: str, body: GameUpdate) -> GameOut:
        game = self.games.get(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(game, key, value)
        _validate_image_rights(
            game.image_url, game.image_source_url, game.image_rights_status
        )
        return game_to_out(self.games.save(game))

    def delete_game(self, game_id: str) -> None:
        game = self.games.get(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        if self.games.count_contents(game_id) > 0:
            raise HTTPException(
                status_code=409,
                detail="Game has contents; delete or reassign contents first",
            )
        self._audit("게임 삭제", "game", game.id, game.name)
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
        source_id: str | None = None,
        raw_text: str | None = None,
        origin_published_at: datetime | None = None,
        summary_status: str = "none",
    ) -> ContentOut:
        _validate_image_rights(
            body.image_url, body.image_source_url, body.image_rights_status
        )
        _validate_http_url(body.official_url, "official_url")
        _validate_http_url(body.reservation_url, "reservation_url")
        if idempotency_key:
            existing = self.contents.get_by_idempotency_key(idempotency_key)
            if existing:
                return content_to_out(existing, include_status=True)

        if not self.games.get(body.game_id):
            raise HTTPException(status_code=400, detail="Unknown game_id")

        content_id = body.id or new_id("c")
        if self.contents.get(content_id):
            raise HTTPException(status_code=409, detail="Content id already exists")

        ingest_fields = {
            "source_id": source_id,
            "raw_text": raw_text,
            "origin_published_at": origin_published_at,
            "summary_status": summary_status,
        }

        if force_draft:
            status_value = ContentStatus.draft
        elif body.status == "published":
            # 한 트랜잭션 안에서 draft→reviewed→published + outbox
            content = self._build_content(
                content_id, body, ContentStatus.draft, idempotency_key, **ingest_fields
            )
            self.contents.add(content)
            return self._apply_status_chain(content.id, ["reviewed", "published"])
        else:
            status_value = ContentStatus(body.status)

        content = self._build_content(
            content_id, body, status_value, idempotency_key, **ingest_fields
        )
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
        *,
        source_id: str | None = None,
        raw_text: str | None = None,
        origin_published_at: datetime | None = None,
        summary_status: str = "none",
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
            image_source_url=body.image_source_url,
            image_rights_status=body.image_rights_status,
            place=body.place,
            reservation_url=body.reservation_url,
            starts_at=body.starts_at,
            ends_at=body.ends_at,
            idempotency_key=idempotency_key,
            source_id=source_id,
            raw_text=raw_text,
            origin_published_at=origin_published_at,
            summary_status=summary_status,
        )

    # 수집 콘텐츠 신뢰도 추적: 이 필드들이 바뀌면 '수정 후 발행'으로 집계한다
    _BODY_FIELDS = frozenset(
        {
            "game_id",
            "kind",
            "title",
            "summary_points",
            "official_url",
            "image_url",
            "place",
            "reservation_url",
            "starts_at",
            "ends_at",
        }
    )

    def _apply_status_chain(
        self, content_id: str, targets: list[str], *, actor: str = "admin"
    ) -> ContentOut:
        out: ContentOut | None = None
        for target in targets:
            out = self.update_content(
                content_id, ContentUpdate(status=target), actor=actor  # type: ignore[arg-type]
            )
        assert out is not None
        return out

    def update_content(
        self, content_id: str, body: ContentUpdate, *, actor: str = "admin"
    ) -> ContentOut:
        content = self.contents.get(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        data = body.model_dump(exclude_unset=True)
        if "game_id" in data and data["game_id"] and not self.games.get(data["game_id"]):
            raise HTTPException(status_code=400, detail="Unknown game_id")

        body_edited = any(key in data for key in self._BODY_FIELDS)

        if "summary_points" in data and data["summary_points"] is not None:
            content.summary_points_json = json.dumps(data.pop("summary_points"), ensure_ascii=False)
        if "kind" in data and data["kind"] is not None:
            content.kind = ContentKind(data.pop("kind"))

        became_published = False
        retracted = False
        if "status" in data and data["status"] is not None:
            previous = content.status.value
            target = data.pop("status")
            try:
                next_status = ContentStatusMachine.transition(previous, target)
            except InvalidTransitionError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            content.status = ContentStatus(next_status)
            if ContentStatusMachine.requires_published_at(previous, next_status):
                if content.published_at is None:
                    content.published_at = datetime.now(timezone.utc)
                became_published = True
            if previous == "published" and next_status != "published":
                retracted = True

        for key, value in data.items():
            setattr(content, key, value)

        # 기간형 콘텐츠가 거꾸로 저장되면 홈의 종료 D-day와 알림 대상이
        # 모두 잘못 계산된다. 초안도 같은 규칙으로 막아 운영 데이터가
        # 나중에 복구하기 어려운 상태로 쌓이지 않게 한다.
        if content.starts_at and content.ends_at and content.ends_at < content.starts_at:
            raise HTTPException(
                status_code=400,
                detail="ends_at must be on or after starts_at",
            )

        if body_edited and actor == "admin" and content.source_id:
            content.edited_after_ingest = True

        _validate_image_rights(
            content.image_url,
            content.image_source_url,
            content.image_rights_status,
        )

        _validate_http_url(
            content.official_url,
            "official_url",
            # 공개 상태인 콘텐츠는 이후 제목/요약만 수정하더라도 원문 링크를
            # 잃지 않아야 한다. 그렇지 않으면 앱의 "공식 원문 보기"가
            # 빈 URL을 열게 되어 신뢰·권리 추적이 끊긴다.
            required=became_published or content.status == ContentStatus.published,
        )
        _validate_http_url(content.reservation_url, "reservation_url")

        if became_published:
            content.scheduled_publish_at = None
            if actor in {"auto"}:
                content.auto_published = True
            self._record_publish_trust(content, actor)
            self._audit("발행", "content", content.id, content.title, actor=actor)
        if retracted:
            self._audit("발행 회수", "content", content.id, content.title, actor=actor)
            self._demote_source_if_auto_published(content)

        self.contents.save(content)
        if became_published:
            self.push.enqueue_content_published(content)

        loaded = self.contents.get(content_id)
        assert loaded is not None
        return content_to_out(loaded, include_status=True)

    def _record_publish_trust(self, content: Content, actor: str) -> None:
        """관리자가 수집 콘텐츠를 발행하면 소스의 무수정/수정 승인 카운터를 올린다."""
        if actor != "admin" or not content.source_id:
            return
        from app.models.entities import IngestSource

        source = self.db.get(IngestSource, content.source_id)
        if source is None:
            return
        if content.edited_after_ingest:
            source.stat_edited += 1
        else:
            source.stat_approved += 1

    def _demote_source_if_auto_published(self, content: Content) -> None:
        """자동 발행된 소식이 회수되면 해당 소스를 검수 모드로 강등한다."""
        if not content.auto_published or not content.source_id:
            return
        from app.models.entities import IngestSource

        source = self.db.get(IngestSource, content.source_id)
        content.auto_published = False
        if source is None:
            return
        source.stat_retracted += 1
        if source.auto_publish:
            source.auto_publish = False
            self._audit(
                "자동 발행 강등",
                "ingest_source",
                source.id,
                f"자동 발행 소식 회수로 검수 모드 전환: {content.title}",
                actor="system",
            )

    def create_content_from_url(self, body: ContentFromUrlIn) -> ContentOut:
        """URL 빠른 등록: 본문 추출 + 동기 AI 요약까지 채운 초안을 만든다."""
        from app.services.source_preview_service import extract_page

        if not self.games.get(body.game_id):
            raise HTTPException(status_code=400, detail="Unknown game_id")

        title, text = extract_page(body.url)
        created = self.create_content(
            ContentCreate(
                game_id=body.game_id,
                kind=body.kind,
                title=title,
                summary_points=[],
                official_url=body.url,
                status="draft",
            ),
            raw_text=text or None,
            summary_status="pending" if text else "none",
        )
        return self._summarize_now(created.id)

    def resummarize_content(self, content_id: str) -> ContentOut:
        return self._summarize_now(content_id)

    def _summarize_now(self, content_id: str) -> ContentOut:
        from app.services.summarize_service import SummarizeService

        content = self.contents.get(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        SummarizeService(self.db).summarize(content)
        self.contents.save(content)
        loaded = self.contents.get(content_id)
        assert loaded is not None
        return content_to_out(loaded, include_status=True)

    def delete_content(self, content_id: str) -> None:
        content = self.contents.get(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        self._audit("소식 삭제", "content", content.id, content.title)
        self.contents.delete(content)

    def list_announcements(self) -> list[AnnouncementOut]:
        return [announcement_to_out(a) for a in self.announcements.list_all()]

    def create_announcement(self, body: AnnouncementCreate) -> AnnouncementOut:
        now = datetime.now(timezone.utc) if body.is_published else None
        item = Announcement(
            id=body.id or new_id("a"),
            title=body.title,
            body=body.body,
            is_published=body.is_published,
            published_at=now,
        )
        saved = self.announcements.add(item)
        if saved.is_published:
            self.push.enqueue_announcement_published(saved)
        self._audit("공지 등록", "announcement", saved.id, saved.title)
        return announcement_to_out(saved)

    def delete_announcement(self, announcement_id: str) -> None:
        item = self.announcements.get(announcement_id)
        if not item:
            raise HTTPException(status_code=404, detail="Announcement not found")
        self._audit("공지 삭제", "announcement", item.id, item.title)
        self.announcements.delete(item)

    def list_inquiries(self) -> list[InquiryOut]:
        return [inquiry_to_out(i) for i in self.inquiries.list_all()]

    def close_inquiry(self, inquiry_id: str) -> InquiryOut:
        item = self.inquiries.get(inquiry_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inquiry not found")
        item.status = InquiryStatus.closed
        self._audit("문의 처리 완료", "inquiry", item.id, item.category)
        return inquiry_to_out(self.inquiries.save(item))

    def dispatch_push(self, limit: int = 100, *, force: bool = False) -> PushDispatchOut:
        return self.push.dispatch_pending(limit=limit, ignore_schedule=force)

    def push_stats(self) -> "PushStatsOut":
        from sqlalchemy import func as sa_func, select

        from app.models.entities import PushOutbox, PushOutboxStatus
        from app.schemas.common import PushStatsOut

        def count(status: PushOutboxStatus) -> int:
            stmt = select(sa_func.count()).select_from(PushOutbox).where(PushOutbox.status == status)
            return int(self.db.scalar(stmt) or 0)

        last_sent_at = self.db.scalar(
            select(sa_func.max(PushOutbox.created_at)).where(
                PushOutbox.status == PushOutboxStatus.sent
            )
        )
        return PushStatsOut(
            pending=count(PushOutboxStatus.pending),
            sent=count(PushOutboxStatus.sent),
            failed=count(PushOutboxStatus.failed),
            last_sent_at=last_sent_at,
        )

    def user_stats(self) -> "UserStatsOut":
        from sqlalchemy import func, select

        from app.models.entities import DeviceToken, Installation, InstallationGame
        from app.schemas.common import TopGamePick, UserStatsOut

        installations = list(
            self.db.scalars(select(Installation).where(Installation.revoked_at.is_(None)))
        )
        token_owner_ids = set(self.db.scalars(select(DeviceToken.installation_id)))

        news = ending = notices = 0
        for item in installations:
            if item.notify_selected_game_news:
                news += 1
            if item.notify_event_ending:
                ending += 1
            if item.notify_service_notices:
                notices += 1
        pick_rows = self.db.execute(
            select(
                InstallationGame.game_id,
                func.count(func.distinct(InstallationGame.installation_id)).label("pick_count"),
            )
            .join(Installation, Installation.id == InstallationGame.installation_id)
            .where(Installation.revoked_at.is_(None))
            .group_by(InstallationGame.game_id)
            .order_by(func.count(func.distinct(InstallationGame.installation_id)).desc())
            .limit(5)
        ).all()
        top_games = []
        for game_id, count in pick_rows:
            game = self.games.get(game_id)
            top_games.append(
                TopGamePick(
                    game_id=game_id,
                    game_name=game.name if game else game_id,
                    pick_count=count,
                )
            )
        return UserStatsOut(
            installations=len(installations),
            with_device_token=len(
                [i for i in installations if i.id in token_owner_ids]
            ),
            notify_selected_game_news=news,
            notify_event_ending=ending,
            notify_service_notices=notices,
            top_games=top_games,
        )

    def list_audit_logs(self, limit: int = 50) -> list["AuditLogOut"]:
        from sqlalchemy import select

        from app.schemas.common import AuditLogOut

        stmt = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)
        return [AuditLogOut.model_validate(row) for row in self.db.scalars(stmt)]
