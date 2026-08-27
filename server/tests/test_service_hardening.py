"""품질 게이트 · 신뢰도 카운터 · 예약 발행 · 마감 리마인더 · 관리자 통계."""

import json
from datetime import datetime, timedelta, timezone


def _admin(client):
    c, password = client
    token = c.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": password},
    ).json()["access_token"]
    return c, {"Authorization": f"Bearer {token}"}


def _make_game(c, headers, game_id="g_hard"):
    c.post("/api/v1/admin/games", headers=headers, json={"id": game_id, "name": "HARD GAME"})
    return game_id


def _make_source(c, headers, game_id, **overrides):
    body = {
        "name": "공지 소스",
        "source_type": "rss",
        "game_id": game_id,
        "endpoint_url": "https://feeds.example.com/news.xml",
        "interval_minutes": 30,
        "config": {"kind": "update"},
    }
    body.update(overrides)
    response = c.post("/api/v1/admin/ingest-sources", headers=headers, json=body)
    assert response.status_code == 201, response.text
    return response.json()


def _ingest(c, source_id, game_id, *, key, title, points):
    response = c.post(
        "/api/v1/ingest/contents",
        headers={"X-Ingest-Key": "test-ingest-key"},
        json={
            "source_id": source_id,
            "game_id": game_id,
            "title": title,
            "summary_points": points,
            "official_url": "https://example.com/ingest-item",
            "idempotency_key": key,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _get_source(c, headers, source_id):
    rows = c.get("/api/v1/admin/ingest-sources", headers=headers).json()
    return next(s for s in rows if s["id"] == source_id)


def _allow_public_dns(monkeypatch):
    import socket

    real = socket.getaddrinfo

    def resolver(host, port, *args, **kwargs):
        if host.endswith("example.com"):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
        return real(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolver)


def _make_installation(c, game_ids, *, token=None, notifications=None):
    reg = c.post("/api/v1/installations").json()
    inst_headers = {
        "X-Installation-Id": reg["installation_id"],
        "X-Installation-Secret": reg["secret"],
    }
    prefs = {"game_ids": game_ids, "notifications": notifications or {}}
    assert (
        c.put("/api/v1/installations/me/preferences", headers=inst_headers, json=prefs).status_code
        == 200
    )
    if token:
        c.put(
            "/api/v1/installations/me/device-token",
            headers=inst_headers,
            json={"platform": "android", "token": token},
        )
    return reg["installation_id"]


def test_quality_gate_blocks_auto_publish_with_reason(client, monkeypatch) -> None:
    c, headers = _admin(client)
    _allow_public_dns(monkeypatch)
    game_id = _make_game(c, headers)
    source = _make_source(c, headers, game_id, auto_publish=True)

    _ingest(c, source["id"], game_id, key="qg-1", title="점검 안내", points=["짧음"])

    row = c.get("/api/v1/admin/contents", headers=headers).json()[0]
    assert row["status"] == "draft"
    assert row["needs_review_reason"]
    assert "짧" in row["needs_review_reason"]


def test_trust_counters_track_approved_and_edited(client, monkeypatch) -> None:
    c, headers = _admin(client)
    _allow_public_dns(monkeypatch)
    game_id = _make_game(c, headers)
    source = _make_source(c, headers, game_id, auto_publish=False)

    # 무수정 발행 → stat_approved
    first = _ingest(
        c, source["id"], game_id,
        key="tc-1", title="신규 업데이트 공지", points=["신규 콘텐츠가 추가됩니다"],
    )
    for status in ("reviewed", "published"):
        assert (
            c.patch(
                f"/api/v1/admin/contents/{first['id']}",
                headers=headers,
                json={"status": status},
            ).status_code
            == 200
        )
    src = _get_source(c, headers, source["id"])
    assert src["stat_approved"] == 1
    assert src["stat_edited"] == 0

    # 수정 후 발행 → stat_edited
    second = _ingest(
        c, source["id"], game_id,
        key="tc-2", title="이벤트 공지", points=["이벤트 보상이 지급됩니다"],
    )
    c.patch(
        f"/api/v1/admin/contents/{second['id']}",
        headers=headers,
        json={"title": "이벤트 공지 (수정)"},
    )
    for status in ("reviewed", "published"):
        c.patch(
            f"/api/v1/admin/contents/{second['id']}", headers=headers, json={"status": status}
        )
    src = _get_source(c, headers, source["id"])
    assert src["stat_approved"] == 1
    assert src["stat_edited"] == 1


def test_retracting_auto_published_content_demotes_source(client, monkeypatch) -> None:
    c, headers = _admin(client)
    _allow_public_dns(monkeypatch)
    game_id = _make_game(c, headers)
    source = _make_source(c, headers, game_id, auto_publish=True)

    created = _ingest(
        c, source["id"], game_id,
        key="rt-1", title="자동 발행 공지", points=["점검 후 신규 기능이 열립니다"],
    )
    row = c.get("/api/v1/admin/contents", headers=headers).json()[0]
    assert row["status"] == "published"
    assert row["auto_published"] is True

    # 회수 → 소스 강등
    assert (
        c.patch(
            f"/api/v1/admin/contents/{created['id']}",
            headers=headers,
            json={"status": "reviewed"},
        ).status_code
        == 200
    )
    src = _get_source(c, headers, source["id"])
    assert src["auto_publish"] is False
    assert src["stat_retracted"] == 1


def test_scheduled_publish_runs_via_scheduler(client) -> None:
    c, headers = _admin(client)
    game_id = _make_game(c, headers)
    created = c.post(
        "/api/v1/admin/contents",
        headers=headers,
        json={
            "game_id": game_id,
            "kind": "update",
            "title": "예약 발행 공지",
            "summary_points": ["예약된 시각에 자동 발행됩니다"],
            "official_url": "https://example.com/scheduled",
            "status": "draft",
        },
    ).json()
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    c.patch(
        f"/api/v1/admin/contents/{created['id']}",
        headers=headers,
        json={"status": "reviewed", "scheduled_publish_at": past},
    )

    from app.db import SessionLocal
    from app.services.scheduler_service import SchedulerService

    db = SessionLocal()
    try:
        count = SchedulerService(db).publish_scheduled(datetime.now(timezone.utc))
        db.commit()
    finally:
        db.close()
    assert count == 1

    row = c.get("/api/v1/admin/contents", headers=headers).json()[0]
    assert row["status"] == "published"
    assert row["scheduled_publish_at"] is None

    logs = c.get("/api/v1/admin/audit-logs", headers=headers).json()
    assert any(log["actor"] == "scheduler" and log["action"] == "발행" for log in logs)


def test_event_ending_reminder_enqueues_once(client) -> None:
    c, headers = _admin(client)
    game_id = _make_game(c, headers)
    _make_installation(
        c, [game_id], token="ExponentPushToken[test-reminder]",
        notifications={"selected_game_news": False, "event_ending": True},
    )

    ends = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    c.post(
        "/api/v1/admin/contents",
        headers=headers,
        json={
            "game_id": game_id,
            "kind": "event",
            "title": "한정 이벤트",
            "summary_points": ["마감 임박 보상을 받으세요"],
            "official_url": "https://example.com/event",
            "ends_at": ends,
            "status": "published",
        },
    )
    baseline = c.get("/api/v1/admin/push/stats", headers=headers).json()["pending"]

    from app.db import SessionLocal
    from app.services.scheduler_service import SchedulerService

    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        first = SchedulerService(db).send_event_ending_reminders(now)
        db.commit()
        second = SchedulerService(db).send_event_ending_reminders(now)
        db.commit()
    finally:
        db.close()

    assert first == 1
    assert second == 0  # event_reminder_sent_at 로 중복 방지
    stats = c.get("/api/v1/admin/push/stats", headers=headers).json()
    assert stats["pending"] == baseline + 1

    from app.models.entities import PushOutbox

    db = SessionLocal()
    try:
        reminder = db.query(PushOutbox).filter_by(channel="event_ending").one()
        payload = json.loads(reminder.payload_json)
    finally:
        db.close()
    assert payload["game_name"] == "HARD GAME"


def test_popup_and_goods_ending_reminders_are_included(client) -> None:
    """기간 한정 팝업·굿즈도 이벤트 기간 알림 대상이어야 한다."""
    c, headers = _admin(client)
    game_id = _make_game(c, headers)
    _make_installation(
        c,
        [game_id],
        token="ExponentPushToken[test-period-reminder]",
        notifications={"selected_game_news": False, "event_ending": True},
    )

    ends = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    for kind, title in (("popup", "기간 한정 팝업"), ("goods", "기간 한정 굿즈")):
        response = c.post(
            "/api/v1/admin/contents",
            headers=headers,
            json={
                "game_id": game_id,
                "kind": kind,
                "title": title,
                "summary_points": ["마감 전에 확인하세요"],
                "official_url": f"https://example.com/{kind}",
                "ends_at": ends,
                "status": "published",
            },
        )
        assert response.status_code == 201

    from app.db import SessionLocal
    from app.services.scheduler_service import SchedulerService

    db = SessionLocal()
    try:
        count = SchedulerService(db).send_event_ending_reminders(datetime.now(timezone.utc))
        db.commit()
    finally:
        db.close()

    assert count == 2


def test_admin_stats_and_audit_endpoints(client) -> None:
    c, headers = _admin(client)
    game_id = _make_game(c, headers)
    _make_installation(c, [game_id], token="ExponentPushToken[stat-1]")
    _make_installation(c, [game_id])

    users = c.get("/api/v1/admin/stats/users", headers=headers).json()
    assert users["installations"] == 2
    assert users["with_device_token"] == 1
    assert users["top_games"][0]["game_id"] == game_id
    assert users["top_games"][0]["pick_count"] == 2

    push = c.get("/api/v1/admin/push/stats", headers=headers).json()
    assert set(push) == {"pending", "sent", "failed", "last_sent_at"}

    logs = c.get("/api/v1/admin/audit-logs", headers=headers).json()
    assert any(log["action"] == "게임 등록" and log["entity_id"] == game_id for log in logs)


def test_scheduler_does_not_fetch_private_or_redirected_links(client, monkeypatch) -> None:
    """데드링크 점검이 오염된 원문 URL로 SSRF를 일으키지 않는다."""
    c, headers = _admin(client)
    game_id = _make_game(c, headers, game_id="g_link_guard")
    created = c.post(
        "/api/v1/admin/contents",
        headers=headers,
        json={
            "game_id": game_id,
            "kind": "update",
            "title": "내부 주소가 섞인 공지",
            "summary_points": ["검수용"],
            "official_url": "http://127.0.0.1/private",
            "status": "published",
        },
    )
    assert created.status_code == 201, created.text

    import app.services.scheduler_service as scheduler

    class FakeClient:
        def __init__(self, *args, **kwargs):
            assert kwargs["follow_redirects"] is False

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def head(self, _url):
            raise AssertionError("private link must be rejected before HTTP")

    monkeypatch.setattr(scheduler.httpx, "Client", FakeClient)
    from app.db import SessionLocal
    from app.services.scheduler_service import SchedulerService

    db = SessionLocal()
    try:
        assert SchedulerService(db).check_dead_links() == 0
    finally:
        db.close()
