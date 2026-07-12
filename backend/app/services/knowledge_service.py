import datetime, re, hashlib
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, or_
from app.models.models import Knowledge, Chunk, Embedding, Tag, KnowledgeTag, Collection, CollectionItem, Entity, Relation

CHUNK_SIZE = 500

def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    paragraphs = re.split(r'\n\s*\n', text.strip())
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) + 1 > chunk_size and current:
            chunks.append(current.strip())
            current = p
        else:
            current += "\n\n" + p if current else p
    if current:
        chunks.append(current.strip())
    return chunks or [text.strip()]

def _count_tokens(text: str) -> int:
    return len(text) // 2

def create_knowledge(db: Session, data) -> Knowledge:
    kn = Knowledge(
        title=data.title, content=data.content, summary=data.summary,
        source=data.source, source_url=data.source_url, file_type=data.file_type,
        metadata_json=data.metadata, token_count=_count_tokens(data.content)
    )
    db.add(kn)
    db.flush()
    chunks_text = _chunk_text(data.content)
    for i, ct in enumerate(chunks_text):
        chunk = Chunk(knowledge_id=kn.id, content=ct, chunk_index=i, token_count=_count_tokens(ct))
        db.add(chunk)
    kn.chunk_count = len(chunks_text)
    if data.tags:
        for tname in data.tags:
            tag = db.query(Tag).filter(Tag.name == tname).first()
            if not tag:
                tag = Tag(name=tname)
                db.add(tag)
                db.flush()
            db.add(KnowledgeTag(knowledge_id=kn.id, tag_id=tag.id))
    if data.collection_ids:
        for cid in data.collection_ids:
            existing = db.query(CollectionItem).filter(
                CollectionItem.collection_id == cid, CollectionItem.knowledge_id == kn.id
            ).first()
            if not existing:
                db.add(CollectionItem(collection_id=cid, knowledge_id=kn.id))
    db.commit()
    db.refresh(kn)
    _sync_fts(db, kn.id)
    return kn

def update_knowledge(db: Session, knowledge_id: int, data) -> Optional[Knowledge]:
    kn = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not kn:
        return None
    if data.title is not None:
        kn.title = data.title
    if data.content is not None:
        kn.content = data.content
        kn.token_count = _count_tokens(data.content)
        db.query(Chunk).filter(Chunk.knowledge_id == knowledge_id).delete()
        chunks_text = _chunk_text(data.content)
        for i, ct in enumerate(chunks_text):
            db.add(Chunk(knowledge_id=knowledge_id, content=ct, chunk_index=i, token_count=_count_tokens(ct)))
        kn.chunk_count = len(chunks_text)
    if data.summary is not None:
        kn.summary = data.summary
    if data.source is not None:
        kn.source = data.source
    if data.metadata is not None:
        kn.metadata_json = data.metadata
    if data.is_active is not None:
        kn.is_active = data.is_active
    if data.tags is not None:
        db.query(KnowledgeTag).filter(KnowledgeTag.knowledge_id == knowledge_id).delete()
        for tname in data.tags:
            tag = db.query(Tag).filter(Tag.name == tname).first()
            if not tag:
                tag = Tag(name=tname)
                db.add(tag)
                db.flush()
            db.add(KnowledgeTag(knowledge_id=knowledge_id, tag_id=tag.id))
    if data.collection_ids is not None:
        db.query(CollectionItem).filter(CollectionItem.knowledge_id == knowledge_id).delete()
        for cid in data.collection_ids:
            db.add(CollectionItem(collection_id=cid, knowledge_id=knowledge_id))
    kn.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(kn)
    _sync_fts(db, knowledge_id)
    return kn

def delete_knowledge(db: Session, knowledge_id: int) -> bool:
    kn = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not kn:
        return False
    db.delete(kn)
    db.commit()
    _remove_fts(db, knowledge_id)
    return True

def get_knowledge(db: Session, knowledge_id: int) -> Optional[Knowledge]:
    return db.query(Knowledge).filter(Knowledge.id == knowledge_id, Knowledge.is_active == True).first()

def list_knowledge(db: Session, skip: int = 0, limit: int = 20, tag: Optional[str] = None,
                   collection_id: Optional[int] = None, search: Optional[str] = None):
    q = db.query(Knowledge).filter(Knowledge.is_active == True)
    if tag:
        q = q.join(KnowledgeTag).join(Tag).filter(Tag.name == tag)
    if collection_id is not None:
        q = q.join(CollectionItem).filter(CollectionItem.collection_id == collection_id)
    if search:
        q = q.filter(
            or_(Knowledge.title.ilike(f"%{search}%"), Knowledge.content.ilike(f"%{search}%"))
        )
    total = q.count()
    items = q.order_by(Knowledge.updated_at.desc()).offset(skip).limit(limit).all()
    return items, total

def get_knowledge_tags(db: Session) -> List[dict]:
    results = db.query(Tag.id, Tag.name, Tag.color, KnowledgeTag.knowledge_id).join(
        KnowledgeTag, KnowledgeTag.tag_id == Tag.id, isouter=True
    ).all()
    from collections import Counter
    counts = Counter()
    for r in results:
        if r.knowledge_id:
            counts[r.name] += 1
    tags = []
    seen = set()
    for r in results:
        if r.name not in seen:
            tags.append({"id": r.id, "name": r.name, "color": r.color, "knowledge_count": counts.get(r.name, 0)})
            seen.add(r.name)
    return tags

def get_related_knowledge(db: Session, knowledge_id: int, limit: int = 10) -> List[Knowledge]:
    relations = db.query(Relation).filter(
        or_(Relation.source_id == knowledge_id, Relation.target_id == knowledge_id)
    ).order_by(Relation.score.desc()).limit(limit).all()
    related_ids = set()
    for r in relations:
        if r.source_id == knowledge_id and r.source_type == "knowledge":
            related_ids.add(r.target_id)
        elif r.target_id == knowledge_id and r.target_type == "knowledge":
            related_ids.add(r.source_id)
    return db.query(Knowledge).filter(Knowledge.id.in_(list(related_ids) or [0])).all()

def _sync_fts(db: Session, knowledge_id: int):
    try:
        kn = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not kn:
            return
        title = kn.title.replace("'", "''")
        content = (kn.content or "")[:1000].replace("'", "''")
        summary = (kn.summary or "").replace("'", "''")
        db.execute(text(f"DELETE FROM knowledge_fts WHERE rowid = {knowledge_id}"))
        db.execute(text(f"INSERT INTO knowledge_fts(rowid, title, content, summary) VALUES ({knowledge_id}, '{title}', '{content}', '{summary}')"))
        db.commit()
    except Exception:
        db.rollback()

def _remove_fts(db: Session, knowledge_id: int):
    try:
        db.execute(text(f"DELETE FROM knowledge_fts WHERE rowid = {knowledge_id}"))
        db.commit()
    except Exception:
        db.rollback()
