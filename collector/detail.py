"""
새 아이템에 한해 상세 페이지 본문을 수집한다 (LLM 요약 입력용 raw_text).

- 기존 아이템은 idempotency 체크로 걸러진 뒤라 절대 다시 fetch하지 않는다.
- robots.txt 허용 + 공개 URL(SSRF 방지) 검사를 통과해야 한다.
- 실패하면 None을 돌려주고 목록의 summary로 폴백한다.
"""

from __future__ import annotations

import httpx
from selectolax.parser import HTMLParser

from collector.connectors.base import checked_body
from collector.robots import RobotsGate
from collector.security import assert_public_source_url

MAX_RAW_TEXT_CHARS = 8000
_STRIP_TAGS = ("script", "style", "noscript", "nav", "header", "footer", "iframe", "svg")


def extract_text(body: bytes, detail_selector: str | None = None) -> str:
    tree = HTMLParser(body)
    tree.strip_tags(list(_STRIP_TAGS))
    node = None
    if detail_selector:
        node = tree.css_first(detail_selector)
    if node is None:
        node = (
            tree.css_first("article")
            or tree.css_first("main")
            or tree.css_first("body")
            or tree.root
        )
    if node is None:
        return ""
    text = " ".join(node.text(separator=" ").split())
    return text[:MAX_RAW_TEXT_CHARS]


def fetch_raw_text(
    client: httpx.Client,
    url: str,
    config: dict[str, str],
    robots: RobotsGate,
) -> str | None:
    if not url:
        return None
    try:
        assert_public_source_url(url)
    except (ValueError, OSError):
        return None
    if not robots.allowed(url):
        return None
    try:
        response = client.get(url, headers={"Accept": "text/html,application/xhtml+xml"})
        body = checked_body(response)
    except (httpx.HTTPError, ValueError):
        return None
    text = extract_text(body, config.get("detail_selector"))
    return text or None
