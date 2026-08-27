import httpx
import pytest
import socket

from collector.connectors import ApiConnector, RssConnector
from collector.models import CollectedItem, Source
from collector.normalizer import to_ingest_payload
from collector.security import assert_public_source_url


def test_control_plane_url_is_required_and_validated(monkeypatch):
    from collector.runner import _control_plane_url

    monkeypatch.delenv("INGEST_SERVER_URL", raising=False)
    try:
        _control_plane_url()
    except SystemExit as exc:
        assert str(exc) == "INGEST_SERVER_URL is required"
    else:  # pragma: no cover - assertion guard
        raise AssertionError("missing control-plane URL must fail fast")

    monkeypatch.setenv("INGEST_SERVER_URL", "https://api.example.com/base")
    assert _control_plane_url() == "https://api.example.com/base"

    monkeypatch.setenv("INGEST_SERVER_URL", "https://user:pass@example.com")
    try:
        _control_plane_url()
    except SystemExit as exc:
        assert "credentials" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("credentials in control-plane URL must fail")


def _client(body: bytes, content_type: str) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body, headers={"content-type": content_type})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_rss_connector_parses_items():
    xml = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel><item>
      <guid>news-1</guid><title>Patch 1.2</title>
      <link>https://example.com/news/1</link>
      <description><![CDATA[First fix. Second fix.]]></description>
    </item></channel></rss>"""
    source = Source("src-1", "rss", "g-1", "https://example.com/feed")
    with _client(xml, "application/rss+xml") as client:
        items = RssConnector().collect(client, source)
    assert items[0].external_id == "news-1"
    assert items[0].title == "Patch 1.2"


def test_rss_connector_returns_empty_for_feed_without_valid_items():
    xml = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item><guid>missing-title</guid><link>https://example.com/1</link></item>
      <item><title>missing-id</title></item>
    </channel></rss>"""
    source = Source("src-empty", "rss", "g-1", "https://example.com/feed")
    with _client(xml, "application/rss+xml") as client:
        assert RssConnector().collect(client, source) == []


def test_rss_connector_extracts_permitted_feed_image():
    xml = b"""<?xml version="1.0"?>
    <rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><item>
      <guid>news-image</guid><title>Image News</title>
      <link>https://example.com/news/image</link>
      <media:thumbnail url="/assets/news.jpg" />
    </item></channel></rss>"""
    source = Source("src-1", "rss", "g-1", "https://example.com/feed")
    with _client(xml, "application/rss+xml") as client:
        items = RssConnector().collect(client, source)
    assert items[0].image_url == "https://example.com/assets/news.jpg"


def test_api_connector_uses_mapping_and_secret():
    body = b'{"data":{"articles":[{"key":"a-1","headline":"News","link":"https://example.com/1"}]}}'
    source = Source(
        "src-2",
        "api",
        "g-1",
        "https://example.com/api",
        {
            "items_path": "data.articles",
            "id_field": "key",
            "title_field": "headline",
            "url_field": "link",
        },
        "SOURCE_TOKEN",
    )
    with _client(body, "application/json") as client:
        items = ApiConnector().collect(client, source, "secret")
    assert items[0].external_id == "a-1"
    assert items[0].url == "https://example.com/1"


def test_api_connector_skips_malformed_rows_and_accepts_empty_list():
    body = '{"data":{"articles":[{"key":"ok","headline":"정상"},{"key":"no-title"},"noise"]}}'.encode()
    source = Source(
        "src-api-filter",
        "api",
        "g-1",
        "https://example.com/api",
        {"items_path": "data.articles", "id_field": "key", "title_field": "headline"},
    )
    with _client(body, "application/json") as client:
        items = ApiConnector().collect(client, source)
    assert [(item.external_id, item.title) for item in items] == [("ok", "정상")]

    empty_source = Source(
        "src-api-empty",
        "api",
        "g-1",
        "https://example.com/api",
        {"items_path": "data.articles"},
    )
    with _client(b'{"data":{"articles":[]}}', "application/json") as client:
        assert ApiConnector().collect(client, empty_source) == []


def test_normalizer_cleans_html_and_builds_stable_key():
    source = Source("src-1", "rss", "g-1", "https://example.com/feed")
    item = CollectedItem("item-1", " New &amp; Good ", "https://example.com/1", "<b>One.</b> Two.")
    first = to_ingest_payload(source, item)
    second = to_ingest_payload(source, item)
    assert first["title"] == "New & Good"
    assert first["summary_points"] == ["One.", "Two."]
    assert first["idempotency_key"] == second["idempotency_key"]


def test_runtime_ssrf_guard_rejects_private_dns(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))
        ],
    )
    with pytest.raises(ValueError, match="private"):
        assert_public_source_url("https://feed.example.com/rss")
