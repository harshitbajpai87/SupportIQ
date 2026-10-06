"""
SupportIQ — Ticket Pydantic schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.models.ticket import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    subject: str
    description: str
    conversation_id: Optional[str] = None
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_agent_id: Optional[int] = None
    escalation_reason: Optional[str] = None


class TicketOut(BaseModel):
    id: int
    ticket_number: str
    user_id: int
    conversation_id: Optional[str] = None
    subject: str
    description: str
    detected_intent: Optional[str] = None
    sentiment: Optional[str] = None
    priority: TicketPriority
    status: TicketStatus
    assigned_agent_id: Optional[int] = None
    escalation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
