from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    initial: str
    genre: str
    color: str
    interest_count: int
    image_url: str | None = None


class ContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    game_id: str
    game_name: str
    kind: Literal["update", "event", "popup", "goods"]
    title: str
    summary_points: list[str]
    official_url: str
    image_url: str | None = None
    place: str | None = None
    reservation_url: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    published_at: datetime | None = None
    status: Literal["draft", "reviewed", "published"] | None = None


class RankingOut(BaseModel):
    game_id: str
    game_name: str
    interest_count: int
    rank: int
    initial: str
    color: str
    image_url: str | None = None


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    body: str
    published_at: datetime


class InquiryCreate(BaseModel):
    email: str | None = Field(default=None, max_length=200)
    category: str = Field(default="general", max_length=40)
    message: str = Field(min_length=5, max_length=4000)


class InquiryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str | None
    category: str
    message: str
    status: Literal["open", "closed"]
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class GameCreate(BaseModel):
    id: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    initial: str = Field(default="", max_length=8)
    genre: str = Field(default="", max_length=80)
    color: str = Field(default="#2A2A2B", max_length=16)
    interest_count: int = Field(default=0, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class GameUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    initial: str | None = Field(default=None, max_length=8)
    genre: str | None = Field(default=None, max_length=80)
    color: str | None = Field(default=None, max_length=16)
    interest_count: int | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ContentCreate(BaseModel):
    id: str | None = Field(default=None, max_length=64)
    game_id: str = Field(min_length=1, max_length=64)
    kind: Literal["update", "event", "popup", "goods"]
    title: str = Field(min_length=1, max_length=240)
    summary_points: list[str] = Field(default_factory=list)
    official_url: str = Field(default="", max_length=500)
    image_url: str | None = Field(default=None, max_length=500)
    place: str | None = Field(default=None, max_length=200)
    reservation_url: str | None = Field(default=None, max_length=500)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: Literal["draft", "reviewed", "published"] = "draft"


class ContentUpdate(BaseModel):
    game_id: str | None = Field(default=None, max_length=64)
    kind: Literal["update", "event", "popup", "goods"] | None = None
    title: str | None = Field(default=None, max_length=240)
    summary_points: list[str] | None = None
    official_url: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=500)
    place: str | None = Field(default=None, max_length=200)
    reservation_url: str | None = Field(default=None, max_length=500)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: Literal["draft", "reviewed", "published"] | None = None


class AnnouncementCreate(BaseModel):
    id: str | None = Field(default=None, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=8000)
    is_published: bool = True


class IngestContentCreate(BaseModel):
    """자동화용 — 항상 draft로만 저장. idempotency_key로 재시도 안전."""

    game_id: str = Field(min_length=1, max_length=64)
    kind: Literal["update", "event", "popup", "goods"] = "update"
    title: str = Field(min_length=1, max_length=240)
    summary_points: list[str] = Field(default_factory=list)
    official_url: str = Field(default="", max_length=500)
    image_url: str | None = Field(default=None, max_length=500)
    place: str | None = None
    reservation_url: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=120)
