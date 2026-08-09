from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
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


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    initial: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    genre: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#2A2A2B")
    interest_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contents: Mapped[list[Content]] = relationship(back_populates="game")


class Content(Base):
    __tablename__ = "contents"

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
    # 자동화 재시도 대비 멱등 키 (동일 키면 기존 draft 반환)
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
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_published: Mapped[bool] = mapped_column(default=True)
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
