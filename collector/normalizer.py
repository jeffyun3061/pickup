from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from collector.models import CollectedItem, Source

_TAGS = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")
_DATE_ONLY = re.compile(r"(\d{4})[.\-/]\s?(\d{1,2})[.\-/]\s?(\d{1,2})")

MAX_RAW_TEXT_CHARS = 8000


def clean_text(value: str) -> str:
    return _SPACE.sub(" ", html.unescape(_TAGS.sub(" ", value))).strip()


def parse_published_at(value: str | None) -> str | None:
    """RFC822(RSS)·ISO8601·YYYY.MM.DD 등 흔한 표기를 ISO 문자열로 정규화. 실패 시 None."""
    if not value:
        return None
    raw = value.strip()
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed is not None:
            return parsed.isoformat()
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).isoformat()
    except ValueError:
        pass
    match = _DATE_ONLY.search(raw)
    if match:
        year, month, day = (int(part) for part in match.groups())
        try:
            return datetime(year, month, day, tzinfo=timezone.utc).isoformat()
        except ValueError:
            return None
    return None


def to_ingest_payload(
    source: Source,
    item: CollectedItem,
    raw_text: str | None = None,
) -> dict[str, object]:
    summary = clean_text(item.summary)
    points = [part.strip() for part in re.split(r"(?<=[.!?。])\s+", summary) if part.strip()]
    # 수집기는 기존 운영 초안과의 호환성을 위해 출처 타입과 외부 ID만
    # 안정 키로 만든다. 최종 저장 시 서버가 source_id를 해시 앞에 붙여
    # 서로 다른 소스에서 같은 guid를 써도 충돌하지 않게 스코프를 보장한다.
    stable = f"{source.source_type}:{item.external_id}"
    key = hashlib.sha256(stable.encode("utf-8")).hexdigest()
    kind = source.config.get("kind", "update")
    if kind not in {"update", "event", "popup", "goods"}:
        kind = "update"
    payload: dict[str, object] = {
        "source_id": source.id,
        "game_id": source.game_id,
        "kind": kind,
        "title": clean_text(item.title)[:240],
        "summary_points": points[:3] or ([summary[:300]] if summary else []),
        "official_url": item.url[:500],
        "image_url": item.image_url,
        "idempotency_key": key,
    }
    origin_published_at = parse_published_at(item.published_at)
    if origin_published_at:
        payload["origin_published_at"] = origin_published_at
    text = (raw_text or "").strip() or summary
    if text:
        payload["raw_text"] = text[:MAX_RAW_TEXT_CHARS]
    return payload
