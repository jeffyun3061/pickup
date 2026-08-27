"""
소스 설정 dry-run(테스트 수집)과 URL 빠른 등록용 페이지 추출.

collector 커넥터와 동일한 config 계약(items_path·셀렉터 등)을 미러링한다.
계약의 원본은 collector이며, 여기는 저장 전 검증을 위한 제어면 미리보기다 (ADR-012).
"""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException
from selectolax.parser import HTMLParser, Node

from app.domain.source_url import UnsafeSourceUrlError, validate_public_http_url
from app.schemas.common import SourcePreviewItem

_MAX_BYTES = 5 * 1024 * 1024
_USER_AGENT = "GamePickupBot/1.0"
_PREVIEW_LIMIT = 10
_ATOM = "{http://www.w3.org/2005/Atom}"
_MEDIA = "{http://search.yahoo.com/mrss/}"


def _fetch(url: str, headers: dict[str, str]) -> bytes:
    try:
        validate_public_http_url(url)
    except UnsafeSourceUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        response = httpx.get(
            url,
            headers={"User-Agent": _USER_AGENT, **headers},
            timeout=15.0,
            follow_redirects=False,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Source fetch failed: {exc}") from exc
    if len(response.content) > _MAX_BYTES:
        raise HTTPException(status_code=502, detail="Source response exceeds 5 MB")
    return response.content


def _json_path(value: Any, dotted: str) -> Any:
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


def _et_text(node: ET.Element, *names: str) -> str:
    for name in names:
        child = node.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def _node_text(node: Node | None) -> str:
    if node is None:
        return ""
    return " ".join(node.text(separator=" ").split()).strip()


def _attr(node: Node | None, name: str) -> str:
    if node is None:
        return ""
    return (node.attributes.get(name) or "").strip()


def _rss_image(node: ET.Element, base_url: str) -> str | None:
    enclosure = node.find("enclosure")
    if enclosure is not None and (enclosure.attrib.get("type") or "").startswith("image/"):
        if enclosure.attrib.get("url"):
            return urljoin(base_url, enclosure.attrib["url"])
    for name in (f"{_MEDIA}content", f"{_MEDIA}thumbnail"):
        media = node.find(name)
        if media is not None and media.attrib.get("url"):
            return urljoin(base_url, media.attrib["url"])
    for atom_link in node.findall(f"{_ATOM}link"):
        if atom_link.attrib.get("rel") == "enclosure" and (
            atom_link.attrib.get("type") or ""
        ).startswith("image/"):
            return urljoin(base_url, atom_link.attrib.get("href", ""))
    return None


def _parse_rss(body: bytes, base_url: str) -> list[SourcePreviewItem]:
    root = ET.fromstring(body)
    nodes = root.findall(".//item") or root.findall(f".//{_ATOM}entry")
    items: list[SourcePreviewItem] = []
    for node in nodes:
        title = _et_text(node, "title", f"{_ATOM}title")
        link = _et_text(node, "link")
        if not link:
            atom_link = node.find(f"{_ATOM}link")
            link = atom_link.attrib.get("href", "") if atom_link is not None else ""
        external_id = _et_text(node, "guid", f"{_ATOM}id") or link
        if not title or not external_id:
            continue
        items.append(
            SourcePreviewItem(
                external_id=external_id,
                title=title,
                url=link,
                summary=_et_text(node, "description", f"{_ATOM}summary", f"{_ATOM}content"),
                image_url=_rss_image(node, base_url),
                published_at=_et_text(node, "pubDate", f"{_ATOM}published", f"{_ATOM}updated")
                or None,
            )
        )
    return items


def _parse_api(body: bytes, config: dict[str, str]) -> list[SourcePreviewItem]:
    payload = json.loads(body)
    raw_items = _json_path(payload, config.get("items_path", ""))
    if not isinstance(raw_items, list):
        raise HTTPException(status_code=400, detail="items_path did not resolve to a list")
    items: list[SourcePreviewItem] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        external_id = _json_path(raw, config.get("id_field", "id"))
        title = _json_path(raw, config.get("title_field", "title"))
        url = _json_path(raw, config.get("url_field", "url"))
        if external_id is None or not title:
            continue
        items.append(
            SourcePreviewItem(
                external_id=str(external_id),
                title=str(title),
                url=str(url or ""),
                summary=str(_json_path(raw, config.get("summary_field", "summary")) or ""),
                image_url=str(_json_path(raw, config.get("image_field", "image_url")) or "")
                or None,
                published_at=str(
                    _json_path(raw, config.get("published_field", "published_at")) or ""
                )
                or None,
            )
        )
    return items


def _parse_html(body: bytes, config: dict[str, str], base_url: str) -> list[SourcePreviewItem]:
    list_selector = (config.get("list_selector") or "").strip()
    if not list_selector:
        raise HTTPException(status_code=400, detail="HTML source requires config.list_selector")
    tree = HTMLParser(body)
    items: list[SourcePreviewItem] = []
    for node in tree.css(list_selector):
        link = node.css_first(config.get("url_selector") or "a")
        href = _attr(link, config.get("url_attr") or "href")
        url = urljoin(base_url, href) if href else ""
        title_selector = config.get("title_selector")
        title = _node_text(node.css_first(title_selector)) if title_selector else ""
        if not title:
            title = _node_text(link) or _node_text(node)
        external_id = ""
        if config.get("id_selector"):
            id_node = node.css_first(config["id_selector"])
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
            image = _attr(node.css_first(config["image_selector"]), config.get("image_attr") or "src")
            if image:
                image_url = urljoin(base_url, image)
        published_at = None
        if config.get("date_selector"):
            date_node = node.css_first(config["date_selector"])
            date_attr = config.get("date_attr")
            published_at = (_attr(date_node, date_attr) if date_attr else _node_text(date_node)) or None
        items.append(
            SourcePreviewItem(
                external_id=external_id,
                title=title,
                url=url,
                summary=summary,
                image_url=image_url,
                published_at=published_at,
            )
        )
    return items


def preview_source(
    source_type: str,
    endpoint_url: str,
    config: dict[str, str],
    secret_env_name: str | None = None,
) -> tuple[list[SourcePreviewItem], str | None]:
    headers: dict[str, str] = {}
    warning = None
    if source_type == "rss":
        headers["Accept"] = "application/rss+xml, application/atom+xml"
    elif source_type == "api":
        headers["Accept"] = "application/json"
        if secret_env_name:
            secret = os.environ.get(secret_env_name)
            if secret:
                header = config.get("auth_header", "Authorization")
                prefix = config.get("auth_prefix", "Bearer")
                headers[header] = f"{prefix} {secret}".strip()
            else:
                warning = f"서버에 {secret_env_name} 환경변수가 없어 인증 없이 조회했습니다."
    else:
        headers["Accept"] = "text/html,application/xhtml+xml"

    body = _fetch(endpoint_url, headers)
    try:
        if source_type == "rss":
            items = _parse_rss(body, endpoint_url)
        elif source_type == "api":
            items = _parse_api(body, config)
        else:
            items = _parse_html(body, config, endpoint_url)
    except HTTPException:
        raise
    except (ET.ParseError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Source parse failed: {exc}") from exc

    if not items and warning is None:
        warning = "아이템이 0건입니다. 셀렉터/경로 설정을 확인하세요."
    return items[:_PREVIEW_LIMIT], warning


def extract_page(url: str) -> tuple[str, str]:
    """URL 빠른 등록용: 페이지 제목과 본문 텍스트(최대 8000자)를 추출한다."""
    body = _fetch(url, {"Accept": "text/html,application/xhtml+xml"})
    tree = HTMLParser(body)
    og_title = tree.css_first('meta[property="og:title"]')
    title = _attr(og_title, "content") if og_title else ""
    if not title:
        title = _node_text(tree.css_first("title"))
    tree.strip_tags(["script", "style", "noscript", "nav", "header", "footer", "iframe", "svg"])
    node = tree.css_first("article") or tree.css_first("main") or tree.css_first("body") or tree.root
    text = _node_text(node) if node is not None else ""
    if not title:
        raise HTTPException(status_code=400, detail="페이지에서 제목을 추출하지 못했습니다.")
    return title[:240], text[:8000]
