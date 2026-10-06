"""
SupportIQ — FastAPI application entry point.

Startup (lifespan):
  - Load ML classifier once
  - Create all DB tables

CORS: allow FRONTEND_URL origin.
"""
from __future__ import annotations

import pathlib
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Ensure ml/ is importable ────────────────────────────────────────────────
_BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.core.config import settings
from app.database.database import Base, engine

# Import all models so metadata is populated before create_all()
import app.models  # noqa: F401

from app.api.v1 import auth, chat, tickets, knowledge, users, admin


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Load ML classifier once
    from ml.classifier import classifier
    if not classifier.is_loaded:
        classifier.load()

    yield
    # (nothing to clean up on shutdown for SQLite)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered customer support backend",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

_V1 = "/api/v1"
app.include_router(auth.router, prefix=_V1)
app.include_router(chat.router, prefix=_V1)
app.include_router(tickets.router, prefix=_V1)
app.include_router(knowledge.router, prefix=_V1)
app.include_router(users.router, prefix=_V1)
app.include_router(admin.router, prefix=_V1)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "SupportIQ API"}


@app.get("/", tags=["Root"])
def root():
    return {"message": "SupportIQ API v2 — visit /docs for Swagger UI"}
