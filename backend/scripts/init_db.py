"""
SupportIQ — Database initialisation and seed script.

Usage:
    cd supportiq/backend
    venv/Scripts/python.exe scripts/init_db.py

Optional env vars:
    ADMIN_EMAIL     — email for the bootstrap admin account
    ADMIN_PASSWORD  — password for the bootstrap admin account
"""
from __future__ import annotations

import os
import pathlib
import sys

# Ensure app/ and ml/ are importable
_BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

# Load .env if present
from dotenv import load_dotenv
load_dotenv(_BACKEND_DIR / ".env")

from app.database.database import Base, engine, SessionLocal
import app.models  # noqa: F401 — populates Base.metadata
from app.models.user import User, UserRole
from app.models.knowledge import KnowledgeDocument
from app.core.security import hash_password

# ---------------------------------------------------------------------------
# Create all tables
# ---------------------------------------------------------------------------

print("Creating database tables …")
Base.metadata.create_all(bind=engine)
print("  [OK] Tables created")

# ---------------------------------------------------------------------------
# Seed knowledge documents
# ---------------------------------------------------------------------------

SEED_DOCS = [
    {
        "title": "How to Reset Your Password",
        "category": "Account",
        "content": (
            "To reset your SupportIQ Demo Services password, navigate to the login page "
            "and click 'Forgot Password'. Enter your registered email address and check "
            "your inbox for a reset link (valid 30 minutes). If you don't receive it, "
            "check your spam folder or contact support@supportiq.demo."
        ),
        "tags": "password reset login account",
        "source": "SupportIQ Help Centre",
    },
    {
        "title": "Billing & Subscription Plans",
        "category": "Billing",
        "content": (
            "SupportIQ Demo Services offers three plans: Starter ($9/mo), Professional ($29/mo), "
            "and Enterprise (custom pricing). Billing is monthly by default; annual plans receive "
            "a 20% discount. All plans include a 14-day free trial — no credit card required. "
            "Invoices are sent by email on the 1st of each month."
        ),
        "tags": "billing subscription plan pricing invoice",
        "source": "SupportIQ Billing Guide",
    },
    {
        "title": "Requesting a Refund",
        "category": "Billing",
        "content": (
            "SupportIQ Demo Services offers a 30-day money-back guarantee for new subscribers. "
            "To request a refund, email billing@supportiq.demo with your account email and "
            "invoice number. Refunds are processed within 5–7 business days to the original "
            "payment method. Partial refunds for mid-cycle cancellations are not available."
        ),
        "tags": "refund billing money back cancellation",
        "source": "SupportIQ Refund Policy",
    },
    {
        "title": "Tracking Your Order or Delivery",
        "category": "Orders",
        "content": (
            "After purchase, SupportIQ Demo Services sends a confirmation email with an order ID. "
            "You can track your order status by logging in to your account and visiting "
            "Dashboard → Orders. Physical deliveries use DHL; tracking numbers are emailed within "
            "24 hours of dispatch. For delays beyond 7 business days, contact orders@supportiq.demo."
        ),
        "tags": "order tracking delivery shipment status",
        "source": "SupportIQ Order Help",
    },
    {
        "title": "How to Cancel Your Subscription",
        "category": "Billing",
        "content": (
            "To cancel your SupportIQ Demo Services subscription, go to Account Settings → "
            "Subscription → Cancel Plan. Your access continues until the end of the current "
            "billing period. Cancellation is immediate for free-trial accounts. "
            "You can reactivate at any time from the same settings page."
        ),
        "tags": "cancel subscription plan billing account",
        "source": "SupportIQ Help Centre",
    },
    {
        "title": "Requesting Account Deletion",
        "category": "Account",
        "content": (
            "To permanently delete your SupportIQ Demo Services account, go to Account Settings → "
            "Privacy → Delete Account and follow the confirmation steps. All personal data is "
            "removed within 30 days in compliance with GDPR. This action is irreversible. "
            "Download your data export before proceeding."
        ),
        "tags": "delete account privacy GDPR data removal",
        "source": "SupportIQ Privacy Policy",
    },
    {
        "title": "Contacting Customer Support",
        "category": "Support",
        "content": (
            "SupportIQ Demo Services support is available Monday–Friday 9 am – 6 pm UTC. "
            "You can reach us via: (1) Live chat on this page, (2) Email: support@supportiq.demo "
            "(response within 24 h), (3) Phone: +1-800-SUPPORT (Enterprise plan only). "
            "For critical issues, use the 'Escalate to Agent' button in chat."
        ),
        "tags": "contact support help email phone chat agent",
        "source": "SupportIQ Contact Page",
    },
    {
        "title": "API Integration & Webhooks",
        "category": "Integrations",
        "content": (
            "SupportIQ Demo Services provides a REST API (v2) and webhook support for third-party "
            "integrations. Generate API keys from Developer Settings. Rate limit: 1000 requests/min "
            "on Professional, unlimited on Enterprise. Webhooks support events: ticket.created, "
            "ticket.updated, conversation.escalated. See api.supportiq.demo/docs for full reference."
        ),
        "tags": "API integration webhook developer REST key",
        "source": "SupportIQ Developer Docs",
    },
    {
        "title": "Upgrading Your Plan",
        "category": "Billing",
        "content": (
            "To upgrade from Starter to Professional or Enterprise, go to Account Settings → "
            "Subscription → Change Plan. Upgrades take effect immediately and are prorated for "
            "the remainder of the billing cycle. Enterprise plans require a call with our sales team "
            "— book at sales.supportiq.demo or email sales@supportiq.demo."
        ),
        "tags": "upgrade plan billing professional enterprise",
        "source": "SupportIQ Help Centre",
    },
    {
        "title": "Troubleshooting Login Issues",
        "category": "Account",
        "content": (
            "If you cannot log in to SupportIQ Demo Services: (1) Ensure Caps Lock is off. "
            "(2) Clear your browser cache and cookies. (3) Try an incognito/private window. "
            "(4) Use the 'Forgot Password' link to reset your credentials. "
            "(5) If your account appears locked, wait 15 minutes or contact support@supportiq.demo."
        ),
        "tags": "login issue locked account password browser",
        "source": "SupportIQ Help Centre",
    },
]


def seed_knowledge(db):
    existing = db.query(KnowledgeDocument).count()
    if existing >= len(SEED_DOCS):
        print(f"  [SKIP] Knowledge docs already seeded ({existing} found), skipping")
        return
    count = 0
    for doc_data in SEED_DOCS:
        doc = KnowledgeDocument(**doc_data)
        db.add(doc)
        count += 1
    db.commit()
    print(f"  [OK] Seeded {count} knowledge documents")


# ---------------------------------------------------------------------------
# Optional admin user
# ---------------------------------------------------------------------------

def maybe_create_admin(db):
    email = os.environ.get("ADMIN_EMAIL", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "").strip()
    if not email or not password:
        print("  [SKIP] ADMIN_EMAIL/ADMIN_PASSWORD not set -- skipping admin creation")
        return
    if db.query(User).filter(User.email == email).first():
        print(f"  [SKIP] Admin '{email}' already exists, skipping")
        return
    admin = User(
        name="Admin",
        email=email,
        hashed_password=hash_password(password),
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()
    print(f"  [OK] Admin user created: {email}")



# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    db = SessionLocal()
    try:
        print("\nSeeding knowledge documents …")
        seed_knowledge(db)
        print("\nCreating admin user …")
        maybe_create_admin(db)
        print("\nDone.")
    finally:
        db.close()
