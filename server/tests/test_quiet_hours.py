from datetime import datetime, timezone

from app.domain.quiet_hours import resolve_available_at


def _utc(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, 14, hour, minute, tzinfo=timezone.utc)


def test_daytime_passes_through() -> None:
    # KST 15:00 (UTC 06:00) — 조용시간 아님
    now = _utc(6)
    assert resolve_available_at(now, start_hour=23, end_hour=8, utc_offset_hours=9) == now


def test_late_night_deferred_to_morning() -> None:
    # KST 23:30 (UTC 14:30) → 다음날 KST 08:00 (UTC 23:00 당일)
    now = _utc(14, 30)
    out = resolve_available_at(now, start_hour=23, end_hour=8, utc_offset_hours=9)
    assert out == datetime(2026, 8, 14, 23, 0, tzinfo=timezone.utc)


def test_early_morning_deferred_to_same_morning() -> None:
    # KST 03:00 (UTC 전날 18:00) → 같은 날 KST 08:00 (UTC 23:00 전날)
    now = datetime(2026, 8, 13, 18, 0, tzinfo=timezone.utc)
    out = resolve_available_at(now, start_hour=23, end_hour=8, utc_offset_hours=9)
    assert out == datetime(2026, 8, 13, 23, 0, tzinfo=timezone.utc)


def test_disabled_when_start_equals_end() -> None:
    now = _utc(14, 30)
    assert resolve_available_at(now, start_hour=0, end_hour=0, utc_offset_hours=9) == now
