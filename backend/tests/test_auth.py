"""
SupportIQ — Auth endpoint tests.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

def test_register_customer(client):
    resp = client.post("/api/v1/auth/register", json={
        "name": "New Customer",
        "email": "newcustomer@test.com",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newcustomer@test.com"
    assert data["role"] == "CUSTOMER"


def test_register_duplicate_email(client):
    payload = {"name": "Dup", "email": "dup@test.com", "password": "pass123"}
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


def test_cannot_self_register_as_admin(client):
    resp = client.post("/api/v1/auth/register", json={
        "name": "Sneaky",
        "email": "sneaky@test.com",
        "password": "pass123",
        "role": "ADMIN",
    })
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_success(client):
    # Register then login
    client.post("/api/v1/auth/register", json={
        "name": "Login User",
        "email": "loginuser@test.com",
        "password": "testpass123",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "loginuser@test.com",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "loginuser@test.com"


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "name": "Wrong Pass",
        "email": "wrongpass@test.com",
        "password": "correct123",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "wrongpass@test.com",
        "password": "wrongpass",
    })
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------

def test_get_me_authenticated(client, customer_token):
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "customer@test.com"


def test_get_me_unauthenticated(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
