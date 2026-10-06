"""
SupportIQ — pytest fixtures shared across all test modules.

Uses a single in-memory SQLite connection shared across all sessions,
so tables created at startup remain visible to every request handler.
"""
from __future__ import annotations

import pathlib
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# ── Make sure app/ and ml/ are importable from backend/ ──────────────────────
_BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# ---------------------------------------------------------------------------
# Shared in-memory SQLite connection
# In-memory SQLite databases are per-connection.  We keep ONE connection open
# for the whole test session and route every session through it so the tables
# created by create_all() stay visible to all requests.
# ---------------------------------------------------------------------------

from sqlalchemy.pool import StaticPool  # noqa: E402

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,          # always returns the same underlying connection
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Import Base and create tables BEFORE importing main so the lifespan
# create_all() call is a no-op (tables already exist).
from app.database.database import Base  # noqa: E402
import app.models  # noqa: F401, E402 — register all ORM classes with Base
Base.metadata.create_all(bind=test_engine)

# Import app and wire the override
from app.core.dependencies import get_db  # noqa: E402
from app.main import app  # noqa: E402

app.dependency_overrides[get_db] = override_get_db

from app.core.security import create_access_token, hash_password  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.knowledge import KnowledgeDocument  # noqa: E402


# ---------------------------------------------------------------------------
# Session-scoped DB fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_db():
    db = TestingSessionLocal()
    yield db
    db.close()


# ---------------------------------------------------------------------------
# TestClient — lifespan runs (loads ML classifier) but create_all is a no-op
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Test users (inserted directly — no HTTP round-trip)
# ---------------------------------------------------------------------------

def _make_user(db, name, email, password, role):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return existing
    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="session")
def customer_user(test_db):
    return _make_user(test_db, "Test Customer", "customer@test.com", "testpass123", UserRole.CUSTOMER)


@pytest.fixture(scope="session")
def agent_user(test_db):
    return _make_user(test_db, "Test Agent", "agent@test.com", "testpass123", UserRole.AGENT)


@pytest.fixture(scope="session")
def admin_user(test_db):
    return _make_user(test_db, "Test Admin", "admin@test.com", "testpass123", UserRole.ADMIN)


@pytest.fixture(scope="session")
def customer_token(customer_user):
    return create_access_token({"sub": customer_user.email, "role": customer_user.role})


@pytest.fixture(scope="session")
def agent_token(agent_user):
    return create_access_token({"sub": agent_user.email, "role": agent_user.role})


@pytest.fixture(scope="session")
def admin_token(admin_user):
    return create_access_token({"sub": admin_user.email, "role": admin_user.role})


# ---------------------------------------------------------------------------
# Seed knowledge documents
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def seed_knowledge(test_db):
    if test_db.query(KnowledgeDocument).count() == 0:
        docs = [
            KnowledgeDocument(
                title="Password Reset Guide",
                category="Account",
                content="To reset your password click Forgot Password on the login page.",
                tags="password reset login",
            ),
            KnowledgeDocument(
                title="Billing FAQ",
                category="Billing",
                content="Our billing cycle is monthly. Refunds are available within 30 days.",
                tags="billing refund invoice",
            ),
            KnowledgeDocument(
                title="Order Tracking",
                category="Orders",
                content="Track your order in Account Dashboard under Orders section.",
                tags="order tracking delivery",
            ),
        ]
        test_db.add_all(docs)
        test_db.commit()
