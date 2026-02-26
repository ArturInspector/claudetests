from datetime import datetime
from typing import List
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Session(Base):
    """Learning session with multiple iterations."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    topic: Mapped[str] = mapped_column(String(255))
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    user: Mapped["User"] = relationship(back_populates="sessions")
    iterations: Mapped[List["Iteration"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Iteration.number",
    )
    messages: Mapped[List["Message"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.timestamp",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Session(id={self.id!r}, topic={self.topic!r})"


class Iteration(Base):
    """Single iteration with question/answer/feedback."""

    __tablename__ = "iterations"
    __table_args__ = (
        UniqueConstraint("session_id", "number", name="uq_session_iteration_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    session: Mapped["Session"] = relationship(back_populates="iterations")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Iteration(id={self.id!r}, number={self.number!r})"


class Message(Base):
    """Chat message in a session."""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text)
    analysis_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.text("now()")
    )

    session: Mapped["Session"] = relationship(back_populates="messages")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Message(id={self.id!r}, role={self.role!r}, session_id={self.session_id!r})"

