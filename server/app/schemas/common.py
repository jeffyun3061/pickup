from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ImageRightsStatus = Literal["unverified", "official", "licensed", "original"]

# 요약은 모바일 카드에서 짧게 읽는 값이다. 입력 계층에서 개수·길이를
# 제한해 관리자/수집기 오류가 DB와 공개 응답 크기로 번지지 않게 한다.
SummaryPoint = Annotated[str, Field(min_length=1, max_length=500)]
SummaryPoints = Annotated[list[SummaryPoint], Field(max_length=8)]


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    initial: str
    genre: str
    color: str
    interest_count: int
    image_url: str | None = None
    image_source_url: str | None = None
    image_rights_status: ImageRightsStatus = "unverified"
    fallback_image_key: str = "coverTactical"


class ContentAnalysisOut(BaseModel):
    """공식 원문 기반 참고용 분석. 커뮤니티 값은 근거 없이는 unknown이어야 한다."""

    importance: Literal[1, 2, 3]
    impact_level: Literal["low", "medium", "high"]
    impact_summary: str
    confidence: Literal["low", "medium", "high"]
    community_sentiment: Literal["positive", "mixed", "negative", "unknown"] = "unknown"
    community_summary: str | None = None
    community_sample_count: int | None = Field(default=None, ge=0)
    generated_at: datetime | None = None


class ContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    game_id: str
    game_name: str
    kind: Literal["update", "event", "popup", "goods"]
    title: str
    summary_points: list[str]
    analysis: ContentAnalysisOut | None = None
    official_url: str
    image_url: str | None = None
    image_source_url: str | None = None
    image_rights_status: ImageRightsStatus = "unverified"
    fallback_image_key: str = "coverTactical"
    fallback_color: str = "#2A2A2B"
    place: str | None = None
    reservation_url: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    published_at: datetime | None = None
    status: Literal["draft", "reviewed", "published"] | None = None
    idempotency_key: str | None = None
    # 관리자 전용 (단계 타임라인 + AI 요약 상태) — public 응답에서는 None
    summary_status: Literal["none", "pending", "done", "failed"] | None = None
    source_id: str | None = None
    created_at: datetime | None = None
    summarized_at: datetime | None = None
    origin_published_at: datetime | None = None
    raw_text_excerpt: str | None = None
    # 품질 게이트·예약 발행·데드링크 (관리자 전용)
    needs_review_reason: str | None = None
    scheduled_publish_at: datetime | None = None
    link_broken: bool | None = None
    auto_published: bool | None = None


class RankingOut(BaseModel):
    game_id: str
    game_name: str
    interest_count: int
    rank: int
    initial: str
    color: str
    image_url: str | None = None
    image_rights_status: ImageRightsStatus = "unverified"
    fallback_image_key: str = "coverTactical"


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    body: str
    published_at: datetime | None = None


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
    image_source_url: str | None = Field(default=None, max_length=500)
    image_rights_status: ImageRightsStatus = "unverified"
    fallback_image_key: str = Field(default="coverTactical", max_length=64)
    is_active: bool = True


class GameUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    initial: str | None = Field(default=None, max_length=8)
    genre: str | None = Field(default=None, max_length=80)
    color: str | None = Field(default=None, max_length=16)
    interest_count: int | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    image_source_url: str | None = Field(default=None, max_length=500)
    image_rights_status: ImageRightsStatus | None = None
    fallback_image_key: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None


class ContentCreate(BaseModel):
    id: str | None = Field(default=None, max_length=64)
    game_id: str = Field(min_length=1, max_length=64)
    kind: Literal["update", "event", "popup", "goods"]
    title: str = Field(min_length=1, max_length=240)
    summary_points: SummaryPoints = Field(default_factory=list)
    official_url: str = Field(default="", max_length=500)
    image_url: str | None = Field(default=None, max_length=500)
    image_source_url: str | None = Field(default=None, max_length=500)
    image_rights_status: ImageRightsStatus = "unverified"
    place: str | None = Field(default=None, max_length=200)
    reservation_url: str | None = Field(default=None, max_length=500)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: Literal["draft", "reviewed", "published"] = "draft"

    @model_validator(mode="after")
    def validate_period(self) -> "ContentCreate":
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("ends_at must be on or after starts_at")
        return self


class ContentUpdate(BaseModel):
    game_id: str | None = Field(default=None, max_length=64)
    kind: Literal["update", "event", "popup", "goods"] | None = None
    title: str | None = Field(default=None, max_length=240)
    summary_points: SummaryPoints | None = None
    official_url: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=500)
    image_source_url: str | None = Field(default=None, max_length=500)
    image_rights_status: ImageRightsStatus | None = None
    place: str | None = Field(default=None, max_length=200)
    reservation_url: str | None = Field(default=None, max_length=500)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: Literal["draft", "reviewed", "published"] | None = None
    scheduled_publish_at: datetime | None = None


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
    summary_points: SummaryPoints = Field(default_factory=list)
    official_url: str = Field(default="", max_length=500)
    image_url: str | None = Field(default=None, max_length=500)
    image_source_url: str | None = Field(default=None, max_length=500)
    image_rights_status: ImageRightsStatus = "unverified"
    place: str | None = None
    reservation_url: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=120)
    source_id: str | None = Field(default=None, max_length=64)
    raw_text: str | None = Field(default=None, max_length=20000)
    origin_published_at: datetime | None = None


class IngestContentOut(ContentOut):
    created: bool


