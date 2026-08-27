"""LLM 요약 + 자동 발행 + 변화감지 카운터 + dry-run/from-url 흐름."""


def _admin(client):
    c, password = client
    token = c.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": password},
    ).json()["access_token"]
    return c, {"Authorization": f"Bearer {token}"}


def _make_game(c, headers, game_id="g_sum"):
    c.post("/api/v1/admin/games", headers=headers, json={"id": game_id, "name": "SUM GAME"})
    return game_id


def _make_source(c, headers, game_id, **overrides):
    body = {
        "name": "공지 소스",
        "source_type": "rss",
        "game_id": game_id,
        "endpoint_url": "https://feeds.example.com/news.xml",
        "interval_minutes": 30,
        "config": {"kind": "update"},
    }
    body.update(overrides)
    response = c.post("/api/v1/admin/ingest-sources", headers=headers, json=body)
    assert response.status_code == 201, response.text
    return response.json()


def _allow_public_dns(monkeypatch):
    import socket

    real = socket.getaddrinfo

    def resolver(host, port, *args, **kwargs):
        if host.endswith("example.com"):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
        return real(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolver)


def _enable_llm(monkeypatch, result=None, fail=False):
    from app.config import get_settings
    import app.services.summarize_service as summarize

    monkeypatch.setattr(get_settings(), "openai_api_key", "test-key")

    def fake_call(settings, title, text):
        if fail:
            raise summarize.SummarizeError("boom")
        return result or {
            "summary_points": [
                "신규 캐릭터 2종이 추가됩니다",
                "8월 20일 점검 후 적용됩니다",
                "출석 보상이 우편으로 지급됩니다",
            ],
            "kind": "event",
        }

    monkeypatch.setattr(summarize, "call_llm", fake_call)


def test_auto_publish_source_publishes_with_llm_summary(client, monkeypatch) -> None:
    c, headers = _admin(client)
    _allow_public_dns(monkeypatch)
    _enable_llm(monkeypatch)
    game_id = _make_game(c, headers)
    source = _make_source(c, headers, game_id, auto_publish=True)

    ingest_headers = {"X-Ingest-Key": "test-ingest-key"}
    created = c.post(
        "/api/v1/ingest/contents",
        headers=ingest_headers,
        json={
            "source_id": source["id"],
            "game_id": game_id,
            "title": "1.5 업데이트 점검 안내",
            "official_url": "https://example.com/news/1",
            "idempotency_key": "auto-1",
            "raw_text": "8월 20일 점검 후 신규 캐릭터가 추가됩니다. 보상은 우편으로 지급됩니다.",
        },
    )
    assert created.status_code == 201
    assert created.json()["status"] == "draft"  # 응답 시점은 draft, 발행은 백그라운드

    rows = c.get("/api/v1/admin/contents", headers=headers).json()
    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "published"
    assert row["summary_status"] == "done"
    assert row["summary_points"] == [
        "신규 캐릭터 2종이 추가됩니다",
        "8월 20일 점검 후 적용됩니다",
        "출석 보상이 우편으로 지급됩니다",
    ]
    assert row["kind"] == "event"
    assert row["source_id"] == source["id"]
    # 공개 API에도 노출
    assert len(c.get("/api/v1/contents").json()) == 1


def test_summary_failure_keeps_draft_for_review(client, monkeypatch) -> None:
    c, headers = _admin(client)
    _allow_public_dns(monkeypatch)
    _enable_llm(monkeypatch, fail=True)
    game_id = _make_game(c, headers)
    source = _make_source(c, headers, game_id, auto_publish=True)

    c.post(
        "/api/v1/ingest/contents",
        headers={"X-Ingest-Key": "test-ingest-key"},
        json={
            "source_id": source["id"],
            "game_id": game_id,
            "title": "요약 실패 케이스",
            "idempotency_key": "auto-2",
            "raw_text": "본문",
        },
    )
    row = c.get("/api/v1/admin/contents", headers=headers).json()[0]
    assert row["status"] == "draft"
    assert row["summary_status"] == "failed"
    assert c.get("/api/v1/contents").json() == []


def test_no_auto_publish_stays_draft_with_summary(client, monkeypatch) -> None:
    c, headers = _admin(client)
    _allow_public_dns(monkeypatch)
    _enable_llm(monkeypatch)
    game_id = _make_game(c, headers)
    source = _make_source(c, headers, game_id, auto_publish=False)

    c.post(
        "/api/v1/ingest/contents",
        headers={"X-Ingest-Key": "test-ingest-key"},
        json={
            "source_id": source["id"],
            "game_id": game_id,
            "title": "검수 대기 케이스",
            "idempotency_key": "auto-3",
            "raw_text": "본문",
        },
    )
    row = c.get("/api/v1/admin/contents", headers=headers).json()[0]
    assert row["status"] == "draft"
    assert row["summary_status"] == "done"
    assert row["summary_points"] == [
        "신규 캐릭터 2종이 추가됩니다",
        "8월 20일 점검 후 적용됩니다",
        "출석 보상이 우편으로 지급됩니다",
    ]


