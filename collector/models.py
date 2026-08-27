from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CollectedItem:
    external_id: str
    title: str
    url: str
    summary: str = ""
    image_url: str | None = None
    published_at: str | None = None


@dataclass(frozen=True)
class Source:
    id: str
    source_type: str
    game_id: str
    endpoint_url: str
    config: dict[str, str] = field(default_factory=dict)
    secret_env_name: str | None = None
    http_cache: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Job:
    run_id: str
    source: Source
