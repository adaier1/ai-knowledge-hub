from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.collection_service import create_collection, update_collection, delete_collection, list_collections, add_to_collection, remove_from_collection
from app.schemas.schemas import CollectionCreate, CollectionUpdate, CollectionResponse

router = APIRouter(prefix="/api/collections", tags=["Collections"])

@router.get("")
def api_list_collections(db: Session = Depends(get_db)):
    return {"items": list_collections(db)}

@router.post("", response_model=CollectionResponse)
def api_create_collection(data: CollectionCreate, db: Session = Depends(get_db)):
    try:
        c = create_collection(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": c.id, "name": c.name, "description": c.description, "icon": c.icon, "color": c.color, "sort_order": c.sort_order, "knowledge_count": 0}

@router.put("/{collection_id}")
def api_update_collection(collection_id: int, data: CollectionUpdate, db: Session = Depends(get_db)):
    c = update_collection(db, collection_id, data)
    if not c:
        raise HTTPException(status_code=404)
    return {"id": c.id, "name": c.name, "description": c.description}

@router.delete("/{collection_id}")
def api_delete_collection(collection_id: int, db: Session = Depends(get_db)):
    if not delete_collection(db, collection_id):
        raise HTTPException(status_code=404)
    return {"message": "Deleted"}

@router.post("/{collection_id}/items/{knowledge_id}")
def api_add_to_collection(collection_id: int, knowledge_id: int, db: Session = Depends(get_db)):
    add_to_collection(db, collection_id, knowledge_id)
    return {"message": "Added"}

@router.delete("/{collection_id}/items/{knowledge_id}")
def api_remove_from_collection(collection_id: int, knowledge_id: int, db: Session = Depends(get_db)):
    remove_from_collection(db, collection_id, knowledge_id)
    return {"message": "Removed"}
