from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeSourceUrlError(ValueError):
    pass


def validate_public_http_url(value: str) -> str:
    """SSRF 방지: HTTP(S) 공개 호스트만 수집 소스로 허용."""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeSourceUrlError("Source URL must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password:
        raise UnsafeSourceUrlError("Credentials are not allowed in source URLs")

    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".local"):
        raise UnsafeSourceUrlError("Private source hosts are not allowed")

    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        addresses = {item[4][0] for item in socket.getaddrinfo(host, port)}
    except (socket.gaierror, ValueError) as exc:
        raise UnsafeSourceUrlError("Source host could not be resolved") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise UnsafeSourceUrlError("Private or reserved source addresses are not allowed")
    return value
