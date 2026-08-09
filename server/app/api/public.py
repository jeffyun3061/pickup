from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.common import (
    AnnouncementOut,
    ContentOut,
    GameOut,
    InquiryCreate,
    InquiryOut,
    RankingOut,
)
from app.services.catalog_service import CatalogService
from app.services.inquiry_service import InquiryService

router = APIRouter(prefix="/api/v1", tags=["public"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/games", response_model=list[GameOut])
def list_games(db: Session = Depends(db_session)) -> list[GameOut]:
    return CatalogService(db).list_games()


@router.get("/contents", response_model=list[ContentOut])
def list_contents(
    scope: str = Query(default="all", pattern="^(all|mine)$"),
    game_ids: str = Query(default="", description="comma-separated ids for scope=mine"),
    db: Session = Depends(db_session),
) -> list[ContentOut]:
    ids = [x.strip() for x in game_ids.split(",") if x.strip()]
    return CatalogService(db).list_contents(scope, ids)


@router.get("/rankings", response_model=list[RankingOut])
def list_rankings(db: Session = Depends(db_session)) -> list[RankingOut]:
    return CatalogService(db).list_rankings()


@router.get("/announcements", response_model=list[AnnouncementOut])
def list_announcements(db: Session = Depends(db_session)) -> list[AnnouncementOut]:
    return CatalogService(db).list_announcements()


@router.post("/inquiries", response_model=InquiryOut, status_code=201)
def create_inquiry(body: InquiryCreate, db: Session = Depends(db_session)) -> InquiryOut:
    return InquiryService(db).create(body)
