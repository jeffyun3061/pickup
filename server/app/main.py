from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, ingest, installations, public
from app.config import get_settings
from app.db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    origins = settings.cors_origin_list
    # credentials=True 와 "*" 조합 금지 — allowlist만 사용
    if not origins:
        origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(public.router)
    app.include_router(admin.router)
    app.include_router(ingest.router)
    app.include_router(installations.router)
    return app


app = create_app()
