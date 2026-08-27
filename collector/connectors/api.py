from __future__ import annotations

import json
from typing import Any

import httpx

from collector.connectors.base import checked_body
from collector.models import CollectedItem, Source


def _path(value: Any, dotted: str) -> Any:
    current = value
    if not dotted:
        return current
    for part in dotted.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            current = current[index] if index < len(current) else None
        else:
            return None
    return current


class ApiConnector:
    @staticmethod
    def request_headers(source: Source, secret: str | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if secret:
            header = source.config.get("auth_header", "Authorization")
            prefix = source.config.get("auth_prefix", "Bearer")
            headers[header] = f"{prefix} {secret}".strip()
        return headers

    def collect(
        self,
        client: httpx.Client,
        source: Source,
        secret: str | None = None,
    ) -> list[CollectedItem]:
        response = client.get(source.endpoint_url, headers=self.request_headers(source, secret))
        return self.parse(checked_body(response), source)

    def parse(self, body: bytes, source: Source) -> list[CollectedItem]:
        config = source.config
        payload = json.loads(body)
        raw_items = _path(payload, config.get("items_path", ""))
        if not isinstance(raw_items, list):
            raise ValueError("Configured items_path did not resolve to a list")

        result: list[CollectedItem] = []
        for raw in raw_items:
            if not isinstance(raw, dict):
                continue
            external_id = _path(raw, config.get("id_field", "id"))
            title = _path(raw, config.get("title_field", "title"))
            url = _path(raw, config.get("url_field", "url"))
            if external_id is None or not title:
                continue
            result.append(
                CollectedItem(
                    external_id=str(external_id),
                    title=str(title),
                    url=str(url or ""),
                    summary=str(_path(raw, config.get("summary_field", "summary")) or ""),
                    image_url=str(_path(raw, config.get("image_field", "image_url")) or "") or None,
                    published_at=str(
                        _path(raw, config.get("published_field", "published_at")) or ""
                    )
                    or None,
                )
            )
        limit = min(max(int(config.get("max_items", "100")), 1), 500)
        return result[:limit]
