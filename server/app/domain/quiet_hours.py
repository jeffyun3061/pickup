"""조용시간 계산 — 심야 푸시는 다음 아침으로 미룬다 (알림 해제 방지)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def resolve_available_at(
    now_utc: datetime,
    *,
    start_hour: int,
    end_hour: int,
    utc_offset_hours: int,
) -> datetime:
    """
    now_utc가 현지 조용시간(start_hour~end_hour)에 들면 다음 end_hour 정각(UTC 환산)을,
    아니면 now_utc를 그대로 돌려준다. start_hour == end_hour이면 조용시간 없음.
    """
    if start_hour == end_hour:
        return now_utc

    local_tz = timezone(timedelta(hours=utc_offset_hours))
    local = now_utc.astimezone(local_tz)

    if start_hour > end_hour:
        # 자정을 걸치는 구간 (예: 23시~08시)
        in_quiet = local.hour >= start_hour or local.hour < end_hour
    else:
        in_quiet = start_hour <= local.hour < end_hour

    if not in_quiet:
        return now_utc

    release = local.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    if release <= local:
        release += timedelta(days=1)
    return release.astimezone(timezone.utc)
