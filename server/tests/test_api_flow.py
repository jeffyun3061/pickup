"""API 통합 스모크: Public / Admin / Ingest 경계."""


def test_public_empty_catalog(client) -> None:
    c, _ = client
    assert c.get("/api/v1/health").json()["status"] == "ok"
    assert c.get("/api/v1/games").json() == []
    assert c.get("/api/v1/contents").json() == []


def test_admin_publish_and_public_read(client) -> None:
    c, password = client
    login = c.post("/api/v1/admin/login", json={"username": "admin", "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    game = c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={"name": "프로젝트: 섀도우", "genre": "전술 RPG", "interest_count": 100},
    )
    assert game.status_code == 201
    game_id = game.json()["id"]

    content = c.post(
        "/api/v1/admin/contents",
        headers=headers,
        json={
            "game_id": game_id,
            "kind": "update",
            "title": "패치 노트",
            "summary_points": ["밸런스", "버그 수정"],
            "status": "draft",
        },
    )
    assert content.status_code == 201
    content_id = content.json()["id"]
    assert content.json()["status"] == "draft"
    assert c.get("/api/v1/contents").json() == []

    bad = c.patch(
        f"/api/v1/admin/contents/{content_id}",
        headers=headers,
        json={"status": "published"},
    )
    assert bad.status_code == 400

    assert (
        c.patch(
            f"/api/v1/admin/contents/{content_id}",
            headers=headers,
            json={"status": "reviewed"},
        ).status_code
        == 200
    )
    pub = c.patch(
        f"/api/v1/admin/contents/{content_id}",
        headers=headers,
        json={"status": "published"},
    )
    assert pub.status_code == 200
    assert pub.json()["status"] == "published"
    assert pub.json()["published_at"] is not None

    public_list = c.get("/api/v1/contents").json()
    assert len(public_list) == 1
    assert public_list[0]["title"] == "패치 노트"


def test_ingest_draft_only_and_idempotent(client) -> None:
    c, password = client
    login = c.post("/api/v1/admin/login", json={"username": "admin", "password": password})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    game = c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={"id": "g_test", "name": "TEST GAME"},
    )
    assert game.status_code == 201

    ingest_headers = {"X-Ingest-Key": "test-ingest-key"}
    payload = {
        "game_id": "g_test",
        "title": "자동 수집 초안",
        "summary_points": ["a"],
        "idempotency_key": "rss-item-1",
    }
    r1 = c.post("/api/v1/ingest/contents", headers=ingest_headers, json=payload)
    r2 = c.post("/api/v1/ingest/contents", headers=ingest_headers, json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]
    assert r1.json()["status"] == "draft"
    assert c.get("/api/v1/contents").json() == []


def test_inquiry_public(client) -> None:
    c, _ = client
    r = c.post(
        "/api/v1/inquiries",
        json={"email": "user@example.com", "category": "bug", "message": "앱이 안 열려요"},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "open"
