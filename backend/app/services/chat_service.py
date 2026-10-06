"""
SupportIQ — Chat service (THE CORE).

Integrates the Phase 1 ML pipeline with the FastAPI request/response cycle.
The ML classifier is loaded ONCE at app startup via FastAPI lifespan; this
module just calls it for every message.

Flow per message:
  1. Call classifier.predict(text) → IntentResult
  2. Call extract_entities(text) → Entities
  3. Call analyse(text) → SentimentResult
  4. Check escalation logic
  5. Persist: Message(USER), Message(BOT), IntentPrediction
  6. Return ChatResponse
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

from sqlalchemy.orm import Session

# Ensure ml/ package is importable
_BACKEND_DIR = pathlib.Path(__file__).resolve().parents[3]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from ml.classifier import classifier
from ml.entity_extractor import extract_entities
from ml.sentiment import analyse

from app.core.config import settings
from app.models.conversation import (
    Conversation,
    ConversationStatus,
    IntentPrediction,
    Message,
    MessageSender,
)
from app.schemas.chat import ChatResponse, MessageOut, IntentPredictionOut
from app.services.escalation_service import should_escalate
from app.services.priority_service import determine_priority


def process_message(
    db: Session,
    conversation_id: str,
    user_id: int,
    text: str,
) -> ChatResponse:
    """
    Core chat handler.

    Parameters
    ----------
    db              : Active SQLAlchemy session
    conversation_id : UUID string of the conversation
    user_id         : Authenticated user's primary key
    text            : Raw user message

    Returns
    -------
    ChatResponse Pydantic model
    """
    # ── 1. Verify conversation belongs to user ─────────────────────────────
    conversation: Conversation | None = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if conversation is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # ── 2. ML pipeline calls ────────────────────────────────────────────────
    intent_result = classifier.predict(text)
    sentiment_result = analyse(text)
    entities = extract_entities(text)

    # ── 3. Escalation & priority ────────────────────────────────────────────
    priority = determine_priority(
        intent_name=intent_result.intent,
        sentiment_label=sentiment_result.label,
        sentiment_intensity=sentiment_result.intensity,
        confidence=intent_result.confidence,
    )
    escalated, escalation_reason = should_escalate(
        intent=intent_result.intent,
        confidence=intent_result.confidence,
        sentiment_label=sentiment_result.label,
        sentiment_intensity=sentiment_result.intensity,
        priority=priority,
    )

    # ── 4. Build bot reply ──────────────────────────────────────────────────
    if escalated:
        bot_text = (
            "I've flagged this for one of our support agents who will be in touch shortly. "
            f"Reason: {escalation_reason}"
        )
        # Update conversation status
        conversation.status = ConversationStatus.ESCALATED
    else:
        bot_text = intent_result.response_template

    # ── 5. Persist messages ─────────────────────────────────────────────────
    user_msg = Message(
        conversation_id=conversation_id,
        sender=MessageSender.USER,
        content=text,
    )
    db.add(user_msg)
    db.flush()

    bot_msg = Message(
        conversation_id=conversation_id,
        sender=MessageSender.BOT,
        content=bot_text,
    )
    db.add(bot_msg)
    db.flush()

    # ── 6. Persist IntentPrediction (for user message only) ─────────────────
    prediction = IntentPrediction(
        message_id=user_msg.id,
        intent=intent_result.intent,
        confidence=intent_result.confidence,
        alternative_intents=json.dumps(intent_result.alternatives),
        sentiment=sentiment_result.label,
        sentiment_score=sentiment_result.compound,
        entities=json.dumps(entities.to_dict()),
        model_version=settings.MODEL_VERSION,
    )
    db.add(prediction)
    db.commit()
    db.refresh(user_msg)
    db.refresh(bot_msg)
    db.refresh(prediction)

    # ── 7. Build response ───────────────────────────────────────────────────
    prediction_out = IntentPredictionOut(
        intent=prediction.intent,
        confidence=prediction.confidence,
        sentiment=prediction.sentiment,
        sentiment_score=prediction.sentiment_score,
        alternative_intents=intent_result.alternatives,
        entities=entities.to_dict(),
        is_fallback=intent_result.is_fallback,
    )

    user_msg_out = MessageOut(
        id=user_msg.id,
        conversation_id=user_msg.conversation_id,
        sender=user_msg.sender,
        content=user_msg.content,
        created_at=user_msg.created_at,
        intent_prediction=prediction_out,
    )
    bot_msg_out = MessageOut(
        id=bot_msg.id,
        conversation_id=bot_msg.conversation_id,
        sender=bot_msg.sender,
        content=bot_msg.content,
        created_at=bot_msg.created_at,
    )

    return ChatResponse(
        user_message=user_msg_out,
        bot_message=bot_msg_out,
        intent=intent_result.intent,
        confidence=intent_result.confidence,
        sentiment=sentiment_result.label,
        sentiment_score=sentiment_result.compound,
        escalated=escalated,
        escalation_reason=escalation_reason if escalated else None,
        response_template=intent_result.response_template,
    )
