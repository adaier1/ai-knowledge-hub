from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import Collection, CollectionItem, Knowledge

def create_collection(db: Session, data) -> Collection:
    existing = db.query(Collection).filter(Collection.name == data.name).first()
    if existing:
        raise ValueError("Collection name already exists")
    coll = Collection(name=data.name, description=data.description, icon=data.icon, color=data.color, sort_order=data.sort_order)
    db.add(coll)
    db.commit()
    db.refresh(coll)
    return coll

def update_collection(db: Session, collection_id: int, data) -> Optional[Collection]:
    coll = db.query(Collection).filter(Collection.id == collection_id).first()
    if not coll:
        return None
    if data.name is not None:
        coll.name = data.name
    if data.description is not None:
        coll.description = data.description
    if data.icon is not None:
        coll.icon = data.icon
    if data.color is not None:
        coll.color = data.color
    if data.sort_order is not None:
        coll.sort_order = data.sort_order
    db.commit()
    db.refresh(coll)
    return coll

def delete_collection(db: Session, collection_id: int) -> bool:
    coll = db.query(Collection).filter(Collection.id == collection_id).first()
    if not coll:
        return False
    db.delete(coll)
    db.commit()
    return True

def list_collections(db: Session):
    collections = db.query(Collection).order_by(Collection.sort_order).all()
    result = []
    for c in collections:
        count = db.query(CollectionItem).filter(CollectionItem.collection_id == c.id).count()
        result.append({
            "id": c.id, "name": c.name, "description": c.description,
            "icon": c.icon, "color": c.color, "sort_order": c.sort_order,
            "knowledge_count": count
        })
    return result

def add_to_collection(db: Session, collection_id: int, knowledge_id: int):
    existing = db.query(CollectionItem).filter(
        CollectionItem.collection_id == collection_id,
        CollectionItem.knowledge_id == knowledge_id
    ).first()
    if not existing:
        db.add(CollectionItem(collection_id=collection_id, knowledge_id=knowledge_id))
        db.commit()

def remove_from_collection(db: Session, collection_id: int, knowledge_id: int):
    db.query(CollectionItem).filter(
        CollectionItem.collection_id == collection_id,
        CollectionItem.knowledge_id == knowledge_id
    ).delete()
    db.commit()
