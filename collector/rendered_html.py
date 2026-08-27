"""JavaScript 렌더링이 필요한 공개 HTML 목록 수집.

브라우저는 지연 생성해 collector 프로세스에서 재사용하고, 작업마다 격리된 context를
사용한다. 로그인·쿠키·차단 우회는 하지 않으며 이미지/미디어/폰트는 내려받지 않는다.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

from collector.connectors.base import MAX_RESPONSE_BYTES
from collector.models import CollectedItem
from collector.security import assert_public_source_url


def rendered_items_cache(items: Sequence[CollectedItem]) -> dict[str, str]:
    """동적 페이지의 안정 필드만 해시해 조회수·광고 같은 렌더 노이즈를 제거한다."""
    stable = [
        {
            "external_id": item.external_id,
            "title": item.title,
            "published_at": item.published_at or "",
        }
        for item in items
    ]
    encoded = json.dumps(
        stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {"rendered_items_sha256": hashlib.sha256(encoded).hexdigest()}


class RenderedHtmlFetcher:
    def __init__(self, user_agent: str) -> None:
        self._user_agent = user_agent
        self._playwright = None
        self._browser = None

    def _ensure_browser(self):
        if self._browser is not None:
            return self._browser
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - 배포 설정 오류 안내
            raise RuntimeError(
                "render_js requires playwright; install collector requirements"
            ) from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage"],
        )
        return self._browser

    def fetch(
        self,
        url: str,
        *,
        wait_selector: str,
        timeout_seconds: float = 20.0,
    ) -> bytes:
        assert_public_source_url(url)
        timeout_ms = max(1_000, min(int(timeout_seconds * 1_000), 60_000))
        browser = self._ensure_browser()
        context = browser.new_context(
            user_agent=self._user_agent,
            java_script_enabled=True,
            service_workers="block",
        )
        page = context.new_page()

        def route_request(route) -> None:
            request = route.request
            if request.resource_type in {"image", "media", "font"}:
                route.abort()
                return
            if request.is_navigation_request():
                try:
                    assert_public_source_url(request.url)
                except (OSError, ValueError):
                    route.abort()
                    return
            route.continue_()

        page.route("**/*", route_request)
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            if response is None:
                raise RuntimeError("rendered page returned no navigation response")
            if response.status >= 400:
                raise RuntimeError(f"rendered page HTTP {response.status}")
            if wait_selector:
                page.wait_for_selector(wait_selector, state="attached", timeout=timeout_ms)
            body = page.content().encode("utf-8")
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError("Rendered source response exceeds 5 MB")
            return body
        finally:
            context.close()

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self) -> RenderedHtmlFetcher:
        return self

    def __exit__(self, *_args) -> None:
        self.close()
