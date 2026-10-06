"""
SupportIQ — Admin router  (/api/v1/admin)
All endpoints require ADMIN role except create-admin (uses ADMIN_SECRET_KEY).
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.core.security import hash_password
from app.models.ticket import SupportTicket
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserOut

router = APIRouter(prefix="/admin", tags=["Admin"])

_admin_only = Depends(require_role(UserRole.ADMIN))


@router.get("/users", response_model=list[UserOut], dependencies=[_admin_only])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.patch("/users/{user_id}", response_model=UserOut, dependencies=[_admin_only])
def update_user_role(
    user_id: int,
    role: UserRole,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.commit()
    db.refresh(user)
    return user


@router.get("/stats", dependencies=[_admin_only])
def get_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_tickets = db.query(SupportTicket).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == "OPEN").count()
    escalated_tickets = db.query(SupportTicket).filter(SupportTicket.status == "ESCALATED").count()
    return {
        "total_users": total_users,
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "escalated_tickets": escalated_tickets,
    }


@router.post("/create-admin", response_model=UserOut, status_code=201)
def create_admin(data: UserCreate, admin_secret: str, db: Session = Depends(get_db)):
    """Bootstrap endpoint — protected by ADMIN_SECRET_KEY env var (dev only)."""
    expected = os.environ.get("ADMIN_SECRET_KEY", "dev-admin-secret")
    if admin_secret != expected:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=UserRole.ADMIN,
        preferred_language=data.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
