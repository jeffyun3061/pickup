from __future__ import annotations

import sys
from pathlib import Path

import pytest
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """앱 모듈을 env 설정 후 깨끗이 로드한 TestClient."""
    db_path = tmp_path / "test.db"
    password = "test-admin-pass"
    pwd_hash = CryptContext(schemes=["bcrypt"]).hash(password)

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", pwd_hash)
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("INGEST_API_KEY", "test-ingest-key")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")

    # 이전 import 잔여물 제거
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from app.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    assert "test.db" in settings.database_url

    from app.db import Base, get_db
    from app.main import create_app

    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c, password

    get_settings.cache_clear()
