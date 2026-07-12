from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import Memory
import datetime

def create_memory(db: Session, agent_id: str, content: str, memory_type: str = "episodic",
                  summary: str = "", importance: int = 5, metadata: dict = {}) -> Memory:
    mem = Memory(agent_id=agent_id, memory_type=memory_type, content=content,
                 summary=summary, importance=importance, metadata_json=metadata)
    db.add(mem)
    db.commit()
    db.refresh(mem)
    return mem

def recall_memories(db: Session, agent_id: str, limit: int = 20, memory_type: Optional[str] = None):
    q = db.query(Memory).filter(Memory.agent_id == agent_id)
    if memory_type:
        q = q.filter(Memory.memory_type == memory_type)
    return q.order_by(desc(Memory.is_pinned), desc(Memory.importance), desc(Memory.updated_at)).limit(limit).all()

def search_memories(db: Session, agent_id: str, query: str, limit: int = 10):
    q = f"%{query}%"
    return db.query(Memory).filter(
        Memory.agent_id == agent_id,
        Memory.content.ilike(q)
    ).order_by(desc(Memory.importance)).limit(limit).all()

def update_memory(db: Session, memory_id: int, content: Optional[str] = None,
                  summary: Optional[str] = None, importance: Optional[int] = None) -> Optional[Memory]:
    mem = db.query(Memory).filter(Memory.id == memory_id).first()
    if not mem:
        return None
    if content is not None:
        mem.content = content
    if summary is not None:
        mem.summary = summary
    if importance is not None:
        mem.importance = importance
    mem.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(mem)
    return mem

def delete_memory(db: Session, memory_id: int) -> bool:
    mem = db.query(Memory).filter(Memory.id == memory_id).first()
    if not mem:
        return False
    db.delete(mem)
    db.commit()
    return True

def pin_memory(db: Session, memory_id: int, pinned: bool = True) -> Optional[Memory]:
    mem = db.query(Memory).filter(Memory.id == memory_id).first()
    if not mem:
        return None
    mem.is_pinned = pinned
    db.commit()
    db.refresh(mem)
    return mem
