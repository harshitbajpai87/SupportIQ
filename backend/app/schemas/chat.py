"""
SupportIQ — Chat Pydantic schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel
from app.models.conversation import ConversationStatus, MessageSender


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class IntentPredictionOut(BaseModel):
    intent: str
    confidence: float
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    alternative_intents: Optional[Any] = None
    entities: Optional[Any] = None
    is_fallback: bool = False

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    conversation_id: str
    sender: MessageSender
    content: str
    created_at: datetime
    intent_prediction: Optional[IntentPredictionOut] = None

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: str
    user_id: int
    title: str
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    id: str
    title: str
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageRequest(BaseModel):
    conversation_id: str
    message: str


class ChatResponse(BaseModel):
    user_message: MessageOut
    bot_message: MessageOut
    intent: str
    confidence: float
    sentiment: str
    sentiment_score: float
    escalated: bool
    escalation_reason: Optional[str] = None
    response_template: str
