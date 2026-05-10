# -*- coding: utf-8 -*-
"""
SQLAlchemy ORM models for Amazon RDS PostgreSQL.
Tables: users, posts, community_images, incident_reports
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, Boolean, Integer, Float,
    DateTime, ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relationships
    posts: Mapped[list["CommunityPost"]] = relationship(
        "CommunityPost", back_populates="author", cascade="all, delete-orphan"
    )
    reports: Mapped[list["IncidentReport"]] = relationship(
        "IncidentReport", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.email})>"


# ─────────────────────────────────────────────
# Community Posts
# ─────────────────────────────────────────────

class CommunityPost(Base):
    __tablename__ = "community_posts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    scam_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    original_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    indicators: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array stored as text
    # S3 object key — never store the full URL, generate pre-signed URLs on demand
    image_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="posts")
    upvotes: Mapped[list["PostUpvote"]] = relationship(
        "PostUpvote", back_populates="post", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_community_posts_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CommunityPost {self.id} by user {self.user_id}>"


# ─────────────────────────────────────────────
# Post Upvotes
# ─────────────────────────────────────────────

from sqlalchemy import UniqueConstraint

class PostUpvote(Base):
    __tablename__ = "post_upvotes"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    post_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("community_posts.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    post: Mapped["CommunityPost"] = relationship("CommunityPost", back_populates="upvotes")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_upvote"),
        Index("ix_post_upvotes_post_id", "post_id"),
    )

    def __repr__(self) -> str:
        return f"<PostUpvote post={self.post_id} user={self.user_id}>"


# ─────────────────────────────────────────────
# Incident Reports
# ─────────────────────────────────────────────

class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    report_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    incident_date: Mapped[str] = mapped_column(String(20), nullable=False)
    scam_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    contact_method: Mapped[str] = mapped_column(String(100), nullable=False)
    scammer_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(200), nullable=True)
    amount_lost: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="MYR", nullable=False)
    reported_to_polis: Mapped[bool] = mapped_column(Boolean, default=False)
    reported_to_bnm: Mapped[bool] = mapped_column(Boolean, default=False)
    victim_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    victim_ic: Mapped[str | None] = mapped_column(String(20), nullable=True)
    victim_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="reports")

    __table_args__ = (
        Index("ix_incident_reports_scam_type", "scam_type"),
        Index("ix_incident_reports_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<IncidentReport {self.report_id}>"