class IngestCheckIn(BaseModel):
    """collector가 새 글에만 상세 fetch를 하도록, 이미 수집된 키를 사전 조회한다."""

    source_id: str = Field(min_length=1, max_length=64)
    idempotency_keys: list[str] = Field(default_factory=list, max_length=500)


class IngestCheckOut(BaseModel):
    existing: list[str]


SourceType = Literal["rss", "api", "html"]


class IngestSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    source_type: SourceType
    game_id: str = Field(min_length=1, max_length=64)
    endpoint_url: str = Field(min_length=8, max_length=1000)
    interval_minutes: int = Field(default=60, ge=5, le=10080)
    enabled: bool = True
    auto_publish: bool = False
    config: dict[str, str] = Field(default_factory=dict)
    secret_env_name: str | None = Field(
        default=None, max_length=120, pattern=r"^[A-Z][A-Z0-9_]*$"
    )


class IngestSourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    source_type: SourceType | None = None
    game_id: str | None = Field(default=None, min_length=1, max_length=64)
    endpoint_url: str | None = Field(default=None, min_length=8, max_length=1000)
    interval_minutes: int | None = Field(default=None, ge=5, le=10080)
    enabled: bool | None = None
    auto_publish: bool | None = None
    config: dict[str, str] | None = None
    secret_env_name: str | None = Field(
        default=None, max_length=120, pattern=r"^[A-Z][A-Z0-9_]*$"
    )


class IngestSourceOut(BaseModel):
    id: str
    name: str
    source_type: SourceType
    game_id: str
    game_name: str
    endpoint_url: str
    interval_minutes: int
    enabled: bool
    auto_publish: bool
    config: dict[str, str]
    secret_env_name: str | None
    next_run_at: datetime | None
    last_run_at: datetime | None
    last_status: str | None
    consecutive_failures: int
    consecutive_empty_runs: int
    # ok | failing | quiet — 조용한 실패(셀렉터 깨짐 등) 노출용
    health: Literal["ok", "failing", "quiet"]
    created_at: datetime
    # 신뢰도 추적 + 자동 발행 승격 제안
    stat_approved: int = 0
    stat_edited: int = 0
    stat_retracted: int = 0
    promote_suggested: bool = False


class IngestRunOut(BaseModel):
    id: str
    source_id: str
    source_name: str
    status: Literal["pending", "running", "succeeded", "failed"]
    attempt: int
    items_seen: int
    items_created: int
    not_modified: bool = False
    error: str | None
    queued_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class IngestJobOut(BaseModel):
    run: IngestRunOut
    source: IngestSourceOut
    http_cache: dict[str, str] = Field(default_factory=dict)


class IngestRunComplete(BaseModel):
    status: Literal["succeeded", "failed"]
    items_seen: int = Field(default=0, ge=0)
    items_created: int = Field(default=0, ge=0)
    error: str | None = Field(default=None, max_length=1000)
    not_modified: bool = False
    http_cache: dict[str, str] | None = None


class SourcePreviewIn(BaseModel):
    """저장 전 소스 설정 검증(dry-run). 서버가 직접 fetch·파싱해 미리보기를 돌려준다."""

    source_type: SourceType
    endpoint_url: str = Field(min_length=8, max_length=1000)
    config: dict[str, str] = Field(default_factory=dict)
    secret_env_name: str | None = Field(
        default=None, max_length=120, pattern=r"^[A-Z][A-Z0-9_]*$"
    )


class SourcePreviewItem(BaseModel):
    external_id: str
    title: str
    url: str
    summary: str = ""
    image_url: str | None = None
    published_at: str | None = None


class SourcePreviewOut(BaseModel):
    items: list[SourcePreviewItem]
    warning: str | None = None


class ContentFromUrlIn(BaseModel):
    """관리자 빠른 등록: URL만 넣으면 본문 추출 + AI 요약까지 채운 초안을 만든다."""

    url: str = Field(min_length=8, max_length=500)
    game_id: str = Field(min_length=1, max_length=64)
    kind: Literal["update", "event", "popup", "goods"] = "update"


class InstallationCreateOut(BaseModel):
    installation_id: str
    secret: str


class DeviceTokenUpsert(BaseModel):
    platform: Literal["android", "ios", "web"] = "android"
    token: str = Field(min_length=8, max_length=512)


class DeviceTokenOut(BaseModel):
    platform: str
    token: str
    updated: bool


class NotificationPrefsIn(BaseModel):
    selected_game_news: bool = True
    event_ending: bool = True
    service_notices: bool = True


class InstallationPreferencesIn(BaseModel):
    game_ids: list[Annotated[str, Field(min_length=1, max_length=64)]] = Field(
        # 앱 정책과 동일하게 요청 자체에서도 8개를 넘기지 않는다.
        # 서비스 계층의 활성 게임·중복 정규화 검증은 별도로 유지한다.
        default_factory=list, max_length=8
    )
    notifications: NotificationPrefsIn = Field(default_factory=NotificationPrefsIn)


class InstallationPreferencesOut(BaseModel):
    game_ids: list[str]
    notifications: NotificationPrefsIn


class PushDispatchOut(BaseModel):
    processed: int
    sent: int
    failed: int


class PushStatsOut(BaseModel):
    pending: int
    sent: int
    failed: int
    last_sent_at: datetime | None = None


class TopGamePick(BaseModel):
    game_id: str
    game_name: str
    pick_count: int


class UserStatsOut(BaseModel):
    installations: int
    with_device_token: int
    notify_selected_game_news: int
    notify_event_ending: int
    notify_service_notices: int
    top_games: list[TopGamePick]


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor: str
    action: str
    entity: str
    entity_id: str
    detail: str
    created_at: datetime
