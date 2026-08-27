"""HTML 커넥터 · 변화감지(fetch_guard) · robots 게이트 · 본문 추출 · 정규화 확장."""

import httpx

from collector.connectors import HtmlConnector
from collector.detail import extract_text, fetch_raw_text
from collector.fetch_guard import guarded_get
from collector.models import CollectedItem, Source
from collector.normalizer import parse_published_at, to_ingest_payload
from collector.rendered_html import rendered_items_cache
from collector.robots import RobotsGate

_LIST_HTML = b"""
<html><body>
<ul class="board">
  <li class="row">
    <a href="/news/101">8\xec\x9b\x94 \xec\x97\x85\xeb\x8d\xb0\xec\x9d\xb4\xed\x8a\xb8</a>
    <span class="date">2026-08-10</span>
    <p class="desc">\xec\x8b\xa0\xea\xb7\x9c \xec\xba\x90\xeb\xa6\xad\xed\x84\xb0</p>
  </li>
  <li class="row">
    <a href="https://games.example.com/news/102">\xec\xa0\x90\xea\xb2\x80 \xec\x95\x88\xeb\x82\xb4</a>
    <span class="date">2026-08-11</span>
  </li>
  <li class="row"><span>\xeb\xa7\x81\xed\x81\xac \xec\x97\x86\xec\x9d\x8c</span></li>
</ul>
</body></html>
"""


def _html_source(**config) -> Source:
    base = {"list_selector": "li.row"}
    base.update(config)
    return Source("src-h", "html", "g-1", "https://games.example.com/notice", base)


def test_html_connector_parses_list_with_selectors():
    source = _html_source(date_selector="span.date", summary_selector="p.desc")
    items = HtmlConnector().parse(_LIST_HTML, source)
    assert len(items) == 2  # 링크 없는 행은 제외
    assert items[0].title == "8월 업데이트"
    assert items[0].url == "https://games.example.com/news/101"  # 상대경로 해석
    assert items[0].external_id == items[0].url
    assert items[0].summary == "신규 캐릭터"
    assert items[0].published_at == "2026-08-10"
    assert items[1].url == "https://games.example.com/news/102"


def test_html_connector_requires_list_selector():
    source = Source("src-h", "html", "g-1", "https://games.example.com/notice", {})
    try:
        HtmlConnector().parse(_LIST_HTML, source)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_rendered_news_markup_parses_without_images():
    body = """
    <ul class="investment_con_list">
      <li>
        <a href="./newsdetail.html?content_id=abc&amp;sid=494">
          <div class="news_label">중요</div>
          <div class="news_list">
            <p><span>08-13</span><span>8월 13일 업데이트 공지</span></p>
            <p>점검 완료와 신규 콘텐츠 안내입니다.</p>
          </div>
        </a>
      </li>
    </ul>
    """.encode()
    source = Source(
        "src-nikke",
        "html",
        "nikke",
        "https://nikke-kr.com/news.html?sid=494",
        {
            "list_selector": ".investment_con_list li",
            "title_selector": ".news_list p:first-child span:nth-child(2)",
            "date_selector": ".news_list p:first-child span:first-child",
            "summary_selector": ".news_list p:nth-child(2)",
        },
    )
    items = HtmlConnector().parse(body, source)
    assert len(items) == 1
    assert items[0].title == "8월 13일 업데이트 공지"
    assert items[0].published_at == "08-13"
    assert items[0].image_url is None
    assert "content_id=abc" in items[0].external_id


def test_rendered_items_cache_uses_stable_fields_only():
    original = CollectedItem("id-1", "공지", "https://example.com/1", "첫 요약")
    changed_summary = CollectedItem(
        "id-1", "공지", "https://example.com/1", "페이지 노이즈가 섞인 요약"
    )
    changed_title = CollectedItem("id-1", "수정 공지", "https://example.com/1", "첫 요약")

    assert rendered_items_cache([original]) == rendered_items_cache([changed_summary])
    assert rendered_items_cache([original]) != rendered_items_cache([changed_title])


def _transport(responses: list[httpx.Response]) -> httpx.MockTransport:
    calls = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        return next(calls)

    return httpx.MockTransport(handler)


def test_guarded_get_uses_etag_and_returns_unchanged_on_304():
    with httpx.Client(
        transport=_transport(
            [httpx.Response(200, content=b"body-1", headers={"etag": 'W/"v1"'})]
        )
    ) as client:
        first = guarded_get(client, "https://example.com/list", {})
    assert first.unchanged is False
    assert first.cache["etag"] == 'W/"v1"'

    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["if_none_match"] = request.headers.get("If-None-Match")
        return httpx.Response(304)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        second = guarded_get(client, "https://example.com/list", first.cache)
    assert captured["if_none_match"] == 'W/"v1"'
    assert second.unchanged is True


def test_guarded_get_detects_same_body_hash_without_etag():
    with httpx.Client(
        transport=_transport(
            [httpx.Response(200, content=b"same"), httpx.Response(200, content=b"same")]
        )
    ) as client:
        first = guarded_get(client, "https://example.com/list", {})
        second = guarded_get(client, "https://example.com/list", first.cache)
    assert first.unchanged is False
    assert second.unchanged is True  # 조건부 GET 미지원이어도 해시로 파싱 스킵


def test_robots_gate_blocks_disallowed_paths():
    robots_txt = b"User-agent: *\nDisallow: /private/\n"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/robots.txt"
        return httpx.Response(200, content=robots_txt)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        gate = RobotsGate(client)
        assert gate.allowed("https://example.com/news/1") is True
        assert gate.allowed("https://example.com/private/1") is False


def test_robots_gate_allows_when_missing():
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(404))
    ) as client:
        assert RobotsGate(client).allowed("https://example.com/anything") is True


def test_robots_gate_blocks_explicit_access_denial():
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(403))
    ) as client:
        assert RobotsGate(client).allowed("https://example.com/anything") is False


def test_extract_text_prefers_article_and_strips_noise():
    html = (
        b"<html><body><script>var x=1;</script><nav>menu</nav>"
        b"<article>Patch notes body. More details.</article></body></html>"
    )
    assert extract_text(html) == "Patch notes body. More details."


def test_fetch_raw_text_skips_robots_blocked(monkeypatch):
    import socket

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, content=b"User-agent: *\nDisallow: /\n")
        return httpx.Response(200, content=b"<article>secret</article>")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        gate = RobotsGate(client)
        assert fetch_raw_text(client, "https://example.com/news/1", {}, gate) is None


def test_normalizer_includes_raw_text_and_origin_published_at():
    source = Source("src-1", "rss", "g-1", "https://example.com/feed")
    item = CollectedItem(
        "item-1",
        "Patch 1.2",
        "https://example.com/1",
        "One. Two.",
        published_at="Mon, 10 Aug 2026 09:00:00 +0900",
    )
    payload = to_ingest_payload(source, item, raw_text="  full body text  ")
    assert payload["raw_text"] == "full body text"
    assert str(payload["origin_published_at"]).startswith("2026-08-10T09:00:00")

    # raw_text가 없으면 summary로 폴백
    fallback = to_ingest_payload(source, item)
    assert fallback["raw_text"] == "One. Two."


def test_parse_published_at_formats():
    assert str(parse_published_at("2026-08-10T12:00:00Z")).startswith("2026-08-10T12:00:00")
    assert str(parse_published_at("2026.08.10")).startswith("2026-08-10")
    assert parse_published_at("not a date") is None
    assert parse_published_at(None) is None
