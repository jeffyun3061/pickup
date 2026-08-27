"""
목록 페이지 변화감지.

1) 조건부 GET: 지난 응답의 ETag/Last-Modified를 실어 보내고 304면 본문 없이 종료.
2) 본문 해시: 조건부 GET 미지원 사이트는 응답 해시가 지난번과 같으면 파싱을 건너뛴다.

해시는 best-effort다(조회수 등 노이즈로 매번 달라질 수 있음). 최종 중복 방어는
아이템 단위 idempotency_key가 담당한다.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import httpx

from collector.connectors.base import checked_body


@dataclass(frozen=True)
class GuardResult:
    unchanged: bool
    cache: dict[str, str]
    body: bytes = field(default=b"", repr=False)


def guarded_get(
    client: httpx.Client,
    url: str,
    cache: dict[str, str],
    headers: dict[str, str] | None = None,
) -> GuardResult:
    request_headers = dict(headers or {})
    if cache.get("etag"):
        request_headers["If-None-Match"] = cache["etag"]
    if cache.get("last_modified"):
        request_headers["If-Modified-Since"] = cache["last_modified"]

    response = client.get(url, headers=request_headers)
    if response.status_code == 304:
        return GuardResult(unchanged=True, cache=dict(cache))

    body = checked_body(response)
    digest = hashlib.sha256(body).hexdigest()
    new_cache: dict[str, str] = {"body_sha256": digest}
    if response.headers.get("etag"):
        new_cache["etag"] = response.headers["etag"]
    if response.headers.get("last-modified"):
        new_cache["last_modified"] = response.headers["last-modified"]

    if cache.get("body_sha256") == digest:
        return GuardResult(unchanged=True, cache=new_cache)
    return GuardResult(unchanged=False, cache=new_cache, body=body)
