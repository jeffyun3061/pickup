from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import httpx

from collector.connectors.base import checked_body
from collector.models import CollectedItem, Source

_MEDIA = "{http://search.yahoo.com/mrss/}"


def _image_url(item: ET.Element, base_url: str) -> str | None:
    enclosure = item.find("enclosure")
    if enclosure is not None and (enclosure.attrib.get("type") or "").startswith("image/"):
        url = enclosure.attrib.get("url", "")
        if url:
            return urljoin(base_url, url)
    for name in (f"{_MEDIA}content", f"{_MEDIA}thumbnail"):
        media = item.find(name)
        if media is not None and media.attrib.get("url"):
            return urljoin(base_url, media.attrib["url"])
    for link in item.findall("{http://www.w3.org/2005/Atom}link"):
        if link.attrib.get("rel") == "enclosure" and (
            link.attrib.get("type") or ""
        ).startswith("image/"):
            return urljoin(base_url, link.attrib.get("href", ""))
    return None


def _text(node: ET.Element, *names: str) -> str:
    for name in names:
        child = node.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""


class RssConnector:
    @staticmethod
    def request_headers(source: Source, secret: str | None = None) -> dict[str, str]:
        return {"Accept": "application/rss+xml, application/atom+xml"}

    def collect(
        self,
        client: httpx.Client,
        source: Source,
        secret: str | None = None,
    ) -> list[CollectedItem]:
        response = client.get(source.endpoint_url, headers=self.request_headers(source, secret))
        return self.parse(checked_body(response), source)

    def parse(self, body: bytes, source: Source) -> list[CollectedItem]:
        root = ET.fromstring(body)
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        result: list[CollectedItem] = []
        for item in items:
            title = _text(item, "title", "{http://www.w3.org/2005/Atom}title")
            link = _text(item, "link")
            if not link:
                atom_link = item.find("{http://www.w3.org/2005/Atom}link")
                link = atom_link.attrib.get("href", "") if atom_link is not None else ""
            external_id = _text(
                item,
                "guid",
                "{http://www.w3.org/2005/Atom}id",
            ) or link
            if not title or not external_id:
                continue
            result.append(
                CollectedItem(
                    external_id=external_id,
                    title=title,
                    url=link,
                    summary=_text(
                        item,
                        "description",
                        "{http://www.w3.org/2005/Atom}summary",
                        "{http://www.w3.org/2005/Atom}content",
                    ),
                    published_at=_text(
                        item,
                        "pubDate",
                        "{http://www.w3.org/2005/Atom}published",
                        "{http://www.w3.org/2005/Atom}updated",
                    )
                    or None,
                    image_url=_image_url(item, source.endpoint_url),
                )
            )
        limit = min(max(int(source.config.get("max_items", "100")), 1), 500)
        return result[:limit]
