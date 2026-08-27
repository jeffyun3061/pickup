from datetime import datetime, timezone

from app.domain.source_schedule import next_source_run, resolve_active_run_at


CONFIG = {
    "active_start_hour": "8",
    "active_end_hour": "22",
    "utc_offset_hours": "9",
}
def test_active_hour_boundaries_kst():
    at_0759 = datetime(2026, 8, 24, 22, 59, tzinfo=timezone.utc)
    at_0800 = datetime(2026, 8, 24, 23, 0, tzinfo=timezone.utc)
    at_2159 = datetime(2026, 8, 25, 12, 59, tzinfo=timezone.utc)
    at_2200 = datetime(2026, 8, 25, 13, 0, tzinfo=timezone.utc)

    assert resolve_active_run_at(at_0759, CONFIG) == at_0800
    assert resolve_active_run_at(at_0800, CONFIG) == at_0800
    assert resolve_active_run_at(at_2159, CONFIG) == at_2159
    assert resolve_active_run_at(at_2200, CONFIG) == datetime(
        2026, 8, 25, 23, 0, tzinfo=timezone.utc
    )


def test_next_interval_crossing_end_moves_to_next_morning():
    at_2145 = datetime(2026, 8, 25, 12, 45, tzinfo=timezone.utc)
    assert next_source_run(at_2145, 30, CONFIG) == datetime(
        2026, 8, 25, 23, 0, tzinfo=timezone.utc
    )


def test_missing_or_equal_active_hours_means_all_day():
    now = datetime(2026, 8, 25, 13, 0, tzinfo=timezone.utc)
    assert resolve_active_run_at(now, {}) == now
    assert resolve_active_run_at(
        now, {"active_start_hour": "8", "active_end_hour": "8"}
    ) == now


def test_manual_pending_run_bypasses_active_hours(client, monkeypatch):
    c, password = client
    token = c.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": password},
    ).json()["access_token"]
    admin = {"Authorization": f"Bearer {token}"}
    c.post(
        "/api/v1/admin/games",
        headers=admin,
        json={"id": "g_manual_night", "name": "MANUAL NIGHT"},
    )

    import app.services.ingest_service as ingest_module

    real_datetime = ingest_module.datetime

    class NightDateTime(real_datetime):
        @classmethod
        def now(cls, tz=None):
            value = real_datetime(2026, 8, 25, 13, 0, tzinfo=timezone.utc)
            return value if tz is None else value.astimezone(tz)

    monkeypatch.setattr(ingest_module, "datetime", NightDateTime)
    source = c.post(
        "/api/v1/admin/ingest-sources",
        headers=admin,
        json={
            "name": "야간 수동 테스트",
            "source_type": "rss",
            "game_id": "g_manual_night",
            "endpoint_url": "https://example.com/feed.xml",
            "enabled": False,
            "config": CONFIG,
        },
    ).json()
    c.post(
        f"/api/v1/admin/ingest-sources/{source['id']}/runs",
        headers=admin,
    )
    claimed = c.post(
        "/api/v1/ingest/jobs/claim",
        headers={"X-Ingest-Key": "test-ingest-key"},
    )
    assert claimed.status_code == 200
    assert claimed.json()["source"]["id"] == source["id"]
