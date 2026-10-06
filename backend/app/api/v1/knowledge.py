"""
SupportIQ — Knowledge router  (/api/v1/knowledge)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.models.knowledge import KnowledgeDocument
from app.models.user import UserRole
from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentOut, KnowledgeDocumentUpdate
from app.services.knowledge_service import get_article, keyword_search

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.get("/search", response_model=list[KnowledgeDocumentOut])
def search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return keyword_search(query=q, db=db)


@router.get("", response_model=list[KnowledgeDocumentOut])
def list_docs(db: Session = Depends(get_db)):
    return db.query(KnowledgeDocument).filter(KnowledgeDocument.is_active == True).all()  # noqa: E712


@router.get("/{doc_id}", response_model=KnowledgeDocumentOut)
def get_doc(doc_id: int, db: Session = Depends(get_db)):
    doc = get_article(doc_id, db)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post(
    "",
    response_model=KnowledgeDocumentOut,
    status_code=201,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
def create_doc(data: KnowledgeDocumentCreate, db: Session = Depends(get_db)):
    doc = KnowledgeDocument(**data.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.put(
    "/{doc_id}",
    response_model=KnowledgeDocumentOut,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
def update_doc(doc_id: int, data: KnowledgeDocumentUpdate, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
def delete_doc(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.is_active = False
    db.commit()
