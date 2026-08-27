from __future__ import annotations

from typing import Any

import httpx

from collector.models import Job, Source


class IngestApiClient:
    def __init__(self, base_url: str, ingest_key: str, timeout: float = 20.0) -> None:
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"X-Ingest-Key": ingest_key},
        )

    def close(self) -> None:
        self._client.close()

    def claim(self) -> Job | None:
        response = self._client.post("/api/v1/ingest/jobs/claim")
        response.raise_for_status()
        body = response.json()
        if body is None:
            return None
        source = body["source"]
        return Job(
            run_id=body["run"]["id"],
            source=Source(
                id=source["id"],
                source_type=source["source_type"],
                game_id=source["game_id"],
                endpoint_url=source["endpoint_url"],
                config=source.get("config") or {},
                secret_env_name=source.get("secret_env_name"),
                http_cache=body.get("http_cache") or {},
            ),
        )

    def check_existing(self, source_id: str, idempotency_keys: list[str]) -> set[str]:
        """이미 수집된 아이템 키 집합. 새 글에만 상세 fetch·제출을 하기 위한 사전 조회."""
        if not idempotency_keys:
            return set()
        response = self._client.post(
            "/api/v1/ingest/contents/check",
            json={"source_id": source_id, "idempotency_keys": idempotency_keys},
        )
        response.raise_for_status()
        return set(response.json().get("existing", []))

    def submit(self, payload: dict[str, object]) -> dict[str, Any]:
        response = self._client.post("/api/v1/ingest/contents", json=payload)
        response.raise_for_status()
        return response.json()

    def complete(
        self,
        run_id: str,
        *,
        status: str,
        items_seen: int,
        items_created: int,
        error: str | None = None,
        not_modified: bool = False,
        http_cache: dict[str, str] | None = None,
    ) -> None:
        response = self._client.post(
            f"/api/v1/ingest/jobs/{run_id}/complete",
            json={
                "status": status,
                "items_seen": items_seen,
                "items_created": items_created,
                "error": error,
                "not_modified": not_modified,
                "http_cache": http_cache,
            },
        )
        response.raise_for_status()
