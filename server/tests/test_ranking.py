"""관심 게임 집계 랭킹의 공개 계약 검증."""


def _admin_headers(client):
    c, password = client
    token = c.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": password},
    ).json()["access_token"]
    return c, {"Authorization": f"Bearer {token}"}


def _pick(c, game_ids):
    registration = c.post("/api/v1/installations").json()
    headers = {
        "X-Installation-Id": registration["installation_id"],
        "X-Installation-Secret": registration["secret"],
    }
    response = c.put(
        "/api/v1/installations/me/preferences",
        headers=headers,
        json={"game_ids": game_ids},
    )
    assert response.status_code == 200, response.text


def test_ranking_uses_active_installation_picks_not_manual_counter(client):
    c, headers = _admin_headers(client)
    for game_id, name, manual_count in (
        ("g_a", "알파", 0),
        ("g_b", "베타", 9999),
        ("g_c", "감마", 5000),
    ):
        response = c.post(
            "/api/v1/admin/games",
            headers=headers,
            json={"id": game_id, "name": name, "interest_count": manual_count},
        )
        assert response.status_code == 201

    _pick(c, ["g_a"])
    _pick(c, ["g_a", "g_b"])

    rows = c.get("/api/v1/rankings").json()
    assert [(row["game_id"], row["interest_count"], row["rank"]) for row in rows] == [
        ("g_a", 2, 1),
        ("g_b", 1, 2),
        ("g_c", 0, 3),
    ]
    game_rows = {row["id"]: row for row in c.get("/api/v1/games").json()}
    assert game_rows["g_b"]["interest_count"] == 1
    assert game_rows["g_c"]["interest_count"] == 0
    admin_rows = {
        row["id"]: row for row in c.get("/api/v1/admin/games", headers=headers).json()
    }
    assert admin_rows["g_a"]["interest_count"] == 2
    assert admin_rows["g_b"]["interest_count"] == 1
    assert admin_rows["g_c"]["interest_count"] == 0


def test_preferences_reject_more_than_eight_games(client):
    c, _ = client
    registration = c.post("/api/v1/installations").json()
    headers = {
        "X-Installation-Id": registration["installation_id"],
        "X-Installation-Secret": registration["secret"],
    }
    response = c.put(
        "/api/v1/installations/me/preferences",
        headers=headers,
        json={"game_ids": [f"g_{i}" for i in range(9)]},
    )
    assert response.status_code == 422


def test_preferences_drop_games_not_in_active_catalog(client):
    c, headers = _admin_headers(client)
    assert c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={"id": "g_active_only", "name": "활성 게임"},
    ).status_code == 201
    registration = c.post("/api/v1/installations").json()
    installation_headers = {
        "X-Installation-Id": registration["installation_id"],
        "X-Installation-Secret": registration["secret"],
    }
    response = c.put(
        "/api/v1/installations/me/preferences",
        headers=installation_headers,
        json={"game_ids": ["g_active_only", "g_retired_or_unknown"]},
    )
    assert response.status_code == 200
    assert response.json()["game_ids"] == ["g_active_only"]


def test_health_live_and_ready_endpoints(client):
    c, _ = client
    assert c.get("/health/live").json() == {"status": "ok"}
    assert c.get("/health/ready").json() == {"status": "ok", "database": "ok"}


def test_installation_revoke_removes_pick_from_ranking(client):
    c, headers = _admin_headers(client)
    assert c.post(
        "/api/v1/admin/games",
        headers=headers,
        json={"id": "g_revoke", "name": "해지 게임"},
    ).status_code == 201
    registration = c.post("/api/v1/installations").json()
    installation_headers = {
        "X-Installation-Id": registration["installation_id"],
        "X-Installation-Secret": registration["secret"],
    }
    assert c.put(
        "/api/v1/installations/me/preferences",
        headers=installation_headers,
        json={"game_ids": ["g_revoke"]},
    ).status_code == 200
    assert c.delete("/api/v1/installations/me", headers=installation_headers).status_code == 204
    row = next(r for r in c.get("/api/v1/rankings").json() if r["game_id"] == "g_revoke")
    assert row["interest_count"] == 0
    assert c.get("/api/v1/installations/me/preferences", headers=installation_headers).status_code == 401
