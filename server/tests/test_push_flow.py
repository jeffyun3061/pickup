"""설치 credential → device token → preference → publish outbox → stub dispatch."""


def _admin_headers(c, password: str) -> dict[str, str]:
    login = c.post("/api/v1/admin/login", json={"username": "admin", "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_install_publish_enqueues_and_dispatch(client) -> None:
    c, password = client
    admin = _admin_headers(c, password)

    game = c.post(
        "/api/v1/admin/games",
        headers=admin,
        json={"id": "g_neon", "name": "Neon Grid"},
    )
    assert game.status_code == 201

    reg = c.post("/api/v1/installations")
    assert reg.status_code == 201
    installation_id = reg.json()["installation_id"]
    secret = reg.json()["secret"]
    inst_headers = {
        "X-Installation-Id": installation_id,
        "X-Installation-Secret": secret,
    }

    token_res = c.put(
        "/api/v1/installations/me/device-token",
        headers=inst_headers,
        json={"platform": "android", "token": "fcm-test-token-abcdef"},
    )
    assert token_res.status_code == 200

    prefs = c.put(
        "/api/v1/installations/me/preferences",
        headers=inst_headers,
        json={
            "game_ids": ["g_neon"],
            "notifications": {
                "selected_game_news": True,
                "event_ending": True,
                "service_notices": True,
            },
        },
    )
    assert prefs.status_code == 200
    assert prefs.json()["game_ids"] == ["g_neon"]

    # 다른 게임만 고른 설치는 outbox에 안 들어감
    reg2 = c.post("/api/v1/installations")
    h2 = {
        "X-Installation-Id": reg2.json()["installation_id"],
        "X-Installation-Secret": reg2.json()["secret"],
    }
    c.put(
        "/api/v1/installations/me/device-token",
        headers=h2,
        json={"platform": "android", "token": "fcm-other-token-xyz"},
    )
    c.put(
        "/api/v1/installations/me/preferences",
        headers=h2,
        json={"game_ids": ["g_other"], "notifications": {"selected_game_news": True}},
    )

    content = c.post(
        "/api/v1/admin/contents",
        headers=admin,
        json={
            "game_id": "g_neon",
            "kind": "update",
            "title": "밸런스 패치",
            "summary_points": ["너프"],
            "status": "draft",
        },
    )
    content_id = content.json()["id"]
    assert (
        c.patch(
            f"/api/v1/admin/contents/{content_id}",
            headers=admin,
            json={"status": "reviewed"},
        ).status_code
        == 200
    )
    pub = c.patch(
        f"/api/v1/admin/contents/{content_id}",
        headers=admin,
        json={"status": "published"},
    )
    assert pub.status_code == 200

    dispatch = c.post("/api/v1/admin/push/dispatch", headers=admin)
    assert dispatch.status_code == 200
    body = dispatch.json()
    assert body["processed"] == 1
    assert body["sent"] == 1
    assert body["failed"] == 0

    # 재호출 시 pending 없음
    again = c.post("/api/v1/admin/push/dispatch", headers=admin).json()
    assert again["processed"] == 0


def test_domain_push_targeting_unit() -> None:
    from app.domain.push_targeting import (
        NotificationPrefs,
        should_notify_content_publish,
        should_notify_service_announcement,
    )

    prefs = NotificationPrefs(
        game_ids=("g1",),
        selected_game_news=False,
        event_ending=True,
        service_notices=False,
    )
    assert should_notify_content_publish(prefs, game_id="g1", kind="event") is True
    assert should_notify_content_publish(prefs, game_id="g1", kind="update") is False
    assert should_notify_content_publish(prefs, game_id="g2", kind="event") is False
    assert should_notify_service_announcement(prefs) is False
