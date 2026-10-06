"""
SupportIQ — Knowledge endpoint tests.
"""
from __future__ import annotations

import pytest


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

def test_get_knowledge_list(client):
    resp = client.get("/api/v1/knowledge")
    assert resp.status_code == 200
    docs = resp.json()
    assert isinstance(docs, list)
    assert len(docs) > 0


def test_search_knowledge(client):
    resp = client.get("/api/v1/knowledge/search?q=password")
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    # At least one seeded doc should match "password"
    assert len(results) >= 1
    titles = [r["title"].lower() for r in results]
    assert any("password" in t for t in titles)


# ---------------------------------------------------------------------------
# Admin-only write operations
# ---------------------------------------------------------------------------

def test_admin_create_knowledge(client, admin_token):
    resp = client.post(
        "/api/v1/knowledge",
        json={
            "title": "Test Admin Article",
            "category": "Testing",
            "content": "This is a test article created by the admin.",
            "tags": "test admin",
        },
        headers=_auth(admin_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Admin Article"
    assert data["is_active"] is True


def test_non_admin_cannot_create_knowledge(client, customer_token):
    resp = client.post(
        "/api/v1/knowledge",
        json={
            "title": "Unauthorized Article",
            "category": "Testing",
            "content": "This should not be created.",
        },
        headers=_auth(customer_token),
    )
    assert resp.status_code == 403
