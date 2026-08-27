"""프로덕션 준비 기능 검증 — 이미지 업로드 · /privacy · 문의 rate limit."""

from __future__ import annotations

import io
from datetime import datetime, timezone

import pytest


def _admin_headers(client):
    c, password = client
    token = c.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": password},
    ).json()["access_token"]
    return c, {"Authorization": f"Bearer {token}"}


# 1x1 투명 PNG
_PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d4944415478da63fcffff3f0300050201f34d85640000000049454e44ae426082"
)


def test_upload_image_saves_and_serves(client):
    c, headers = _admin_headers(client)
    res = c.post(
        "/api/v1/admin/uploads",
        headers=headers,
        files={"file": ("cover.png", io.BytesIO(_PNG_BYTES), "image/png")},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["path"].startswith("/media/img_")
    assert body["url"].endswith(body["path"])

    served = c.get(body["path"])
    assert served.status_code == 200
    assert served.content == _PNG_BYTES


def test_upload_rejects_non_image(client):
    c, headers = _admin_headers(client)
    res = c.post(
        "/api/v1/admin/uploads",
        headers=headers,
        files={"file": ("evil.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert res.status_code == 400


def test_upload_rejects_mime_type_spoof(client):
    c, headers = _admin_headers(client)
    res = c.post(
        "/api/v1/admin/uploads",
        headers=headers,
        files={"file": ("fake.png", io.BytesIO(b"not-a-png"), "image/png")},
    )
    assert res.status_code == 400


def test_upload_requires_admin(client):
    c, _ = client
    res = c.post(
        "/api/v1/admin/uploads",
        files={"file": ("cover.png", io.BytesIO(_PNG_BYTES), "image/png")},
    )
    assert res.status_code in {401, 403}


def test_config_rejects_non_postgresql_database(client):
    from app.config import Settings

    with pytest.raises(ValueError, match="PostgreSQL"):
        Settings(
            env="production",
            database_url="sqlite:///./unsafe.db",
            jwt_secret="rotated-secret-for-production-tests-32",
            admin_password_hash="bcrypt-hash",
            ingest_api_key="ingest-key-for-production-tests-32",
            cors_origins="https://admin.gamepickup.dev",
            expo_push_enabled=True,
            scheduler_enabled=True,
        )

    with pytest.raises(ValueError, match="must not contain"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://user:pass@db/gamepickup",
            jwt_secret="rotated-secret-for-production-tests-32",
            admin_password_hash="bcrypt-hash",
            ingest_api_key="ingest-key-for-production-tests-32",
            cors_origins="*",
            expo_push_enabled=True,
            scheduler_enabled=True,
        )

    with pytest.raises(ValueError, match="PRIVACY_CONTACT_EMAIL"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://user:pass@db/gamepickup",
            jwt_secret="rotated-secret-for-production-tests-32",
            admin_password_hash="bcrypt-hash",
            ingest_api_key="ingest-key-for-production-tests-32",
            cors_origins="https://admin.gamepickup.dev",
            expo_push_enabled=True,
            scheduler_enabled=True,
        )

    with pytest.raises(ValueError, match="32 bytes"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://user:pass@db/gamepickup",
            jwt_secret="too-short",
            admin_password_hash="bcrypt-hash",
            ingest_api_key="ingest-key-for-production-tests-32",
            cors_origins="https://admin.gamepickup.dev",
            expo_push_enabled=True,
            scheduler_enabled=True,
            privacy_contact_email="owner@example.com",
        )

    with pytest.raises(ValueError, match="INGEST_API_KEY.*32 bytes"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://user:pass@db/gamepickup",
            jwt_secret="rotated-secret-for-production-tests-32",
            admin_password_hash="bcrypt-hash",
            ingest_api_key="short-ingest-key",
            cors_origins="https://admin.gamepickup.dev",
            expo_push_enabled=True,
            scheduler_enabled=True,
            privacy_contact_email="owner@example.com",
        )

    valid = Settings(
        env="production",
        database_url="postgresql+psycopg://user:pass@db/gamepickup",
        jwt_secret="rotated-secret-for-production-tests-32",
        admin_password_hash="$2b$12$MAR4MoI546y9/F7qRnjHOurpcgIqrZLV1y5zqoZ2nkhDDlWfvIO5u",
        ingest_api_key="ingest-key-for-production-tests-32",
        cors_origins="https://admin.gamepickup.dev",
        expo_push_enabled=True,
        scheduler_enabled=True,
        privacy_contact_email="owner@gamepickup.dev",
    )
    assert valid.is_production is True

    normalized = Settings(
        **{
            **valid.model_dump(),
            "database_url": "postgresql://user:pass@db/gamepickup",
        }
    )
    assert normalized.database_url == "postgresql+psycopg://user:pass@db/gamepickup"

    with pytest.raises(ValueError, match="ADMIN_PASSWORD_HASH"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://user:pass@db/gamepickup",
            jwt_secret="rotated-secret-for-production-tests-32",
            admin_password_hash="bcrypt-hash",
            ingest_api_key="ingest-key-for-production-tests-32",
            cors_origins="https://admin.gamepickup.dev",
            expo_push_enabled=True,
            scheduler_enabled=True,
            privacy_contact_email="owner@gamepickup.dev",
        )

    with pytest.raises(ValueError, match="HTTPS origins"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://user:pass@db/gamepickup",
            jwt_secret="rotated-secret-for-production-tests-32",
            admin_password_hash="bcrypt-hash",
            ingest_api_key="ingest-key-for-production-tests-32",
            cors_origins="http://localhost:5173",
            expo_push_enabled=True,
            scheduler_enabled=True,
            privacy_contact_email="owner@gamepickup.dev",
        )

    with pytest.raises(ValueError, match="development placeholders"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://user:pass@db/gamepickup",
            jwt_secret="rotated-secret-for-production-tests-32",
            admin_password_hash="bcrypt-hash",
            ingest_api_key="ingest-key-for-production-tests-32",
            cors_origins="https://admin.localhost",
            expo_push_enabled=True,
            scheduler_enabled=True,
            privacy_contact_email="owner@gamepickup.dev",
        )

    with pytest.raises(ValueError, match="PRIVACY_CONTACT_EMAIL"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://user:pass@db/gamepickup",
            jwt_secret="rotated-secret-for-production-tests-32",
            admin_password_hash="bcrypt-hash",
            ingest_api_key="ingest-key-for-production-tests-32",
            cors_origins="https://admin.gamepickup.dev",
            expo_push_enabled=True,
            scheduler_enabled=True,
            privacy_contact_email="owner@example.com",
        )


def test_privacy_page_uses_configured_contact_safely(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("PRIVACY_CONTACT_EMAIL", "owner+privacy@example.com")
    get_settings.cache_clear()
    response = client[0].get("/privacy")
    assert response.status_code == 200
    assert "owner+privacy@example.com" in response.text
    assert "__CONTACT_EMAIL__" not in response.text


def test_production_security_headers_include_hsts_and_csp(monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app import main

    production = Settings(
        env="production",
        database_url="postgresql+psycopg://user:pass@db/gamepickup",
        jwt_secret="rotated-secret-for-production-tests-32",
        admin_password_hash="$2b$12$MAR4MoI546y9/F7qRnjHOurpcgIqrZLV1y5zqoZ2nkhDDlWfvIO5u",
        ingest_api_key="ingest-key-for-production-tests-32",
        cors_origins="https://admin.gamepickup.dev",
        expo_push_enabled=True,
        scheduler_enabled=True,
        privacy_contact_email="owner@gamepickup.dev",
    )
    monkeypatch.setattr(main, "get_settings", lambda: production)
    # 이 테스트의 관심사는 보안 헤더와 문서 라우트다. 앱 lifespan의 DB
    # 초기화는 PostgreSQL 통합 테스트에서 별도로 검증하므로, 환경에 따라
    # 기본 로컬 포트에 연결을 시도하지 않도록 격리한다.
    monkeypatch.setattr(main, "_initialize_database", lambda: None)
    with TestClient(main.create_app()) as test_client:
        response = test_client.get("/health/live")
        docs_response = test_client.get("/docs")
        openapi_response = test_client.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers["strict-transport-security"].startswith("max-age=31536000")
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert docs_response.status_code == 404
    assert openapi_response.status_code == 404


def test_development_api_docs_remain_available(monkeypatch):
    from fastapi.testclient import TestClient

    from app import main

    # 개발 설정으로 create_app()을 만들면 로컬 계약 확인용 문서를 유지한다.
    monkeypatch.setattr(main, "_initialize_database", lambda: None)
    with TestClient(main.create_app()) as test_client:
        assert test_client.get("/docs").status_code == 200
        assert test_client.get("/openapi.json").status_code == 200


def test_database_initialization_retries_transient_connection(monkeypatch):
    """API가 DB보다 먼저 부팅돼도 제한된 횟수 안에 초기화를 재시도한다."""
    from pathlib import Path

    from sqlalchemy.exc import SQLAlchemyError

    # 모듈 import 시 기본 앱이 정적 디렉터리를 준비하므로 이미 존재하는
    # 저장소 디렉터리를 사용해 테스트 자체가 파일시스템 권한에 좌우되지 않게 한다.
    server_dir = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("MEDIA_DIR", str(server_dir))
    monkeypatch.setenv("ADMIN_DIST_DIR", str(server_dir))
    from app import main

    attempts = 0

    def flaky_create_all(*, bind):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise SQLAlchemyError("temporary database startup failure")

    monkeypatch.setattr(main.Base.metadata, "create_all", flaky_create_all)
    monkeypatch.setattr(main, "ensure_schema", lambda _engine: None)
    monkeypatch.setattr(main.engine, "dispose", lambda: None)
    monkeypatch.setattr(main.time, "sleep", lambda _seconds: None)

    main._initialize_database()

    assert attempts == 3


def test_published_content_requires_official_url(client):
    c, headers = _admin_headers(client)
    game = c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={"id": "g_url_guard", "name": "URL 검증 게임"},
    )
    assert game.status_code == 201
    content = c.post(
        "/api/v1/admin/contents",
        headers=headers,
        json={
            "game_id": "g_url_guard",
            "kind": "update",
            "title": "원문 없는 공지",
            "summary_points": ["요약"],
            "status": "draft",
        },
    ).json()
    assert c.patch(
        f"/api/v1/admin/contents/{content['id']}",
        headers=headers,
        json={"status": "reviewed"},
    ).status_code == 200
    published = c.patch(
        f"/api/v1/admin/contents/{content['id']}",
        headers=headers,
        json={"status": "published"},
    )
    assert published.status_code == 400


def test_published_content_cannot_clear_official_url(client):
    c, headers = _admin_headers(client)
    assert c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={"id": "g_url_retain", "name": "원문 유지 게임"},
    ).status_code == 201
    content = c.post(
        "/api/v1/admin/contents",
        headers=headers,
        json={
            "game_id": "g_url_retain",
            "kind": "update",
            "title": "공식 공지",
            "summary_points": ["요약"],
            "official_url": "https://official.example.com/notice",
            "status": "draft",
        },
    ).json()
    assert c.patch(
        f"/api/v1/admin/contents/{content['id']}",
        headers=headers,
        json={"status": "reviewed"},
    ).status_code == 200
    assert c.patch(
        f"/api/v1/admin/contents/{content['id']}",
        headers=headers,
        json={"status": "published"},
    ).status_code == 200
    cleared = c.patch(
        f"/api/v1/admin/contents/{content['id']}",
        headers=headers,
        json={"official_url": ""},
    )
    assert cleared.status_code == 400


def test_image_urls_reject_non_http_schemes(client):
    c, headers = _admin_headers(client)
    response = c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={
            "id": "g_image_scheme_guard",
            "name": "이미지 스킴 검증 게임",
            "image_url": "javascript:alert(1)",
        },
    )
    assert response.status_code == 400


def test_image_source_rejects_embedded_credentials(client):
    c, headers = _admin_headers(client)
    response = c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={
            "id": "g_image_credential_guard",
            "name": "이미지 출처 검증 게임",
            "image_url": "https://cdn.example.com/cover.png",
            "image_source_url": "https://user:password@example.com/license",
            "image_rights_status": "official",
        },
    )
    assert response.status_code == 400


def test_content_period_cannot_end_before_start(client):
    c, headers = _admin_headers(client)
    assert c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={"id": "g_period_guard", "name": "기간 검증 게임"},
    ).status_code == 201
    response = c.post(
        "/api/v1/admin/contents",
        headers=headers,
        json={
            "game_id": "g_period_guard",
            "kind": "event",
            "title": "잘못된 기간",
            "starts_at": datetime(2026, 9, 2, tzinfo=timezone.utc).isoformat(),
            "ends_at": datetime(2026, 9, 1, tzinfo=timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 422


def test_summary_points_have_bounded_input_contract():
    """관리자·수집기 입력이 공개 카드 크기를 무제한으로 늘리지 않게 한다."""
    from pydantic import ValidationError

    from app.schemas.common import ContentCreate, ContentUpdate, IngestContentCreate

    with pytest.raises(ValidationError):
        ContentCreate(
            game_id="g_summary_limit",
            kind="update",
            title="요약 개수 초과",
            summary_points=[str(index) for index in range(9)],
        )

    long_point = "가" * 501
    with pytest.raises(ValidationError):
        ContentUpdate(summary_points=[long_point])

    with pytest.raises(ValidationError):
        IngestContentCreate(
            game_id="g_summary_limit",
            title="수집 요약 길이 초과",
            summary_points=[long_point],
        )


def test_ingest_preserves_image_rights_metadata(client):
    c, headers = _admin_headers(client)
    assert c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={"id": "g_ingest_rights", "name": "권리 메타 게임"},
    ).status_code == 201
    response = c.post(
        "/api/v1/ingest/contents",
        headers={"X-Ingest-Key": "test-ingest-key"},
        json={
            "game_id": "g_ingest_rights",
            "title": "공식 이미지 소식",
            "official_url": "https://example.com/rights",
            "image_url": "/media/img_rights.png",
            "image_source_url": "https://example.com/image-rights",
            "image_rights_status": "official",
        },
    )
    assert response.status_code == 201, response.text
    content = c.get("/api/v1/admin/contents", headers=headers).json()[0]
    assert content["image_rights_status"] == "official"
    assert content["image_source_url"] == "https://example.com/image-rights"


def test_public_catalog_hides_unverified_image_urls(client):
    c, headers = _admin_headers(client)
    assert c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={
            "id": "g_unverified_image",
            "name": "검수 대기 게임",
            "image_url": "https://cdn.example.com/pending.png",
            "image_rights_status": "unverified",
        },
    ).status_code == 201

    public_game = next(
        row for row in c.get("/api/v1/games").json() if row["id"] == "g_unverified_image"
    )
    public_rank = next(
        row for row in c.get("/api/v1/rankings").json()
        if row["game_id"] == "g_unverified_image"
    )
    admin_game = next(
        row
        for row in c.get("/api/v1/admin/games", headers=headers).json()
        if row["id"] == "g_unverified_image"
    )
    assert public_game["image_url"] is None
    assert public_game["image_source_url"] is None
    assert public_rank["image_url"] is None
    assert admin_game["image_url"] == "https://cdn.example.com/pending.png"


def test_public_content_hides_image_source_url(client):
    c, headers = _admin_headers(client)
    assert c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={"id": "g_public_content_image", "name": "콘텐츠 이미지 게임"},
    ).status_code == 201
    created = c.post(
        "/api/v1/admin/contents",
        headers=headers,
        json={
            "game_id": "g_public_content_image",
            "kind": "update",
            "title": "미승인 콘텐츠 이미지",
            "summary_points": ["공식 공지를 확인하세요"],
            "official_url": "https://official.example.com/content-image",
            "image_url": "https://cdn.example.com/content.png",
            "image_source_url": "https://cdn.example.com/content-source",
            "image_rights_status": "unverified",
            "status": "draft",
        },
    )
    assert created.status_code == 201
    content_id = created.json()["id"]
    assert c.patch(
        f"/api/v1/admin/contents/{content_id}",
        headers=headers,
        json={"status": "reviewed"},
    ).status_code == 200
    assert c.patch(
        f"/api/v1/admin/contents/{content_id}",
        headers=headers,
        json={"status": "published"},
    ).status_code == 200

    public_item = c.get("/api/v1/contents").json()[0]
    assert public_item["image_url"] is None
    assert public_item["image_source_url"] is None
    admin_item = c.get(
        "/api/v1/admin/contents", headers=headers
    ).json()[0]
    assert admin_item["image_source_url"] == "https://cdn.example.com/content-source"


def test_privacy_page_served_at_root(client):
    c, _ = client
    res = c.get("/privacy")
    assert res.status_code == 200
    assert "개인정보처리방침" in res.text


def test_terms_page_served_at_root(client):
    c, _ = client
    res = c.get("/terms")
    assert res.status_code == 200
    assert "이용약관" in res.text
    assert "참고용" in res.text
    assert "자동 정리" in res.text.replace("\n", " ")


def test_inquiry_rate_limit(client):
    c, _ = client
    payload = {"category": "general", "message": "문의 rate limit 테스트입니다"}
    for _i in range(5):
        res = c.post("/api/v1/inquiries", json=payload)
        assert res.status_code == 201, res.text
    blocked = c.post("/api/v1/inquiries", json=payload)
    assert blocked.status_code == 429


def test_installation_registration_rate_limit(client, monkeypatch):
    from app.api import installations

    monkeypatch.setattr(installations, "_REGISTER_MAX_PER_IP", 1)
    c, _ = client
    assert c.post("/api/v1/installations").status_code == 201
    blocked = c.post("/api/v1/installations")
    assert blocked.status_code == 429
    assert blocked.headers.get("retry-after") == "600"
