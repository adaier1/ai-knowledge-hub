from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.services.search_service import hybrid_search, search_by_tag, search_by_collection, log_search
from app.services.embedding_service import embedding_service
from app.schemas.schemas import SearchRequest, SearchResult
import time

router = APIRouter(prefix="/api/search", tags=["Search"])

@router.post("")
def api_search(req: SearchRequest, db: Session = Depends(get_db)):
    start = time.time()
    results = []
    if req.search_type in ("hybrid", "keyword"):
        results = hybrid_search(db, req.query, req.limit, req.offset, req.collections, req.tags)
    elif req.search_type == "semantic":
        try:
            results = embedding_service.semantic_search(db, req.query, req.limit)
        except Exception:
            results = hybrid_search(db, req.query, req.limit, req.offset, req.collections, req.tags)
    elif req.search_type == "tag":
        for t in req.tags:
            results += search_by_tag(db, t, req.limit, req.offset)
    elif req.search_type == "collection":
        for cid in req.collections:
            results += search_by_collection(db, cid, req.limit, req.offset)
    latency = (time.time() - start) * 1000
    log_search(db, req.query, req.search_type, results, latency)
    return {"results": results[:req.limit], "total": len(results), "latency_ms": round(latency, 2)}

@router.get("/logs")
def api_search_logs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    from app.models.models import SearchLog
    logs = db.query(SearchLog).order_by(SearchLog.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [{
        "id": l.id, "query": l.query, "search_type": l.search_type,
        "results_count": l.results_count, "latency_ms": l.latency_ms,
        "hit": l.hit, "score": l.score, "source": l.source,
        "agent_name": l.agent_name, "llm_model": l.llm_model,
        "created_at": l.created_at.isoformat() if l.created_at else None
    } for l in logs], "total": db.query(SearchLog).count()}
