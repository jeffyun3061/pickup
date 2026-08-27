import socket
from datetime import datetime, timedelta, timezone


def _admin(client):
    c, password = client
    token = c.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": password},
    ).json()["access_token"]
    return c, {"Authorization": f"Bearer {token}"}


def test_source_job_draft_and_history(client, monkeypatch) -> None:
    c, admin_headers = _admin(client)
    c.post(
        "/api/v1/admin/games",
        headers=admin_headers,
        json={"id": "g_auto", "name": "AUTO GAME"},
    )

    real_resolver = socket.getaddrinfo

    def public_resolver(host, port, *args, **kwargs):
        if host == "feeds.example.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
        return real_resolver(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", public_resolver)
    source = c.post(
        "/api/v1/admin/ingest-sources",
        headers=admin_headers,
        json={
            "name": "공식 RSS",
            "source_type": "rss",
            "game_id": "g_auto",
            "endpoint_url": "https://feeds.example.com/news.xml",
            "interval_minutes": 30,
            "config": {"kind": "update"},
        },
    )
    assert source.status_code == 201
    source_id = source.json()["id"]

    audit_actions = [
        row["action"]
        for row in c.get("/api/v1/admin/audit-logs", headers=admin_headers).json()
    ]
    assert "관리자 로그인" in audit_actions
    assert "수집 소스 등록" in audit_actions

    queued = c.post(
        f"/api/v1/admin/ingest-sources/{source_id}/runs",
        headers=admin_headers,
    )
    assert queued.status_code == 202
    assert queued.json()["status"] == "pending"

    ingest_headers = {"X-Ingest-Key": "test-ingest-key"}
    job = c.post("/api/v1/ingest/jobs/claim", headers=ingest_headers)
    assert job.status_code == 200
    assert job.json()["source"]["id"] == source_id
    run_id = job.json()["run"]["id"]

    payload = {
        "source_id": source_id,
        "game_id": "g_auto",
        "title": "자동 수집 소식",
        "official_url": "https://example.com/news/1",
        "idempotency_key": "external-1",
    }
    first = c.post("/api/v1/ingest/contents", headers=ingest_headers, json=payload)
    second = c.post("/api/v1/ingest/contents", headers=ingest_headers, json=payload)
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["created"] is True
    assert second.json()["created"] is False
    assert first.json()["status"] == "draft"
    assert first.json()["idempotency_key"].startswith("src:")
    assert c.get("/api/v1/contents").json() == []

    completed = c.post(
        f"/api/v1/ingest/jobs/{run_id}/complete",
        headers=ingest_headers,
        json={"status": "succeeded", "items_seen": 1, "items_created": 1},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "succeeded"
    history = c.get("/api/v1/admin/ingest-runs", headers=admin_headers).json()
    assert history[0]["items_created"] == 1

    renamed = c.patch(
        f"/api/v1/admin/ingest-sources/{source_id}",
        headers=admin_headers,
        json={"name": "공식 RSS 수정"},
    )
    assert renamed.status_code == 200
    assert c.delete(
        f"/api/v1/admin/ingest-sources/{source_id}",
        headers=admin_headers,
    ).status_code == 204
    audit_actions = [
        row["action"]
        for row in c.get("/api/v1/admin/audit-logs", headers=admin_headers).json()
    ]
    assert "수집 소스 수정" in audit_actions
    assert "수집 소스 삭제" in audit_actions


def test_ingest_idempotency_is_scoped_per_source(client) -> None:
    c, admin_headers = _admin(client)
    c.post(
        "/api/v1/admin/games",
        headers=admin_headers,
        json={"id": "g_scope", "name": "SCOPE GAME"},
    )
    sources = []
    for name, endpoint in (
        ("source one", "https://example.com/one.xml"),
        ("source two", "https://example.com/two.xml"),
    ):
        response = c.post(
            "/api/v1/admin/ingest-sources",
            headers=admin_headers,
            json={
                "name": name,
                "source_type": "rss",
                "game_id": "g_scope",
                "endpoint_url": endpoint,
            },
        )
        assert response.status_code == 201, response.text
        sources.append(response.json()["id"])

    ingest_headers = {"X-Ingest-Key": "test-ingest-key"}
    ids = []
    for source_id in sources:
        response = c.post(
            "/api/v1/ingest/contents",
            headers=ingest_headers,
            json={
                "source_id": source_id,
                "game_id": "g_scope",
                "title": "같은 외부 GUID 공지",
                "official_url": "https://example.com/news/same",
                "idempotency_key": "same-guid",
            },
        )
        assert response.status_code == 201, response.text
        ids.append(response.json())

    assert ids[0]["id"] != ids[1]["id"]
    assert ids[0]["idempotency_key"] != ids[1]["idempotency_key"]


def test_private_source_url_and_worker_auth_are_rejected(client) -> None:
    c, admin_headers = _admin(client)
    c.post(
        "/api/v1/admin/games",
        headers=admin_headers,
        json={"id": "g_safe", "name": "SAFE GAME"},
    )
    blocked = c.post(
        "/api/v1/admin/ingest-sources",
        headers=admin_headers,
        json={
            "name": "내부망",
            "source_type": "rss",
            "game_id": "g_safe",
            "endpoint_url": "http://127.0.0.1/private",
        },
    )
    assert blocked.status_code == 400
    assert c.post("/api/v1/ingest/jobs/claim").status_code == 401
    assert c.get("/api/v1/admin/ingest-sources").status_code == 401


def test_stale_running_job_is_recovered_and_backed_off(client) -> None:
    c, admin_headers = _admin(client)
    c.post(
        "/api/v1/admin/games",
        headers=admin_headers,
        json={"id": "g_stale", "name": "STALE GAME"},
    )

    # URL 검증을 통과시키기 위해 실제 공개 예제 주소를 테스트 소스로 사용한다.
    source = c.post(
        "/api/v1/admin/ingest-sources",
        headers=admin_headers,
        json={
            "name": "stale source",
            "source_type": "rss",
            "game_id": "g_stale",
            "endpoint_url": "https://example.com/feed.xml",
            "interval_minutes": 30,
        },
    )
    assert source.status_code == 201, source.text
    source_id = source.json()["id"]
    ingest_headers = {"X-Ingest-Key": "test-ingest-key"}
    claimed = c.post("/api/v1/ingest/jobs/claim", headers=ingest_headers)
    assert claimed.status_code == 200
    run_id = claimed.json()["run"]["id"]

    # 실제 collector가 죽은 상황을 재현한다.
    from app.db import SessionLocal
    from app.models.entities import IngestRun

    db = SessionLocal()
    try:
        run = db.get(IngestRun, run_id)
        assert run is not None
        run.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()
    finally:
        db.close()

    # 다음 claim에서 고아 작업이 failed로 회수된다.
    again = c.post("/api/v1/ingest/jobs/claim", headers=ingest_headers)
    assert again.status_code == 200
    history = c.get("/api/v1/admin/ingest-runs", headers=admin_headers).json()
    recovered = next(row for row in history if row["id"] == run_id)
    assert recovered["status"] == "failed"
    assert "heartbeat timed out" in recovered["error"]


def test_security_headers_are_present(client) -> None:
    c, _ = client
    response = c.get("/health/live")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
