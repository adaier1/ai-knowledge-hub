import time, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, or_
from app.models.models import Knowledge, Chunk, Tag, KnowledgeTag, CollectionItem, SearchLog, Embedding
from app.services.embedding_service import embedding_service

def search_keyword(db: Session, query: str, limit: int = 10, offset: int = 0):
    try:
        q = query.replace("'", "''")
        sql = text(f"SELECT rowid, rank FROM knowledge_fts WHERE knowledge_fts MATCH '\"{q}\"' ORDER BY rank LIMIT {limit} OFFSET {offset}")
        results = db.execute(sql).fetchall()
        ids = [r[0] for r in results]
        scores = {r[0]: 1.0 / (1.0 + abs(r[1])) for r in results} if results else {}
        knowledges = db.query(Knowledge).filter(Knowledge.id.in_(ids or [0])).all()
        kn_map = {k.id: k for k in knowledges}
        return [{"knowledge_id": kid, "chunk_id": 0, "title": kn_map[kid].title, "content": (kn_map[kid].content or "")[:300], "score": scores.get(kid, 0.0), "source": "keyword"} for kid in ids if kid in kn_map]
    except Exception:
        q = f"%{query}%"
        results = db.query(Knowledge).filter(
            or_(Knowledge.title.ilike(q), Knowledge.content.ilike(q)),
            Knowledge.is_active == True
        ).limit(limit).offset(offset).all()
        return [{"knowledge_id": k.id, "chunk_id": 0, "title": k.title, "content": (k.content or "")[:300], "score": 0.5, "source": "keyword"} for k in results]

def hybrid_search(db: Session, query: str, limit: int = 10, offset: int = 0,
                  collections: Optional[List[int]] = None, tags: Optional[List[str]] = None):
    """混合搜索：关键词搜索 + 语义搜索"""
    kw_results = search_keyword(db, query, limit, offset)
    # 添加语义搜索结果
    try:
        semantic_results = embedding_service.semantic_search(db, query, limit)
        # 合并结果，去重，按分数排序
        seen_ids = set()
        combined = []
        for r in kw_results + semantic_results:
            kid = r["knowledge_id"]
            if kid not in seen_ids:
                seen_ids.add(kid)
                combined.append(r)
        combined.sort(key=lambda x: x["score"], reverse=True)
        kw_results = combined[:limit]
    except Exception:
        pass
    if collections:
        filtered = []
        for r in kw_results:
            items = db.query(CollectionItem).filter(
                CollectionItem.knowledge_id == r["knowledge_id"],
                CollectionItem.collection_id.in_(collections)
            ).count()
            if items > 0:
                filtered.append(r)
        kw_results = filtered
    if tags:
        filtered = []
        for r in kw_results:
            ktags = db.query(KnowledgeTag).join(Tag).filter(
                KnowledgeTag.knowledge_id == r["knowledge_id"],
                Tag.name.in_(tags)
            ).count()
            if ktags > 0:
                filtered.append(r)
        kw_results = filtered
    return kw_results

def search_by_tag(db: Session, tag: str, limit: int = 10, offset: int = 0):
    tag_obj = db.query(Tag).filter(Tag.name == tag).first()
    if not tag_obj:
        return []
    kts = db.query(KnowledgeTag).filter(KnowledgeTag.tag_id == tag_obj.id).offset(offset).limit(limit).all()
    kn_ids = [kt.knowledge_id for kt in kts]
    knowledges = db.query(Knowledge).filter(Knowledge.id.in_(kn_ids or [0])).all()
    kn_map = {k.id: k for k in knowledges}
    return [{"knowledge_id": kid, "chunk_id": 0, "title": kn_map[kid].title, "content": (kn_map[kid].content or "")[:300], "score": 1.0, "source": "tag"} for kid in kn_ids if kid in kn_map]

def search_by_collection(db: Session, collection_id: int, limit: int = 10, offset: int = 0):
    items = db.query(CollectionItem).filter(
        CollectionItem.collection_id == collection_id
    ).offset(offset).limit(limit).all()
    kn_ids = [i.knowledge_id for i in items]
    knowledges = db.query(Knowledge).filter(Knowledge.id.in_(kn_ids or [0])).all()
    kn_map = {k.id: k for k in knowledges}
    return [{"knowledge_id": kid, "chunk_id": 0, "title": kn_map[kid].title, "content": (kn_map[kid].content or "")[:300], "score": 1.0, "source": "collection"} for kid in kn_ids if kid in kn_map]

def log_search(db: Session, query: str, search_type: str, results: list, latency_ms: float,
               source: str = "webui", agent: str = "", llm: str = ""):
    log = SearchLog(
        query=query, search_type=search_type, results_count=len(results),
        top_chunk_ids=[r.get("chunk_id", 0) for r in results[:10]],
        final_context="\n\n".join([r.get("content", "")[:500] for r in results[:3]]),
        latency_ms=latency_ms, hit=len(results) > 0,
        score=results[0].get("score", 0.0) if results else 0.0,
        source=source, agent_name=agent, llm_model=llm
    )
    db.add(log)
    db.commit()
