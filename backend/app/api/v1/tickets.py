"""
SupportIQ — Tickets router  (/api/v1/tickets)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.ticket import SupportTicket
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketOut, TicketUpdate
from app.services.ticket_service import create_ticket, get_ticket, list_tickets, update_ticket

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketOut, status_code=201)
def create(
    data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_ticket(db=db, user_id=current_user.id, data=data)


@router.get("", response_model=list[TicketOut])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_tickets(db=db, user=current_user)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_one(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = get_ticket(db=db, ticket_id=ticket_id, user=current_user)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch(
    "/{ticket_id}",
    response_model=TicketOut,
    dependencies=[Depends(require_role(UserRole.AGENT, UserRole.ADMIN))],
)
def patch_ticket(
    ticket_id: int,
    data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return update_ticket(db=db, ticket=ticket, data=data)
