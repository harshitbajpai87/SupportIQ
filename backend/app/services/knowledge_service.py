"""
SupportIQ — Knowledge document service.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeDocument


def keyword_search(query: str, db: Session) -> list[KnowledgeDocument]:
    """
    Simple keyword search over title, content, and tags using SQL LIKE.
    Tokenises the query and returns documents matching ANY token.
    """
    if not query or not query.strip():
        return []

    tokens = [t.strip() for t in query.split() if len(t.strip()) >= 2]
    if not tokens:
        return []

    results = (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.is_active == True)  # noqa: E712
        .all()
    )

    matched: list[KnowledgeDocument] = []
    seen: set[int] = set()
    for token in tokens:
        token_lower = token.lower()
        for doc in results:
            if doc.id in seen:
                continue
            haystack = " ".join(
                filter(None, [doc.title, doc.content, doc.tags or ""])
            ).lower()
            if token_lower in haystack:
                matched.append(doc)
                seen.add(doc.id)

    return matched


def get_article(article_id: int, db: Session) -> KnowledgeDocument | None:
    return (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.id == article_id, KnowledgeDocument.is_active == True)  # noqa: E712
        .first()
    )
