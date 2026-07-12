from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.services.knowledge_service import create_knowledge, update_knowledge, delete_knowledge, get_knowledge, list_knowledge, get_related_knowledge
from app.services.embedding_service import embedding_service
from app.schemas.schemas import KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse, KnowledgeListItem, ChunkResponse

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])

@router.post("", response_model=KnowledgeResponse)
def api_create_knowledge(data: KnowledgeCreate, db: Session = Depends(get_db)):
    kn = create_knowledge(db, data)
    return _to_response(kn, db)

@router.get("", response_model=dict)
def api_list_knowledge(skip: int = 0, limit: int = 20, tag: Optional[str] = None,
                       collection_id: Optional[int] = None, search: Optional[str] = None,
                       db: Session = Depends(get_db)):
    items, total = list_knowledge(db, skip, limit, tag, collection_id, search)
    return {"items": [_to_list_item(k) for k in items], "total": total}

@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
def api_get_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    kn = get_knowledge(db, knowledge_id)
    if not kn:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    return _to_response(kn, db)

@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
def api_update_knowledge(knowledge_id: int, data: KnowledgeUpdate, db: Session = Depends(get_db)):
    kn = update_knowledge(db, knowledge_id, data)
    if not kn:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    return _to_response(kn, db)

@router.delete("/{knowledge_id}")
def api_delete_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    if not delete_knowledge(db, knowledge_id):
        raise HTTPException(status_code=404, detail="Knowledge not found")
    return {"message": "Deleted"}

@router.post("/{knowledge_id}/embed")
def api_rebuild_embedding(knowledge_id: int, db: Session = Depends(get_db)):
    kn = get_knowledge(db, knowledge_id)
    if not kn:
        raise HTTPException(status_code=404, detail="Not found")
    embedding_service.build_embeddings_for_knowledge(db, knowledge_id, getattr(embedding_service, "_active_version", "v1"))
    return {"message": "Embedding rebuilt"}

@router.get("/{knowledge_id}/chunks")
def api_get_chunks(knowledge_id: int, db: Session = Depends(get_db)):
    from app.models.models import Chunk
    chunks = db.query(Chunk).filter(Chunk.knowledge_id == knowledge_id).order_by(Chunk.chunk_index).all()
    return {"items": [{"id": c.id, "knowledge_id": c.knowledge_id, "content": c.content, "chunk_index": c.chunk_index, "token_count": c.token_count} for c in chunks]}

@router.get("/{knowledge_id}/related")
def api_get_related(knowledge_id: int, db: Session = Depends(get_db)):
    related = get_related_knowledge(db, knowledge_id)
    return {"items": [_to_list_item(k) for k in related]}

def _to_response(kn, db):
    tags = []
    for kt in kn.tags:
        if kt.tag:
            tags.append(kt.tag.name)
    collections = []
    from app.models.models import CollectionItem, Collection
    items = db.query(CollectionItem).filter(CollectionItem.knowledge_id == kn.id).all()
    for item in items:
        c = db.query(Collection).filter(Collection.id == item.collection_id).first()
        if c:
            collections.append({"id": c.id, "name": c.name})
    return {
        "id": kn.id, "title": kn.title, "content": kn.content, "summary": kn.summary,
        "source": kn.source, "source_url": kn.source_url or "", "file_type": kn.file_type,
        "metadata": kn.metadata_json or {}, "token_count": kn.token_count, "chunk_count": kn.chunk_count,
        "is_active": kn.is_active, "tags": tags, "collections": collections,
        "created_at": kn.created_at.isoformat() if kn.created_at else None,
        "updated_at": kn.updated_at.isoformat() if kn.updated_at else None
    }

def _to_list_item(kn):
    tags = [kt.tag.name for kt in kn.tags if kt.tag] if hasattr(kn, 'tags') else []
    return {
        "id": kn.id, "title": kn.title, "summary": kn.summary, "source": kn.source,
        "file_type": kn.file_type, "token_count": kn.token_count, "chunk_count": kn.chunk_count,
        "tags": tags,
        "created_at": kn.created_at.isoformat() if kn.created_at else None,
        "updated_at": kn.updated_at.isoformat() if kn.updated_at else None
    }

