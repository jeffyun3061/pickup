from __future__ import annotations

import sys
from pathlib import Path

import pytest
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """앱 모듈을 env 설정 후 깨끗이 로드한 TestClient.

    테스트도 PostgreSQL만 사용한다. TEST_DATABASE_URL을 주면 해당 DB를 사용한다:
      TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5433/gamepickup_test
    """
    import os

    password = "test-admin-pass"
    pwd_hash = CryptContext(schemes=["bcrypt"]).hash(password)

    test_db_url = os.environ.get("TEST_DATABASE_URL", "").strip()
    database_url = test_db_url or "postgresql+psycopg://gamepickup:gamepickup_dev@127.0.0.1:5432/gamepickup_test"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", pwd_hash)
    monkeypatch.setenv("JWT_SECRET", "test-secret-for-local-suite-32-bytes")
    monkeypatch.setenv("INGEST_API_KEY", "test-ingest-key")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")
    monkeypatch.setenv("ENV", "development")
    # 조용시간 비활성 (start == end) — 발송 시점 검증이 시간대에 좌우되지 않게
    monkeypatch.setenv("QUIET_HOURS_START", "0")
    monkeypatch.setenv("QUIET_HOURS_END", "0")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setenv("EXPO_PUSH_ENABLED", "false")
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path / "media"))
    monkeypatch.setenv("ADMIN_DIST_DIR", str(tmp_path / "no-admin-dist"))

    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from app.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    assert settings.database_url == database_url

    from app.db import Base, get_db
    from app import db as app_db
    from app.main import create_app

    engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=1800)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    # PG 테스트 DB는 테스트 간 유지되므로 매 테스트마다 스키마를 초기화한다.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient

    try:
        with TestClient(app) as c:
            yield c, password
    finally:
        # PostgreSQL test runs create a fresh engine per fixture.  Explicitly
        # return every pooled connection (including the app lifespan engine),
        # otherwise the embedded server reaches max_connections halfway through
        # the suite and reports a misleading application failure.
        engine.dispose()
        app_db.engine.dispose()
        get_settings.cache_clear()
