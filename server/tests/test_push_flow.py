"""설치 credential → device token → preference → publish outbox → dispatch 계약."""

import json
from datetime import datetime, timedelta, timezone


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
            "official_url": "https://example.com/patch",
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


def test_manual_dispatch_can_override_quiet_hours(client, monkeypatch) -> None:
    """대시보드의 즉시 발송은 예약된 조용시간 푸시도 처리한다."""
    c, password = client
    admin = _admin_headers(c, password)

    game = c.post(
        "/api/v1/admin/games",
        headers=admin,
        json={"id": "g_quiet", "name": "Quiet Game"},
    )
    assert game.status_code == 201

    reg = c.post("/api/v1/installations").json()
    inst_headers = {
        "X-Installation-Id": reg["installation_id"],
        "X-Installation-Secret": reg["secret"],
    }
    assert c.put(
        "/api/v1/installations/me/device-token",
        headers=inst_headers,
        json={"platform": "android", "token": "ExponentPushToken[quiet-test]"},
    ).status_code == 200
    assert c.put(
        "/api/v1/installations/me/preferences",
        headers=inst_headers,
        json={
            "game_ids": ["g_quiet"],
            "notifications": {"selected_game_news": True},
        },
    ).status_code == 200

    from app.services import push_service

    monkeypatch.setattr(
        push_service,
        "resolve_available_at",
        lambda *_args, **_kwargs: datetime.now(timezone.utc) + timedelta(hours=1),
    )
    content = c.post(
        "/api/v1/admin/contents",
        headers=admin,
        json={
            "game_id": "g_quiet",
            "kind": "update",
            "title": "예약 알림 테스트",
            "summary_points": ["테스트"],
            "official_url": "https://example.com/quiet",
            "status": "draft",
        },
    ).json()
    assert c.patch(
        f"/api/v1/admin/contents/{content['id']}",
        headers=admin,
        json={"status": "reviewed"},
    ).status_code == 200
    assert c.patch(
        f"/api/v1/admin/contents/{content['id']}",
        headers=admin,
        json={"status": "published"},
    ).status_code == 200

    delayed = c.post("/api/v1/admin/push/dispatch", headers=admin).json()
    assert delayed["processed"] == 0

    immediate = c.post(
        "/api/v1/admin/push/dispatch?force=true", headers=admin
    ).json()
    assert immediate == {"processed": 1, "sent": 1, "failed": 0}


def test_content_pushes_are_grouped_by_game(client) -> None:
    c, password = client
    admin = _admin_headers(c, password)

    game = c.post(
        "/api/v1/admin/games",
        headers=admin,
        json={"id": "g_grouped", "name": "Grouped Game"},
    )
    assert game.status_code == 201

    reg = c.post("/api/v1/installations").json()
    inst_headers = {
        "X-Installation-Id": reg["installation_id"],
        "X-Installation-Secret": reg["secret"],
    }
    assert c.put(
        "/api/v1/installations/me/device-token",
        headers=inst_headers,
        json={"platform": "android", "token": "ExponentPushToken[grouped]"},
    ).status_code == 200
    assert c.put(
        "/api/v1/installations/me/preferences",
        headers=inst_headers,
        json={"game_ids": ["g_grouped"]},
    ).status_code == 200

    content_ids = []
    for index in range(3):
        response = c.post(
            "/api/v1/admin/contents",
            headers=admin,
            json={
                "game_id": "g_grouped",
                "kind": "update",
                "title": f"패치 소식 {index + 1}",
                "summary_points": ["변경 사항"],
                "official_url": f"https://example.com/grouped-{index}",
                "status": "published",
            },
        )
        assert response.status_code == 201
        content_ids.append(response.json()["id"])

    from app.db import SessionLocal
    from app.models.entities import PushOutbox

    db = SessionLocal()
    try:
        rows = list(db.query(PushOutbox).all())
        assert len(rows) == 1
        payload = json.loads(rows[0].payload_json)
    finally:
        db.close()

    assert payload["game_name"] == "Grouped Game"
    assert payload["content_count"] == 3
    assert payload["content_ids"] == content_ids
    assert payload["title"] == "Grouped Game 새 소식 3건"


def test_notification_copy_uses_brand_and_groups_content() -> None:
    from app.services.push_service import _notification_copy

    title, body = _notification_copy(
        "content_published",
        {"game_name": "니케", "content_count": 3, "title": "첫 번째 소식"},
    )
    assert title == "피키의 새로운 소식 ~♬"
    assert body == "니케에 새 소식 3건이 올라왔어요"

    title, body = _notification_copy(
        "content_published",
        {"game_name": "니케", "content_count": 1, "title": "신규 캐릭터 안내"},
    )
    assert title == "피키의 새로운 소식 ~♬"
    assert body == "니케 · 신규 캐릭터 안내"


