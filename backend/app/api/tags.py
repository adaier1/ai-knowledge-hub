from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Tag, KnowledgeTag
from app.schemas.schemas import TagCreate, TagResponse

router = APIRouter(prefix="/api/tags", tags=["Tags"])

@router.get("")
def api_list_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).all()
    result = []
    for tag in tags:
        count = db.query(KnowledgeTag).filter(KnowledgeTag.tag_id == tag.id).count()
        result.append({"id": tag.id, "name": tag.name, "color": tag.color, "knowledge_count": count})
    return {"items": result}

@router.post("")
def api_create_tag(data: TagCreate, db: Session = Depends(get_db)):
    existing = db.query(Tag).filter(Tag.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")
    tag = Tag(name=data.name, color=data.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return {"id": tag.id, "name": tag.name, "color": tag.color, "knowledge_count": 0}

@router.delete("/{tag_id}")
def api_delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404)
    db.delete(tag)
    db.commit()
    return {"message": "Deleted"}
