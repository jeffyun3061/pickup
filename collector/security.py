from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


def assert_public_source_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Source URL must be public HTTP(S)")
    if parsed.username or parsed.password:
        raise ValueError("Source URL credentials are not allowed")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".local"):
        raise ValueError("Source URL must not target a local host")
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as exc:
        raise ValueError("Source URL has an invalid port") from exc
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, port)}
    except socket.gaierror as exc:
        raise ValueError("Source host could not be resolved") from exc
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("Source URL resolved to a private or reserved address")
