"""
SupportIQ — Escalation determination and ticket creation service.

Escalation triggers:
  1. Confidence below threshold
  2. Intent == "escalation_request"
  3. Intent in the auto-escalate set
  4. Negative sentiment with strong intensity
  5. Priority is CRITICAL
"""
from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timezone

# Allow importing from ml/ package
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ticket import SupportTicket, TicketPriority, TicketStatus
from app.services.priority_service import determine_priority

_AUTO_ESCALATE_INTENTS = {
    "escalation_request",
    "account_delete",
    "billing_refund_request",
    "tech_integration_issue",
    "general_complaint",
}


def should_escalate(
    intent: str,
    confidence: float,
    sentiment_label: str,
    sentiment_intensity: str,
    priority: TicketPriority,
) -> tuple[bool, str]:
    """
    Return (escalate: bool, reason: str).

    Check in order:
      1. Low confidence → fallback
      2. Explicit escalation request
      3. High-risk intents
      4. Negative + strong sentiment
      5. CRITICAL priority
    """
    if confidence < settings.CONFIDENCE_THRESHOLD:
        return True, "Low confidence — intent unclear, requires human review"

    if intent == "escalation_request":
        return True, "Customer explicitly requested escalation to a human agent"

    if intent in _AUTO_ESCALATE_INTENTS:
        return True, f"Intent '{intent}' requires agent review by policy"

    if sentiment_label == "negative" and sentiment_intensity == "strong":
        return True, "Strong negative sentiment detected — customer may be distressed"

    if priority == TicketPriority.CRITICAL:
        return True, "Critical priority ticket requires immediate agent attention"

    return False, ""


def create_escalation_ticket(
    db: Session,
    user_id: int,
    conversation_id: str | None,
    subject: str,
    description: str,
    reason: str,
    intent: str,
    sentiment: str,
    priority: TicketPriority,
) -> SupportTicket:
    """Persist an escalation ticket and return it."""
    ticket = SupportTicket(
        ticket_number="PENDING",   # will be replaced after flush
        user_id=user_id,
        conversation_id=conversation_id,
        subject=subject,
        description=description,
        detected_intent=intent,
        sentiment=sentiment,
        priority=priority,
        status=TicketStatus.ESCALATED,
        escalation_reason=reason,
    )
    db.add(ticket)
    db.flush()   # assigns ticket.id
    ticket.ticket_number = f"SUP-{ticket.id:06d}"
    db.commit()
    db.refresh(ticket)
    return ticket
