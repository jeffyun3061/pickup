from __future__ import annotations

import argparse
import os
import sys
import time
from urllib.parse import urlsplit

import httpx

from collector.client import IngestApiClient
from collector.connectors import ApiConnector, HtmlConnector, RssConnector
from collector.detail import fetch_raw_text
from collector.fetch_guard import guarded_get
from collector.models import Job
from collector.normalizer import to_ingest_payload
from collector.rendered_html import RenderedHtmlFetcher, rendered_items_cache
from collector.robots import DEFAULT_USER_AGENT, RobotsGate
from collector.security import assert_public_source_url

_CONNECTORS = {
    "rss": RssConnector(),
    "api": ApiConnector(),
    "html": HtmlConnector(),
}

# 첫 수집처럼 새 글이 몰려도 상세 fetch는 최신 N건까지만 (상대 서버 예의)
_DEFAULT_DETAIL_BUDGET = 10
_DEFAULT_FETCH_DELAY_SECONDS = 1.0


def _user_agent() -> str:
    return os.environ.get("COLLECTOR_USER_AGENT", DEFAULT_USER_AGENT)


def _is_enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _control_plane_url() -> str:
    """collector가 연결할 API 주소를 검증해 조용한 localhost 오접속을 막는다."""
    raw = os.environ.get("INGEST_SERVER_URL", "").strip()
    if not raw:
        raise SystemExit("INGEST_SERVER_URL is required")
    parsed = urlsplit(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SystemExit("INGEST_SERVER_URL must be an absolute http(s) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise SystemExit("INGEST_SERVER_URL must not contain credentials, query, or fragment")
    return raw.rstrip("/")


def _process_job(
    api: IngestApiClient,
    job: Job,
    rendered_fetcher: RenderedHtmlFetcher | None = None,
) -> tuple[int, int, bool, dict[str, str]]:
    source = job.source
    connector = _CONNECTORS.get(source.source_type)
    if connector is None:
        raise RuntimeError(f"Unsupported source_type: {source.source_type}")

    secret = None
    if source.secret_env_name:
        secret = os.environ.get(source.secret_env_name)
        if not secret:
            raise RuntimeError(f"Required source secret is missing: {source.secret_env_name}")

    assert_public_source_url(source.endpoint_url)

    with httpx.Client(
        timeout=20.0,
        follow_redirects=False,
        headers={"User-Agent": _user_agent()},
    ) as external:
        robots = RobotsGate(external, _user_agent())

        # HTML 목록 크롤만 robots 대상. RSS/JSON 피드는 구독용 인터페이스 (ADR-012)
        if source.source_type == "html" and not robots.allowed(source.endpoint_url):
            raise RuntimeError(f"robots_blocked: {source.endpoint_url}")

        if source.source_type == "html" and _is_enabled(source.config.get("render_js")):
            if rendered_fetcher is None:
                raise RuntimeError("render_js source requires a rendered HTML fetcher")
            try:
                timeout = float(source.config.get("render_timeout_seconds", "20"))
            except ValueError:
                timeout = 20.0
            body = rendered_fetcher.fetch(
                source.endpoint_url,
                wait_selector=source.config.get("wait_selector", ""),
                timeout_seconds=timeout,
            )
            items = connector.parse(body, source)
            rendered_cache = rendered_items_cache(items)
            if (
                source.http_cache.get("rendered_items_sha256")
                == rendered_cache["rendered_items_sha256"]
            ):
                return 0, 0, True, rendered_cache
            next_cache = rendered_cache
        else:
            guarded = guarded_get(
                external,
                source.endpoint_url,
                source.http_cache,
                connector.request_headers(source, secret),
            )
            if guarded.unchanged:
                return 0, 0, True, guarded.cache
            items = connector.parse(guarded.body, source)
            next_cache = guarded.cache
        payloads = [to_ingest_payload(source, item) for item in items]
        existing = api.check_existing(
            source.id, [str(payload["idempotency_key"]) for payload in payloads]
        )

        detail_budget = min(
            max(int(source.config.get("max_detail_fetches", str(_DEFAULT_DETAIL_BUDGET))), 0),
            50,
        )
        try:
            fetch_delay = max(
                float(source.config.get("fetch_delay_seconds", str(_DEFAULT_FETCH_DELAY_SECONDS))),
                0.0,
            )
        except ValueError:
            fetch_delay = _DEFAULT_FETCH_DELAY_SECONDS
        wants_detail = source.config.get("fetch_detail", "true").lower() != "false"

        created = 0
        for item, payload in zip(items, payloads):
            if payload["idempotency_key"] in existing:
                continue
            if wants_detail and detail_budget > 0 and item.url:
                raw_text = fetch_raw_text(external, item.url, source.config, robots)
                detail_budget -= 1
                if raw_text:
                    payload = to_ingest_payload(source, item, raw_text)
                if fetch_delay:
                    time.sleep(fetch_delay)
            for attempt in range(3):
                try:
                    result = api.submit(payload)
                    if result.get("created", True):
                        created += 1
                    break
                except (httpx.HTTPError, OSError):
                    if attempt == 2:
                        raise
                    time.sleep(2**attempt)
        return len(items), created, False, next_cache


def run_once(
    api: IngestApiClient,
    rendered_fetcher: RenderedHtmlFetcher | None = None,
) -> bool:
    job = api.claim()
    if job is None:
        return False

    try:
        seen, created, not_modified, http_cache = _process_job(
            api, job, rendered_fetcher
        )
        api.complete(
            job.run_id,
            status="succeeded",
            items_seen=seen,
            items_created=created,
            not_modified=not_modified,
            http_cache=http_cache,
        )
    except Exception as exc:
        api.complete(
            job.run_id,
            status="failed",
            items_seen=0,
            items_created=0,
            error=str(exc)[:1000],
            http_cache=job.source.http_cache or None,
        )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="GamePickup RSS/API/HTML collector")
    parser.add_argument("--once", action="store_true", help="작업 하나를 처리하고 종료")
    parser.add_argument("--poll-seconds", type=float, default=10.0)
    args = parser.parse_args()

    key = os.environ.get("INGEST_API_KEY")
    if not key:
        raise SystemExit("INGEST_API_KEY is required")
    api = IngestApiClient(_control_plane_url(), key)
    rendered_fetcher = RenderedHtmlFetcher(_user_agent())
    try:
        if args.once:
            run_once(api, rendered_fetcher)
            return
        while True:
            try:
                worked = run_once(api, rendered_fetcher)
                time.sleep(0 if worked else args.poll_seconds)
            except (httpx.HTTPError, OSError) as exc:
                print(f"collector control-plane error: {exc}", file=sys.stderr)
                time.sleep(args.poll_seconds)
    finally:
        rendered_fetcher.close()
        api.close()


if __name__ == "__main__":
    main()
