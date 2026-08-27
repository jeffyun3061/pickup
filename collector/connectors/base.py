from __future__ import annotations

from typing import Protocol

import httpx

from collector.models import CollectedItem, Source

MAX_RESPONSE_BYTES = 5 * 1024 * 1024


class Connector(Protocol):
    def collect(
        self,
        client: httpx.Client,
        source: Source,
        secret: str | None,
    ) -> list[CollectedItem]: ...


def checked_body(response: httpx.Response) -> bytes:
    response.raise_for_status()
    length = int(response.headers.get("content-length", "0") or 0)
    if length > MAX_RESPONSE_BYTES or len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("Source response exceeds 5 MB")
    return response.content
