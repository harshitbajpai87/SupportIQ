"""
SupportIQ — Chat endpoint tests.

These tests call the real ML classifier (Phase 1 pipeline).
"""
from __future__ import annotations

import pytest


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------

def test_create_conversation(client, customer_token):
    resp = client.post(
        "/api/v1/chat/conversations",
        json={"title": "Test Conversation"},
        headers=_auth(customer_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Conversation"
    assert "id" in data


def test_send_message_returns_intent(client, customer_token):
    # Create a conversation first
    conv_resp = client.post(
        "/api/v1/chat/conversations",
        json={"title": "Intent Test"},
        headers=_auth(customer_token),
    )
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["id"]

    # Send a clear message the classifier should handle
    resp = client.post(
        "/api/v1/chat/message",
        json={"conversation_id": conv_id, "message": "I can't log into my account"},
        headers=_auth(customer_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "intent" in data
    assert "confidence" in data
    assert data["confidence"] > 0.0
    assert "sentiment" in data
    assert "bot_message" in data
    assert data["bot_message"]["content"] != ""


def test_send_message_low_confidence(client, customer_token):
    """Nonsense input should trigger fallback / escalation."""
    conv_resp = client.post(
        "/api/v1/chat/conversations",
        json={"title": "Low Confidence"},
        headers=_auth(customer_token),
    )
    conv_id = conv_resp.json()["id"]

    resp = client.post(
        "/api/v1/chat/message",
        json={"conversation_id": conv_id, "message": "xyzzy abc 123 zzz"},
        headers=_auth(customer_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    # Low-confidence messages are escalated
    assert data["escalated"] is True


def test_conversation_isolation(client, customer_token, admin_token):
    """A user cannot retrieve another user's conversation."""
    # Customer creates a conversation
    conv_resp = client.post(
        "/api/v1/chat/conversations",
        json={"title": "Private Conv"},
        headers=_auth(customer_token),
    )
    conv_id = conv_resp.json()["id"]

    # Admin tries to fetch it (different user → 404)
    resp = client.get(
        f"/api/v1/chat/conversations/{conv_id}",
        headers=_auth(admin_token),
    )
    assert resp.status_code == 404


def test_intent_prediction_persisted(client, customer_token, test_db):
    """After sending a message the IntentPrediction row should exist."""
    from app.models.conversation import IntentPrediction

    conv_resp = client.post(
        "/api/v1/chat/conversations",
        json={"title": "Persist Test"},
        headers=_auth(customer_token),
    )
    conv_id = conv_resp.json()["id"]

    client.post(
        "/api/v1/chat/message",
        json={"conversation_id": conv_id, "message": "Please refund my last payment"},
        headers=_auth(customer_token),
    )

    count = test_db.query(IntentPrediction).count()
    assert count > 0
