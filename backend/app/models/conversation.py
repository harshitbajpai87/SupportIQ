"""
SupportIQ — Conversation and Message ORM models.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class ConversationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"


class MessageSender(str, enum.Enum):
    USER = "USER"
    BOT = "BOT"
    AGENT = "AGENT"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus), default=ConversationStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations", foreign_keys=[user_id])  # type: ignore[name-defined]
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"))
    sender: Mapped[MessageSender] = mapped_column(Enum(MessageSender))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    intent_prediction: Mapped["IntentPrediction"] = relationship("IntentPrediction", back_populates="message", uselist=False)  # type: ignore[name-defined]
    feedback: Mapped[list["Feedback"]] = relationship("Feedback", back_populates="message")  # type: ignore[name-defined]


class IntentPrediction(Base):
    __tablename__ = "intent_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id"), unique=True)
    intent: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column()
    alternative_intents: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON string
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(nullable=True)
    entities: Mapped[str | None] = mapped_column(Text, nullable=True)              # JSON string
    model_version: Mapped[str] = mapped_column(String(20), default="1.0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="intent_prediction")
