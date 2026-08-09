"""인증 부정 경로 — 최소 권한 경계를 증명."""


def test_admin_requires_bearer(client) -> None:
    c, _ = client
    assert c.get("/api/v1/admin/games").status_code == 401
    assert (
        c.get(
            "/api/v1/admin/games",
            headers={"Authorization": "Bearer not-a-jwt"},
        ).status_code
        == 401
    )


def test_ingest_requires_key(client) -> None:
    c, _ = client
    assert c.post("/api/v1/ingest/contents", json={"game_id": "x", "title": "t"}).status_code == 401
    assert (
        c.post(
            "/api/v1/ingest/contents",
            headers={"X-Ingest-Key": "wrong"},
            json={"game_id": "x", "title": "t"},
        ).status_code
        == 401
    )


def test_installation_write_requires_credentials(client) -> None:
    c, _ = client
    assert (
        c.put(
            "/api/v1/installations/me/device-token",
            json={"platform": "android", "token": "token-12345678"},
        ).status_code
        == 401
    )
    assert (
        c.put(
            "/api/v1/installations/me/preferences",
            headers={
                "X-Installation-Id": "inst_nope",
                "X-Installation-Secret": "bad",
            },
            json={"game_ids": [], "notifications": {}},
        ).status_code
        == 401
    )