def test_check_endpoint_reports_existing_keys(client, monkeypatch) -> None:
    c, headers = _admin(client)
    _allow_public_dns(monkeypatch)
    game_id = _make_game(c, headers)
    source = _make_source(c, headers, game_id)

    ingest_headers = {"X-Ingest-Key": "test-ingest-key"}
    c.post(
        "/api/v1/ingest/contents",
        headers=ingest_headers,
        json={
            "source_id": source["id"],
            "game_id": game_id,
            "title": "기존 글",
            "idempotency_key": "known-key",
        },
    )
    checked = c.post(
        "/api/v1/ingest/contents/check",
        headers=ingest_headers,
        json={"source_id": source["id"], "idempotency_keys": ["known-key", "new-key"]},
    )
    assert checked.status_code == 200
    assert checked.json()["existing"] == ["known-key"]


def test_empty_runs_mark_source_quiet_but_not_modified_does_not(client, monkeypatch) -> None:
    c, headers = _admin(client)
    _allow_public_dns(monkeypatch)
    game_id = _make_game(c, headers)
    source = _make_source(c, headers, game_id)
    ingest_headers = {"X-Ingest-Key": "test-ingest-key"}

    def run_cycle(items_seen: int, not_modified: bool):
        c.post(f"/api/v1/admin/ingest-sources/{source['id']}/runs", headers=headers)
        job = c.post("/api/v1/ingest/jobs/claim", headers=ingest_headers).json()
        c.post(
            f"/api/v1/ingest/jobs/{job['run']['id']}/complete",
            headers=ingest_headers,
            json={
                "status": "succeeded",
                "items_seen": items_seen,
                "items_created": 0,
                "not_modified": not_modified,
                "http_cache": {"etag": "abc"},
            },
        )

    # 변화 없음(304)은 경고 대상이 아님
    for _ in range(6):
        run_cycle(items_seen=0, not_modified=True)
    sources = c.get("/api/v1/admin/ingest-sources", headers=headers).json()
    assert sources[0]["health"] == "ok"

    # 페이지는 바뀌는데 0건 파싱이 반복되면 quiet 경고 (셀렉터 깨짐 의심)
    for _ in range(5):
        run_cycle(items_seen=0, not_modified=False)
    sources = c.get("/api/v1/admin/ingest-sources", headers=headers).json()
    assert sources[0]["health"] == "quiet"
    assert sources[0]["consecutive_empty_runs"] == 5

    # 다시 글이 잡히면 정상 복귀
    run_cycle(items_seen=3, not_modified=False)
    sources = c.get("/api/v1/admin/ingest-sources", headers=headers).json()
    assert sources[0]["health"] == "ok"

    # http_cache는 claim에 실려 collector로 돌아간다
    c.post(f"/api/v1/admin/ingest-sources/{source['id']}/runs", headers=headers)
    job = c.post("/api/v1/ingest/jobs/claim", headers=ingest_headers).json()
    assert job["http_cache"] == {"etag": "abc"}


_HTML_PAGE = b"""
<html><head><title>fallback</title>
<meta property="og:title" content="8\xec\x9b\x94 \xec\x97\x85\xeb\x8d\xb0\xec\x9d\xb4\xed\x8a\xb8 \xec\x95\x88\xeb\x82\xb4" />
</head><body>
<article>8\xec\x9b\x94 20\xec\x9d\xbc \xec\xa0\x90\xea\xb2\x80 \xed\x9b\x84 \xec\x8b\xa0\xea\xb7\x9c \xec\xba\x90\xeb\xa6\xad\xed\x84\xb0\xea\xb0\x80 \xec\xb6\x94\xea\xb0\x80\xeb\x90\xa9\xeb\x8b\x88\xeb\x8b\xa4.</article>
<ul class="board">
  <li class="row"><a href="/news/1">\xea\xb3\xb5\xec\xa7\x80 \xed\x95\x98\xeb\x82\x98</a><span class="date">2026.08.10</span></li>
  <li class="row"><a href="/news/2">\xea\xb3\xb5\xec\xa7\x80 \xeb\x91\x98</a><span class="date">2026.08.11</span></li>
</ul>
</body></html>
"""


def test_dry_run_previews_html_source(client, monkeypatch) -> None:
    c, headers = _admin(client)
    import app.services.source_preview_service as preview

    monkeypatch.setattr(preview, "_fetch", lambda url, headers: _HTML_PAGE)
    response = c.post(
        "/api/v1/admin/ingest-sources/dry-run",
        headers=headers,
        json={
            "source_type": "html",
            "endpoint_url": "https://games.example.com/notice",
            "config": {"list_selector": "li.row", "date_selector": "span.date"},
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["warning"] is None
    assert [item["title"] for item in body["items"]] == ["공지 하나", "공지 둘"]
    assert body["items"][0]["url"] == "https://games.example.com/news/1"
    assert body["items"][0]["published_at"] == "2026.08.10"


def test_from_url_quick_add_creates_summarized_draft(client, monkeypatch) -> None:
    c, headers = _admin(client)
    _enable_llm(monkeypatch)
    game_id = _make_game(c, headers)
    import app.services.source_preview_service as preview

    monkeypatch.setattr(preview, "_fetch", lambda url, headers: _HTML_PAGE)
    response = c.post(
        "/api/v1/admin/contents/from-url",
        headers=headers,
        json={"url": "https://games.example.com/news/1", "game_id": game_id, "kind": "update"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == "8월 업데이트 안내"
    assert body["status"] == "draft"
    assert body["summary_status"] == "done"
    assert body["summary_points"] == [
        "신규 캐릭터 2종이 추가됩니다",
        "8월 20일 점검 후 적용됩니다",
        "출석 보상이 우편으로 지급됩니다",
    ]
    assert body["official_url"] == "https://games.example.com/news/1"
    assert body["raw_text_excerpt"]
