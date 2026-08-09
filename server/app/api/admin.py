from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session, require_admin
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
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(db_session)) -> TokenOut:
    return AdminService(db).login(body)


@router.get("/games", response_model=list[GameOut])
def admin_list_games(
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> list[GameOut]:
    return AdminService(db).list_games()


@router.post("/games", response_model=GameOut, status_code=201)
def admin_create_game(
    body: GameCreate,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> GameOut:
    return AdminService(db).create_game(body)


@router.patch("/games/{game_id}", response_model=GameOut)
def admin_update_game(
    game_id: str,
    body: GameUpdate,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> GameOut:
    return AdminService(db).update_game(game_id, body)


@router.delete("/games/{game_id}", status_code=204)
def admin_delete_game(
    game_id: str,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> None:
    AdminService(db).delete_game(game_id)


@router.get("/contents", response_model=list[ContentOut])
def admin_list_contents(
    status: str | None = Query(default=None, pattern="^(draft|reviewed|published)$"),
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> list[ContentOut]:
    return AdminService(db).list_contents(status)


@router.post("/contents", response_model=ContentOut, status_code=201)
def admin_create_content(
    body: ContentCreate,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> ContentOut:
    return AdminService(db).create_content(body)


@router.patch("/contents/{content_id}", response_model=ContentOut)
def admin_update_content(
    content_id: str,
    body: ContentUpdate,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> ContentOut:
    return AdminService(db).update_content(content_id, body)


@router.delete("/contents/{content_id}", status_code=204)
def admin_delete_content(
    content_id: str,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> None:
    AdminService(db).delete_content(content_id)


@router.get("/announcements", response_model=list[AnnouncementOut])
def admin_list_announcements(
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> list[AnnouncementOut]:
    return AdminService(db).list_announcements()


@router.post("/announcements", response_model=AnnouncementOut, status_code=201)
def admin_create_announcement(
    body: AnnouncementCreate,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> AnnouncementOut:
    return AdminService(db).create_announcement(body)


@router.delete("/announcements/{announcement_id}", status_code=204)
def admin_delete_announcement(
    announcement_id: str,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> None:
    AdminService(db).delete_announcement(announcement_id)


@router.get("/inquiries", response_model=list[InquiryOut])
def admin_list_inquiries(
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> list[InquiryOut]:
    return AdminService(db).list_inquiries()


@router.post("/inquiries/{inquiry_id}/close", response_model=InquiryOut)
def admin_close_inquiry(
    inquiry_id: str,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> InquiryOut:
    return AdminService(db).close_inquiry(inquiry_id)
