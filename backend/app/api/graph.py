from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.graph_service import get_graph_data, find_path, get_graph_statistics
from app.services.knowledge_service import create_knowledge, get_knowledge
from app.models.models import Entity, Relation
from app.schemas.schemas import EntityCreate, RelationCreate

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])

@router.get("")
def api_get_graph(center_id: int = None, center_type: str = "knowledge", depth: int = 1, limit: int = 200, db: Session = Depends(get_db)):
    return get_graph_data(db, center_id, center_type, depth, limit)

@router.get("/statistics")
def api_graph_stats(db: Session = Depends(get_db)):
    return get_graph_statistics(db)

@router.post("/path")
def api_find_path(source_id: int, target_id: int, source_type: str = "knowledge", target_type: str = "knowledge", db: Session = Depends(get_db)):
    return find_path(db, source_id, target_id, source_type, target_type)

@router.get("/entities")
def api_list_entities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    entities = db.query(Entity).offset(skip).limit(limit).all()
    return {"items": [{"id": e.id, "name": e.name, "type": e.type, "description": e.description} for e in entities], "total": db.query(Entity).count()}

@router.post("/entities")
def api_create_entity(data: EntityCreate, db: Session = Depends(get_db)):
    ent = Entity(name=data.name, type=data.type, description=data.description, metadata_json=data.metadata)
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return {"id": ent.id, "name": ent.name, "type": ent.type, "description": ent.description}

@router.delete("/entities/{entity_id}")
def api_delete_entity(entity_id: int, db: Session = Depends(get_db)):
    ent = db.query(Entity).filter(Entity.id == entity_id).first()
    if not ent:
        raise HTTPException(status_code=404)
    db.delete(ent)
    db.commit()
    return {"message": "Deleted"}

@router.get("/relations")
def api_list_relations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    relations = db.query(Relation).offset(skip).limit(limit).all()
    return {"items": [{"id": r.id, "source_id": r.source_id, "target_id": r.target_id, "source_type": r.source_type, "target_type": r.target_type, "relation_type": r.relation_type, "score": r.score, "source": r.source} for r in relations], "total": db.query(Relation).count()}

@router.post("/relations")
def api_create_relation(data: RelationCreate, db: Session = Depends(get_db)):
    rel = Relation(source_id=data.source_id, target_id=data.target_id, source_type=data.source_type, target_type=data.target_type, relation_type=data.relation_type, score=data.score, source=data.source)
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return {"id": rel.id, "relation_type": rel.relation_type, "score": rel.score}

@router.delete("/relations/{relation_id}")
def api_delete_relation(relation_id: int, db: Session = Depends(get_db)):
    rel = db.query(Relation).filter(Relation.id == relation_id).first()
    if not rel:
        raise HTTPException(status_code=404)
    db.delete(rel)
    db.commit()
    return {"message": "Deleted"}
