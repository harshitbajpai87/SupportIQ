"""
SupportIQ — Knowledge Pydantic schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class KnowledgeDocumentCreate(BaseModel):
    title: str
    category: str
    content: str
    source: Optional[str] = None
    tags: Optional[str] = None


class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeDocumentOut(BaseModel):
    id: int
    title: str
    category: str
    content: str
    source: Optional[str] = None
    tags: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
