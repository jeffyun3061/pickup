import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.api import admin, ingest, installations, public
from app.config import get_settings
from app.db import Base, engine
from app.db_migrate import ensure_schema

logger = logging.getLogger(__name__)

# Railway에서 PostgreSQL이 API보다 수 초 늦게 준비되는 경우를 흡수한다.
# 별도 health worker를 두지 않고, 시작 시에만 제한된 횟수로 재시도한다.
_DB_INIT_DELAYS_SECONDS = (0, 1, 2, 4)


def _initialize_database() -> None:
    """기본 스키마와 경량 마이그레이션을 연결 일시 오류에 안전하게 초기화한다."""
    last_error: SQLAlchemyError | None = None
    total_attempts = len(_DB_INIT_DELAYS_SECONDS)
    for attempt, delay in enumerate(_DB_INIT_DELAYS_SECONDS, start=1):
        if delay:
            time.sleep(delay)
        try:
            Base.metadata.create_all(bind=engine)
            ensure_schema(engine)
            return
        except SQLAlchemyError as exc:
            last_error = exc
            engine.dispose()
            if attempt == total_attempts:
                break
            logger.warning(
                "database initialization attempt %d/%d failed; retrying",
                attempt,
                total_attempts,
            )
    # 원래 DB 예외의 traceback은 유지하되, 연결 문자열 자체는 로그에 남기지 않는다.
    assert last_error is not None
    raise last_error


async def _scheduler_loop(interval_seconds: int) -> None:
    from app.services.scheduler_service import run_scheduler_cycle

    while True:
        await asyncio.sleep(interval_seconds)
        await asyncio.to_thread(run_scheduler_cycle)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 동기 SQLAlchemy 초기화가 이벤트 루프를 막지 않도록 시작 스레드에서 수행한다.
    await asyncio.to_thread(_initialize_database)

    settings = get_settings()
    task: asyncio.Task | None = None
    if settings.scheduler_enabled:
        task = asyncio.create_task(_scheduler_loop(settings.scheduler_interval_seconds))
    try:
        yield
    finally:
        if task:
            task.cancel()


def create_app() -> FastAPI:
    settings = get_settings()
    origins = settings.cors_origin_list
    # credentials=True 와 "*" 조합 금지 — allowlist만 사용
    if not origins:
        origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # 운영에서는 관리자·수집 API의 스키마를 공개하지 않는다. 개발 환경의
    # Swagger는 그대로 유지해 로컬 계약 확인과 수동 테스트에 사용한다.
    docs_url = None if settings.is_production else "/docs"
    redoc_url = None if settings.is_production else "/redoc"
    openapi_url = None if settings.is_production else "/openapi.json"
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        """브라우저·스토어 심사에서 기대하는 최소 응답 보안 헤더."""
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; "
                "media-src 'self' https:; object-src 'none'; base-uri 'self'; "
                "form-action 'self'; frame-ancestors 'none'",
            )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Authorization",
            "Content-Type",
            "X-Ingest-Key",
            "X-Installation-Id",
            "X-Installation-Secret",
        ],
    )
    app.include_router(public.router)
    app.include_router(public.root_router)
    app.include_router(admin.router)
    app.include_router(ingest.router)
    app.include_router(installations.router)

    # 업로드 이미지 정적 서빙 (관리자가 올린 게임/소식 이미지)
    media_path = Path(settings.media_dir)
    media_path.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(media_path)), name="media")

    # 관리자 웹 same-origin 서빙 — 빌드 산출물이 있으면 /admin 으로 제공 (CORS 불필요)
    admin_dist = Path(settings.admin_dist_dir)
    if admin_dist.is_dir():
        app.mount("/admin", StaticFiles(directory=str(admin_dist), html=True), name="admin-web")

    return app


app = create_app()
