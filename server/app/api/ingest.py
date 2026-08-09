from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, require_ingest_key
from app.schemas.common import ContentCreate, ContentOut, IngestContentCreate
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


@router.post("/contents", response_model=ContentOut, status_code=201)
def ingest_content(
    body: IngestContentCreate,
    _: None = Depends(require_ingest_key),
    db: Session = Depends(db_session),
) -> ContentOut:
    """자동화(RSS/AI)용. 항상 draft. 동일 idempotency_key면 기존 행 반환."""
    create = ContentCreate(
        game_id=body.game_id,
        kind=body.kind,
        title=body.title,
        summary_points=body.summary_points,
        official_url=body.official_url,
        image_url=body.image_url,
        place=body.place,
        reservation_url=body.reservation_url,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        status="draft",
    )
    return AdminService(db).create_content(
        create,
        force_draft=True,
        idempotency_key=body.idempotency_key,
    )
