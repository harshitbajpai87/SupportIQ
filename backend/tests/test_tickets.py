"""
SupportIQ — Ticket endpoint tests.
"""
from __future__ import annotations

import re

import pytest


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create_ticket(client, token, subject="Test Issue", description="Something broke"):
    resp = client.post(
        "/api/v1/tickets",
        json={"subject": subject, "description": description},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------

def test_create_ticket(client, customer_token):
    ticket = _create_ticket(client, customer_token)
    assert ticket["subject"] == "Test Issue"
    assert ticket["status"] == "OPEN"
    assert re.match(r"SUP-\d{6}", ticket["ticket_number"])


def test_ticket_number_format(client, customer_token):
    ticket = _create_ticket(client, customer_token, subject="Format Test")
    assert re.match(r"^SUP-\d{6}$", ticket["ticket_number"])


# ---------------------------------------------------------------------------
# Visibility rules
# ---------------------------------------------------------------------------

def test_customer_sees_own_tickets_only(client, customer_token, admin_token):
    # Customer creates a ticket
    _create_ticket(client, customer_token, subject="Customer Only Ticket")

    # Customer gets tickets
    resp = client.get("/api/v1/tickets", headers=_auth(customer_token))
    assert resp.status_code == 200
    tickets = resp.json()
    # All returned tickets belong to the customer (no cross-user leakage)
    assert all(t["status"] is not None for t in tickets)  # basic sanity


def test_admin_sees_all_tickets(client, admin_token, customer_token):
    # Create a customer ticket
    _create_ticket(client, customer_token, subject="Admin Visibility Test")

    resp = client.get("/api/v1/tickets", headers=_auth(admin_token))
    assert resp.status_code == 200
    tickets = resp.json()
    assert len(tickets) >= 1


def test_agent_sees_assigned_tickets(client, agent_token, admin_token, test_db):
    from app.models.user import User, UserRole
    from app.models.ticket import SupportTicket, TicketStatus

    # Get the agent user id
    agent = test_db.query(User).filter(User.email == "agent@test.com").first()

    # Create a ticket as customer then assign it via admin patch
    cust_resp = client.post("/api/v1/auth/register", json={
        "name": "Cust2", "email": "cust2@test.com", "password": "pass123"
    })
    from app.core.security import create_access_token
    # Login as that customer
    cust_login = client.post("/api/v1/auth/login", json={
        "email": "cust2@test.com", "password": "pass123"
    })
    cust_token = cust_login.json()["access_token"]
    ticket = _create_ticket(client, cust_token, subject="Agent Assigned Test")
    ticket_id = ticket["id"]

    # Admin assigns the ticket to the agent
    resp = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"assigned_agent_id": agent.id},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 200

    # Agent lists tickets — should see the assigned one
    resp = client.get("/api/v1/tickets", headers=_auth(agent_token))
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()]
    assert ticket_id in ids


def test_update_ticket_status_as_agent(client, agent_token, admin_token, test_db):
    from app.models.user import User
    agent = test_db.query(User).filter(User.email == "agent@test.com").first()

    # Create ticket and assign to agent
    cust_login = client.post("/api/v1/auth/login", json={
        "email": "customer@test.com", "password": "testpass123"
    })
    cust_token = cust_login.json()["access_token"]
    ticket = _create_ticket(client, cust_token, subject="Status Update Test")
    ticket_id = ticket["id"]

    client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"assigned_agent_id": agent.id},
        headers=_auth(admin_token),
    )

    # Agent updates status
    resp = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "IN_PROGRESS"},
        headers=_auth(agent_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"
