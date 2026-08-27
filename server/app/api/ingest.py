import hashlib

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, require_ingest_key
from app.schemas.common import (
    ContentCreate,
    IngestCheckIn,
    IngestCheckOut,
    IngestContentCreate,
    IngestContentOut,
    IngestJobOut,
    IngestRunComplete,
    IngestRunOut,
)
from app.repositories.content_repository import ContentRepository
from app.services.admin_service import AdminService
from app.services.ingest_service import IngestService
from app.services.summarize_service import run_post_ingest

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


def _scoped_key(source_id: str, key: str) -> str:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return f"src:{source_id[-24:]}:{digest}"


@router.post("/contents", response_model=IngestContentOut, status_code=201)
def ingest_content(
    body: IngestContentCreate,
    background: BackgroundTasks,
    _: None = Depends(require_ingest_key),
    db: Session = Depends(db_session),
) -> IngestContentOut:
    """자동화(RSS/API/HTML)용. 항상 draft. 동일 idempotency_key면 기존 행 반환.

    새로 생성된 draft는 백그라운드에서 LLM 요약 → (신뢰 소스면) 자동 발행 파이프라인을 탄다.
    """
    create = ContentCreate(
        game_id=body.game_id,
        kind=body.kind,
        title=body.title,
        summary_points=body.summary_points,
        official_url=body.official_url,
        image_url=body.image_url,
        image_source_url=body.image_source_url,
        image_rights_status=body.image_rights_status,
        place=body.place,
        reservation_url=body.reservation_url,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        status="draft",
    )
    idempotency_key = body.idempotency_key
    if body.source_id:
        IngestService(db).assert_source_exists(body.source_id)
        if idempotency_key:
            idempotency_key = _scoped_key(body.source_id, idempotency_key)
    existed = (
        ContentRepository(db).get_by_idempotency_key(idempotency_key)
        if idempotency_key
        else None
    )
    content = AdminService(db).create_content(
        create,
        force_draft=True,
        idempotency_key=idempotency_key,
        source_id=body.source_id,
        raw_text=body.raw_text,
        origin_published_at=body.origin_published_at,
        summary_status="pending",
    )
    created = existed is None
    if created:
        # Starlette 1.x executes BackgroundTasks before FastAPI's yield-based
        # dependency teardown.  Commit the draft first so the worker's
        # separate SessionLocal transaction can see it.  Without this explicit
        # boundary the worker can legitimately query no row, leave
        # summary_status=pending, and silently skip auto-publish.
        db.commit()
        background.add_task(run_post_ingest, content.id)
    return IngestContentOut(**content.model_dump(), created=created)


@router.post("/contents/check", response_model=IngestCheckOut)
def check_ingest_contents(
    body: IngestCheckIn,
    _: None = Depends(require_ingest_key),
    db: Session = Depends(db_session),
) -> IngestCheckOut:
    """이미 수집된 키 목록. collector가 새 글에만 상세 fetch·제출을 하도록 돕는다."""
    IngestService(db).assert_source_exists(body.source_id)
    repo = ContentRepository(db)
    scoped = {key: _scoped_key(body.source_id, key) for key in body.idempotency_keys}
    existing = repo.filter_existing_idempotency_keys(list(scoped.values()))
    return IngestCheckOut(existing=[key for key, value in scoped.items() if value in existing])


@router.post("/jobs/claim", response_model=IngestJobOut | None)
def claim_ingest_job(
    _: None = Depends(require_ingest_key),
    db: Session = Depends(db_session),
) -> IngestJobOut | None:
    return IngestService(db).claim_job()


@router.post("/jobs/{run_id}/complete", response_model=IngestRunOut)
def complete_ingest_job(
    run_id: str,
    body: IngestRunComplete,
    _: None = Depends(require_ingest_key),
    db: Session = Depends(db_session),
) -> IngestRunOut:
    return IngestService(db).complete_run(run_id, body)
