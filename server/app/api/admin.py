from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import db_session, require_admin
from app.domain.login_guard import login_guard
from app.schemas.common import (
    AnnouncementCreate,
    AnnouncementOut,
    AuditLogOut,
    ContentCreate,
    ContentFromUrlIn,
    ContentOut,
    ContentUpdate,
    GameCreate,
    GameOut,
    GameUpdate,
    InquiryOut,
    IngestRunOut,
    IngestSourceCreate,
    IngestSourceOut,
    IngestSourceUpdate,
    LoginIn,
    PushDispatchOut,
    PushStatsOut,
    SourcePreviewIn,
    SourcePreviewOut,
    TokenOut,
    UserStatsOut,
)
from app.services.admin_service import AdminService
from app.services.ingest_service import IngestService
from app.services.source_preview_service import preview_source

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(db_session)) -> TokenOut:
    client_key = request.client.host if request.client else "unknown"
    retry_after = login_guard.retry_after(client_key)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="로그인 시도가 너무 많습니다. 잠시 후 다시 시도하세요.",
            headers={"Retry-After": str(retry_after)},
        )
    try:
        token = AdminService(db).login(body)
    except HTTPException as exc:
        if exc.status_code == 401:
            login_guard.record_failure(client_key)
        raise
    login_guard.reset(client_key)
    return token


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


@router.post("/contents/from-url", response_model=ContentOut, status_code=201)
def admin_create_content_from_url(
    body: ContentFromUrlIn,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> ContentOut:
    """URL 빠른 등록: 본문 추출 + AI 요약까지 채운 초안 생성."""
    return AdminService(db).create_content_from_url(body)


@router.post("/contents/{content_id}/summarize", response_model=ContentOut)
def admin_resummarize_content(
    content_id: str,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> ContentOut:
    """AI 요약 재실행 (동기)."""
    return AdminService(db).resummarize_content(content_id)


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


@router.post("/push/dispatch", response_model=PushDispatchOut)
def admin_dispatch_push(
    limit: int = Query(default=100, ge=1, le=500),
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> PushDispatchOut:
    """outbox 발송 (EXPO_PUSH_ENABLED면 실발송, 아니면 스텁)."""
    return AdminService(db).dispatch_push(limit=limit)


@router.get("/push/stats", response_model=PushStatsOut)
def admin_push_stats(
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> PushStatsOut:
    return AdminService(db).push_stats()


@router.get("/stats/users", response_model=UserStatsOut)
def admin_user_stats(
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> UserStatsOut:
    return AdminService(db).user_stats()


@router.get("/audit-logs", response_model=list[AuditLogOut])
def admin_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> list[AuditLogOut]:
    return AdminService(db).list_audit_logs(limit=limit)


# 게임/소식 이미지 업로드 — 볼륨(media_dir)에 저장하고 /media 로 서빙
_UPLOAD_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
_UPLOAD_MAX_BYTES = 5 * 1024 * 1024
_UPLOAD_CHUNK_BYTES = 64 * 1024


def _matches_image_signature(data: bytes, content_type: str) -> bool:
    """MIME 헤더 위장을 막기 위한 최소 파일 시그니처 검사."""
    signatures = {
        "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/jpeg": data.startswith(b"\xff\xd8\xff"),
        "image/gif": data.startswith((b"GIF87a", b"GIF89a")),
        "image/webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
    }
    return signatures.get(content_type, False)


@router.post("/uploads", status_code=201)
async def admin_upload_image(
    request: Request,
    file: UploadFile,
    _: str = Depends(require_admin),
) -> dict[str, str]:
    from pathlib import Path

    from app.config import get_settings
    from app.domain.ids import new_id

    ext = _UPLOAD_TYPES.get(file.content_type or "")
    if not ext:
        raise HTTPException(status_code=400, detail="PNG/JPEG/WebP/GIF 이미지만 업로드할 수 있습니다")

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_UPLOAD_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > _UPLOAD_MAX_BYTES:
            raise HTTPException(status_code=413, detail="이미지는 5MB 이하만 업로드할 수 있습니다")
        chunks.append(chunk)
    data = b"".join(chunks)
    if not _matches_image_signature(data, file.content_type or ""):
        raise HTTPException(status_code=400, detail="파일 내용이 이미지 형식과 일치하지 않습니다")

    media_dir = Path(get_settings().media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    name = f"{new_id('img')}{ext}"
    (media_dir / name).write_bytes(data)

    base = str(request.base_url).rstrip("/")
    return {"url": f"{base}/media/{name}", "path": f"/media/{name}"}


@router.get("/ingest-sources", response_model=list[IngestSourceOut])
def admin_list_ingest_sources(
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> list[IngestSourceOut]:
    return IngestService(db).list_sources()


@router.post("/ingest-sources", response_model=IngestSourceOut, status_code=201)
def admin_create_ingest_source(
    body: IngestSourceCreate,
    admin_subject: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> IngestSourceOut:
    return IngestService(db).create_source(body, actor=admin_subject)


@router.patch("/ingest-sources/{source_id}", response_model=IngestSourceOut)
def admin_update_ingest_source(
    source_id: str,
    body: IngestSourceUpdate,
    admin_subject: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> IngestSourceOut:
    return IngestService(db).update_source(source_id, body, actor=admin_subject)


@router.delete("/ingest-sources/{source_id}", status_code=204)
def admin_delete_ingest_source(
    source_id: str,
    admin_subject: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> None:
    IngestService(db).delete_source(source_id, actor=admin_subject)


@router.post("/ingest-sources/dry-run", response_model=SourcePreviewOut)
def admin_dry_run_ingest_source(
    body: SourcePreviewIn,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> SourcePreviewOut:
    """저장 전 소스 설정 검증 — 서버가 직접 fetch·파싱해 미리보기 반환."""
    items, warning = preview_source(
        body.source_type, body.endpoint_url, body.config, body.secret_env_name
    )
    return SourcePreviewOut(items=items, warning=warning)


@router.post("/ingest-sources/{source_id}/runs", response_model=IngestRunOut, status_code=202)
def admin_enqueue_ingest_run(
    source_id: str,
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> IngestRunOut:
    return IngestService(db).enqueue_run(source_id)


@router.get("/ingest-runs", response_model=list[IngestRunOut])
def admin_list_ingest_runs(
    limit: int = Query(default=50, ge=1, le=200),
    _: str = Depends(require_admin),
    db: Session = Depends(db_session),
) -> list[IngestRunOut]:
    return IngestService(db).list_runs(limit)
