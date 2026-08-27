"""
HTML 목록 크롤 커넥터.

RSS도 내부 JSON도 없는 서버 렌더링 페이지용. 사이트별 차이는 CSS 셀렉터 config로 흡수한다.

config:
- list_selector  (필수) 목록 아이템 노드
- url_selector   기본 "a" / url_attr 기본 "href" — endpoint_url 기준으로 상대경로 해석
- title_selector 없으면 링크 노드(또는 아이템 노드) 텍스트
- id_selector + id_attr  없으면 해석된 URL을 external_id로 사용
- summary_selector, image_selector(image_attr 기본 "src"), date_selector(date_attr)
- max_items 기본 100
"""

from __future__ import annotations

from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser, Node

from collector.connectors.base import checked_body
from collector.models import CollectedItem, Source


def _node_text(node: Node | None) -> str:
    if node is None:
        return ""
    return " ".join(node.text(separator=" ").split()).strip()


def _attr(node: Node | None, name: str) -> str:
    if node is None:
        return ""
    return (node.attributes.get(name) or "").strip()


class HtmlConnector:
    @staticmethod
    def request_headers(source: Source, secret: str | None = None) -> dict[str, str]:
        return {"Accept": "text/html,application/xhtml+xml"}

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
        list_selector = (config.get("list_selector") or "").strip()
        if not list_selector:
            raise ValueError("HTML source requires config.list_selector")

        tree = HTMLParser(body)
        nodes = tree.css(list_selector)

        result: list[CollectedItem] = []
        for node in nodes:
            link = node.css_first(config.get("url_selector") or "a")
            href = _attr(link, config.get("url_attr") or "href")
            url = urljoin(source.endpoint_url, href) if href else ""

            title_selector = config.get("title_selector")
            title = _node_text(node.css_first(title_selector)) if title_selector else ""
            if not title:
                title = _node_text(link) or _node_text(node)

            external_id = ""
            id_selector = config.get("id_selector")
            if id_selector:
                id_node = node.css_first(id_selector)
                id_attr = config.get("id_attr")
                external_id = _attr(id_node, id_attr) if id_attr else _node_text(id_node)
            if not external_id:
                external_id = url

            if not title or not external_id:
                continue

            summary = ""
            if config.get("summary_selector"):
                summary = _node_text(node.css_first(config["summary_selector"]))

            image_url = None
            if config.get("image_selector"):
                image = _attr(
                    node.css_first(config["image_selector"]),
                    config.get("image_attr") or "src",
                )
                if image:
                    image_url = urljoin(source.endpoint_url, image)

            published_at = None
            if config.get("date_selector"):
                date_node = node.css_first(config["date_selector"])
                date_attr = config.get("date_attr")
                published_at = (_attr(date_node, date_attr) if date_attr else _node_text(date_node)) or None

            result.append(
                CollectedItem(
                    external_id=external_id,
                    title=title,
                    url=url,
                    summary=summary,
                    image_url=image_url,
                    published_at=published_at,
                )
            )

        limit = min(max(int(config.get("max_items", "100")), 1), 500)
        return result[:limit]
