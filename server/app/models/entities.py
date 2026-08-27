from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ContentKind(str, enum.Enum):
    update = "update"
    event = "event"
    popup = "popup"
    goods = "goods"


class ContentStatus(str, enum.Enum):
    draft = "draft"
    reviewed = "reviewed"
    published = "published"


class InquiryStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class PushOutboxStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class IngestSourceType(str, enum.Enum):
    rss = "rss"
    api = "api"
    html = "html"


class IngestRunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    initial: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    genre: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#2A2A2B")
    interest_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_rights_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unverified"
    )
    fallback_image_key: Mapped[str] = mapped_column(
        String(64), nullable=False, default="coverTactical"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contents: Mapped[list[Content]] = relationship(back_populates="game")
    installation_games: Mapped[list[InstallationGame]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class Content(Base):
    __tablename__ = "contents"
    __table_args__ = (Index("ix_contents_status_published_at", "status", "published_at"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False, index=True)
    kind: Mapped[ContentKind] = mapped_column(Enum(ContentKind), nullable=False)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), nullable=False, default=ContentStatus.draft, index=True
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary_points_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    official_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_rights_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unverified"
    )
    place: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reservation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    # 자동 수집 파이프라인 (LLM 요약 + 단계 타임라인)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 공식 원문 기반 LLM 분석 결과. 커뮤니티 분석은 근거 수집 전까지 unknown으로 저장한다.
    analysis_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    # none | pending | done | failed — 마이그레이션 단순화를 위해 String 사용
    summary_status: Mapped[str] = mapped_column(String(12), nullable=False, default="none")
    summarized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    origin_published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 소스 삭제 시에도 콘텐츠는 남아야 하므로 FK 없이 참조만 보관
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # 품질 게이트가 자동 발행을 막은 사유 (검수 큐에서 표시)
    needs_review_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # 예약 발행: 검수 완료 상태에서 이 시각 도달 시 러너가 발행
    scheduled_publish_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 데드링크 감지: 원문 URL이 404/410으로 확인됨
    link_broken: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # 소스 신뢰도 추적용: 수집 후 관리자가 본문을 수정했는지 / 자동 발행 여부
    edited_after_ingest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # 이벤트 마감 리마인더 중복 발송 방지
    event_reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    game: Mapped[Game] = relationship(back_populates="contents")


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Inquiry(Base):
    __tablename__ = "inquiries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="general")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InquiryStatus] = mapped_column(
        Enum(InquiryStatus), nullable=False, default=InquiryStatus.open
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Installation(Base):
    """앱 설치 단위 신원. secret은 해시만 보관."""

    __tablename__ = "installations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    secret_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    game_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    notify_selected_game_news: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_event_ending: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_service_notices: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    device_tokens: Mapped[list[DeviceToken]] = relationship(back_populates="installation")
    installation_games: Mapped[list[InstallationGame]] = relationship(
        back_populates="installation", cascade="all, delete-orphan"
    )


class InstallationGame(Base):
    """설치별 관심 게임의 정규화된 집계 원천.

    game_ids_json은 구버전 클라이언트 호환을 위한 캐시로 유지하고,
    랭킹·통계는 이 테이블만 사용한다. 설치가 취소되면 revoked_at으로
    제외하므로 기기 삭제/재설치에 따른 중복 집계를 막을 수 있다.
    """

    __tablename__ = "installation_games"
    __table_args__ = (
        Index("ix_installation_games_game_id", "game_id"),
    )

    installation_id: Mapped[str] = mapped_column(
        ForeignKey("installations.id", ondelete="CASCADE"), primary_key=True
    )
    game_id: Mapped[str] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    installation: Mapped[Installation] = relationship(back_populates="installation_games")
    game: Mapped[Game] = relationship(back_populates="installation_games")


class DeviceToken(Base):
    __tablename__ = "device_tokens"
    __table_args__ = (UniqueConstraint("token", name="uq_device_tokens_token"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    installation_id: Mapped[str] = mapped_column(
        ForeignKey("installations.id"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    token: Mapped[str] = mapped_column(String(512), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    installation: Mapped[Installation] = relationship(back_populates="device_tokens")


class PushOutbox(Base):
    """신뢰할 수 있는 전달: 발행 트랜잭션에서 enqueue, 워커가 발송."""

    __tablename__ = "push_outbox"
    __table_args__ = (Index("ix_push_outbox_status_available", "status", "available_at"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    installation_id: Mapped[str] = mapped_column(
        ForeignKey("installations.id"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[PushOutboxStatus] = mapped_column(
        Enum(PushOutboxStatus), nullable=False, default=PushOutboxStatus.pending, index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IngestSource(Base):
    """관리자가 설정하고 collector가 실행하는 외부 소식 소스."""

    __tablename__ = "ingest_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[IngestSourceType] = mapped_column(Enum(IngestSourceType), nullable=False)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False, index=True)
    endpoint_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # 신뢰 소스: 요약 성공 시 시스템이 draft→reviewed→published 전이를 자동 수행 (ADR-012)
    auto_publish: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    secret_env_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # 조건부 GET 캐시 (etag / last_modified / body_sha256) — collector가 갱신
    http_cache_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 페이지는 바뀌는데 아이템이 0건인 실행 연속 횟수 — 셀렉터 깨짐 감지용
    consecutive_empty_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 신뢰도 추적: 무수정 발행 / 수정 후 발행 / 자동 발행 회수 누적
    stat_approved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stat_edited: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stat_retracted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    runs: Mapped[list[IngestRun]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class AuditLog(Base):
    """관리자·시스템의 쓰기 작업 이력 (발행/회수/삭제 추적)."""

    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_created", "created_at"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor: Mapped[str] = mapped_column(String(40), nullable=False, default="admin")
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    entity: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    detail: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IngestRun(Base):
    __tablename__ = "ingest_runs"
    __table_args__ = (Index("ix_ingest_runs_status_queued", "status", "queued_at"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("ingest_sources.id"), nullable=False, index=True
    )
    status: Mapped[IngestRunStatus] = mapped_column(
        Enum(IngestRunStatus), nullable=False, default=IngestRunStatus.pending, index=True
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    items_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 변화감지(304/해시 동일)로 파싱을 건너뛴 실행 — 0건 경고에서 제외
    not_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped[IngestSource] = relationship(back_populates="runs")
