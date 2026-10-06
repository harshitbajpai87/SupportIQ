"""
SupportIQ — Ticket CRUD service.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ticket import SupportTicket, TicketPriority, TicketStatus
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketUpdate


def create_ticket(
    db: Session,
    user_id: int,
    data: TicketCreate,
    detected_intent: str | None = None,
    sentiment: str | None = None,
) -> SupportTicket:
    ticket = SupportTicket(
        ticket_number="PENDING",
        user_id=user_id,
        conversation_id=data.conversation_id,
        subject=data.subject,
        description=data.description,
        detected_intent=detected_intent,
        sentiment=sentiment,
        priority=data.priority,
        status=TicketStatus.OPEN,
    )
    db.add(ticket)
    db.flush()
    ticket.ticket_number = f"SUP-{ticket.id:06d}"
    db.commit()
    db.refresh(ticket)
    return ticket


def list_tickets(db: Session, user: User) -> list[SupportTicket]:
    """Customers see own, agents see assigned, admins see all."""
    if user.role == UserRole.ADMIN:
        return db.query(SupportTicket).all()
    elif user.role == UserRole.AGENT:
        return (
            db.query(SupportTicket)
            .filter(SupportTicket.assigned_agent_id == user.id)
            .all()
        )
    else:
        return db.query(SupportTicket).filter(SupportTicket.user_id == user.id).all()


def get_ticket(db: Session, ticket_id: int, user: User) -> SupportTicket | None:
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if ticket is None:
        return None
    if user.role == UserRole.CUSTOMER and ticket.user_id != user.id:
        return None
    if user.role == UserRole.AGENT and ticket.assigned_agent_id != user.id:
        return None
    return ticket


def update_ticket(db: Session, ticket: SupportTicket, data: TicketUpdate) -> SupportTicket:
    if data.status is not None:
        ticket.status = data.status
    if data.priority is not None:
        ticket.priority = data.priority
    if data.assigned_agent_id is not None:
        ticket.assigned_agent_id = data.assigned_agent_id
    if data.escalation_reason is not None:
        ticket.escalation_reason = data.escalation_reason
    db.commit()
    db.refresh(ticket)
    return ticket