def test_notification_copy_distinguishes_event_and_service() -> None:
    from app.services.push_service import _notification_copy

    assert _notification_copy(
        "event_ending",
        {"game_name": "블루 아카이브", "title": "여름 이벤트"},
    ) == ("피키의 이벤트 알림", "블루 아카이브 · 여름 이벤트 종료가 가까워요")
    assert _notification_copy(
        "service_notice", {"title": "점검 안내"}
    ) == ("피키 공지", "점검 안내")


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
    assert should_notify_content_publish(prefs, game_id="g1", kind="event") is False
    assert should_notify_content_publish(
        NotificationPrefs(
            game_ids=("g1",),
            selected_game_news=True,
            event_ending=False,
            service_notices=False,
        ),
        game_id="g1",
        kind="event",
    ) is True
    assert should_notify_content_publish(prefs, game_id="g1", kind="update") is False
    assert should_notify_content_publish(prefs, game_id="g2", kind="event") is False
    assert should_notify_content_publish(
        NotificationPrefs(
            game_ids=("g1",),
            selected_game_news=True,
            event_ending=True,
            service_notices=True,
        ),
        game_id="g1",
        kind="popup",
    ) is False
    assert should_notify_service_announcement(prefs) is False


def test_expired_expo_token_is_removed_after_permanent_error(client, monkeypatch) -> None:
    c, password = client
    admin = _admin_headers(c, password)
    assert c.post(
        "/api/v1/admin/games",
        headers=admin,
        json={"id": "g_expo", "name": "Expo Game"},
    ).status_code == 201
    reg = c.post("/api/v1/installations").json()
    inst_headers = {
        "X-Installation-Id": reg["installation_id"],
        "X-Installation-Secret": reg["secret"],
    }
    assert c.put(
        "/api/v1/installations/me/device-token",
        headers=inst_headers,
        json={"platform": "android", "token": "ExpoPushToken[expired-token]"},
    ).status_code == 200
    assert c.put(
        "/api/v1/installations/me/preferences",
        headers=inst_headers,
        json={"game_ids": ["g_expo"]},
    ).status_code == 200

    created = c.post(
        "/api/v1/admin/contents",
        headers=admin,
        json={
            "game_id": "g_expo",
            "kind": "update",
            "title": "Expo 토큰 테스트",
            "official_url": "https://example.com/expo",
            "status": "draft",
        },
    ).json()
    assert c.patch(
        f"/api/v1/admin/contents/{created['id']}",
        headers=admin,
        json={"status": "reviewed"},
    ).status_code == 200
    assert c.patch(
        f"/api/v1/admin/contents/{created['id']}",
        headers=admin,
        json={"status": "published"},
    ).status_code == 200

    from app.config import get_settings
    from app.services import expo_push

    monkeypatch.setenv("EXPO_PUSH_ENABLED", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(
        expo_push,
        "send_messages",
        lambda _messages: ["The recipient device is not registered."],
    )
    result = c.post("/api/v1/admin/push/dispatch", headers=admin)
    assert result.status_code == 200
    assert result.json()["failed"] == 1
    # 폐기된 토큰은 제거되고 동일 outbox가 불필요하게 재시도되지 않는다.
    assert c.post("/api/v1/admin/push/dispatch", headers=admin).json()["processed"] == 0

    # 동일 설치로 토큰을 다시 올릴 수 있어야 한다(기존 폐기 토큰이 삭제됨).
    renewed = c.put(
        "/api/v1/installations/me/device-token",
        headers=inst_headers,
        json={"platform": "android", "token": "ExpoPushToken[new-token]"},
    )
    assert renewed.status_code == 200


def test_transient_expo_failure_is_retried_without_dropping_outbox(client, monkeypatch) -> None:
    """일시적인 Expo 장애는 토큰·알림을 버리지 않고 다음 주기에 재시도한다."""
    c, password = client
    admin = _admin_headers(c, password)
    assert c.post(
        "/api/v1/admin/games",
        headers=admin,
        json={"id": "g_retry", "name": "Retry Game"},
    ).status_code == 201

    reg = c.post("/api/v1/installations").json()
    inst_headers = {
        "X-Installation-Id": reg["installation_id"],
        "X-Installation-Secret": reg["secret"],
    }
    assert c.put(
        "/api/v1/installations/me/device-token",
        headers=inst_headers,
        json={"platform": "android", "token": "ExpoPushToken[retry-token]"},
    ).status_code == 200
    assert c.put(
        "/api/v1/installations/me/preferences",
        headers=inst_headers,
        json={"game_ids": ["g_retry"]},
    ).status_code == 200

    created = c.post(
        "/api/v1/admin/contents",
        headers=admin,
        json={
            "game_id": "g_retry",
            "kind": "update",
            "title": "재시도 테스트",
            "official_url": "https://example.com/retry",
            "status": "draft",
        },
    ).json()
    assert c.patch(
        f"/api/v1/admin/contents/{created['id']}",
        headers=admin,
        json={"status": "reviewed"},
    ).status_code == 200
    assert c.patch(
        f"/api/v1/admin/contents/{created['id']}",
        headers=admin,
        json={"status": "published"},
    ).status_code == 200

    from app.config import get_settings
    from app.services import expo_push

    get_settings.cache_clear()
    monkeypatch.setenv("EXPO_PUSH_ENABLED", "true")
    get_settings.cache_clear()
    calls = {"count": 0}

    def flaky_send(_messages):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("temporary Expo outage")
        return [None]

    monkeypatch.setattr(expo_push, "send_messages", flaky_send)

    first = c.post("/api/v1/admin/push/dispatch", headers=admin)
    assert first.status_code == 200
    assert first.json()["failed"] == 1
    assert first.json()["sent"] == 0

    second = c.post("/api/v1/admin/push/dispatch", headers=admin)
    assert second.status_code == 200
    assert second.json()["sent"] == 1
    assert second.json()["failed"] == 0
    assert calls["count"] == 2


def test_transient_expo_ticket_error_is_retried_without_dropping_outbox(client, monkeypatch) -> None:
    """HTTP 200 ticket의 rate limit 오류도 outbox에 남겨 다음 주기에 재시도한다."""
    c, password = client
    admin = _admin_headers(c, password)
    assert c.post(
        "/api/v1/admin/games",
        headers=admin,
        json={"id": "g_ticket_retry", "name": "Ticket Retry Game"},
    ).status_code == 201

    reg = c.post("/api/v1/installations").json()
    inst_headers = {
        "X-Installation-Id": reg["installation_id"],
        "X-Installation-Secret": reg["secret"],
    }
    assert c.put(
        "/api/v1/installations/me/device-token",
        headers=inst_headers,
        json={"platform": "android", "token": "ExpoPushToken[ticket-retry]"},
    ).status_code == 200
    assert c.put(
        "/api/v1/installations/me/device-token",
        headers=inst_headers,
        json={"platform": "android", "token": "ExpoPushToken[ticket-retry-2]"},
    ).status_code == 200
    assert c.put(
        "/api/v1/installations/me/preferences",
        headers=inst_headers,
        json={"game_ids": ["g_ticket_retry"]},
    ).status_code == 200

    created = c.post(
        "/api/v1/admin/contents",
        headers=admin,
        json={
            "game_id": "g_ticket_retry",
            "kind": "update",
            "title": "티켓 재시도 테스트",
            "official_url": "https://example.com/ticket-retry",
            "status": "draft",
        },
    ).json()
    content_id = created["id"]
    assert c.patch(
        f"/api/v1/admin/contents/{content_id}",
        headers=admin,
        json={"status": "reviewed"},
    ).status_code == 200
    assert c.patch(
        f"/api/v1/admin/contents/{content_id}",
        headers=admin,
        json={"status": "published"},
    ).status_code == 200

    from app.config import get_settings
    from app.services import expo_push

    monkeypatch.setenv("EXPO_PUSH_ENABLED", "true")
    get_settings.cache_clear()
    calls = {"count": 0}

    def rate_limited_then_ok(_messages):
        calls["count"] += 1
        # 폐기 토큰과 일시 오류가 한 batch에 섞여도 남은 토큰은 재시도한다.
        return (
            ["DeviceNotRegistered", "MessageRateExceeded"]
            if calls["count"] == 1
            else [None]
        )

    monkeypatch.setattr(expo_push, "send_messages", rate_limited_then_ok)

    first = c.post("/api/v1/admin/push/dispatch", headers=admin)
    assert first.status_code == 200
    assert first.json()["failed"] == 1
    assert first.json()["sent"] == 0

    second = c.post("/api/v1/admin/push/dispatch", headers=admin)
    assert second.status_code == 200
    assert second.json()["sent"] == 1
    assert second.json()["failed"] == 0
    assert calls["count"] == 2
