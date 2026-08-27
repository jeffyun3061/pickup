"""
robots.txt 준수 게이트.

- HTML 목록 크롤과 상세 페이지 fetch 전에 허용 여부를 확인한다.
- RSS/JSON 피드 엔드포인트 자체는 구독용 데이터 인터페이스로 보고 검사하지 않는다(ADR-012).
- 도메인별로 캐시하고, robots.txt 조회 실패 시에는 허용으로 간주하되 짧게 캐시해 재확인한다.
"""

from __future__ import annotations

import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

DEFAULT_USER_AGENT = "GamePickupBot/1.0"
_ALLOW_ALL = object()
_DENY_ALL = object()

_TTL_OK_SECONDS = 24 * 60 * 60
_TTL_ERROR_SECONDS = 5 * 60


class RobotsGate:
    def __init__(self, client: httpx.Client, user_agent: str = DEFAULT_USER_AGENT) -> None:
        self._client = client
        self._user_agent = user_agent
        self._cache: dict[str, tuple[float, object]] = {}

    def allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
        origin = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._parser_for(origin)
        if parser is _ALLOW_ALL:
            return True
        if parser is _DENY_ALL:
            return False
        assert isinstance(parser, RobotFileParser)
        return parser.can_fetch(self._user_agent, url)

    def _parser_for(self, origin: str) -> object:
        now = time.monotonic()
        cached = self._cache.get(origin)
        if cached and cached[0] > now:
            return cached[1]

        parser: object
        ttl = _TTL_OK_SECONDS
        try:
            response = self._client.get(f"{origin}/robots.txt")
            if response.status_code in {401, 403}:
                # 접근 거부는 robots.txt 부재(404)와 다르다. 사이트가
                # 자동 접근을 명시적으로 막았으므로 해당 도메인은 건너뛴다.
                parser = _DENY_ALL
                ttl = _TTL_ERROR_SECONDS
            elif response.status_code >= 500:
                # 일시 장애일 수 있으니 허용하되 짧게 캐시해 재확인한다.
                parser = _ALLOW_ALL
                ttl = _TTL_ERROR_SECONDS
            elif response.status_code >= 400:
                # robots.txt 없음 → 전체 허용 관례
                parser = _ALLOW_ALL
            else:
                rp = RobotFileParser()
                rp.parse(response.text.splitlines())
                parser = rp
        except httpx.HTTPError:
            parser = _ALLOW_ALL
            ttl = _TTL_ERROR_SECONDS

        self._cache[origin] = (now + ttl, parser)
        return parser
