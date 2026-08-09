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


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    initial: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    genre: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#2A2A2B")
    interest_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contents: Mapped[list[Content]] = relationship(back_populates="game")


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
    place: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reservation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
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
