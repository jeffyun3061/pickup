"""수집 소스의 현지 활성시간 계산."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Mapping


def _hour(config: Mapping[str, object], key: str) -> int | None:
    value = config.get(key)
    if value is None or str(value).strip() == "":
        return None
    try:
        hour = int(str(value))
    except ValueError:
        return None
    return hour if 0 <= hour <= 23 else None


def _offset(config: Mapping[str, object]) -> int:
    try:
        value = int(str(config.get("utc_offset_hours", "0")))
    except ValueError:
        return 0
    return value if -12 <= value <= 14 else 0


def resolve_active_run_at(
    candidate_utc: datetime,
    config: Mapping[str, object],
) -> datetime:
    """비활성 시간의 후보를 다음 현지 active_start_hour 정각으로 미룬다.

    활성시간 설정이 없거나 시작과 종료가 같으면 하루 종일 활성으로 취급한다.
    """
    start_hour = _hour(config, "active_start_hour")
    end_hour = _hour(config, "active_end_hour")
    if start_hour is None or end_hour is None or start_hour == end_hour:
        return candidate_utc

    local_tz = timezone(timedelta(hours=_offset(config)))
    local = candidate_utc.astimezone(local_tz)
    if start_hour < end_hour:
        active = start_hour <= local.hour < end_hour
    else:
        active = local.hour >= start_hour or local.hour < end_hour
    if active:
        return candidate_utc

    release = local.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    if local.hour >= end_hour and start_hour < end_hour:
        release += timedelta(days=1)
    elif start_hour > end_hour and end_hour <= local.hour < start_hour:
        # 자정을 걸친 활성 구간의 낮 휴지시간
        pass
    elif release <= local:
        release += timedelta(days=1)
    return release.astimezone(timezone.utc)


def next_source_run(
    now_utc: datetime,
    interval_minutes: int,
    config: Mapping[str, object],
) -> datetime:
    return resolve_active_run_at(
        now_utc + timedelta(minutes=interval_minutes),
        config,
    )
