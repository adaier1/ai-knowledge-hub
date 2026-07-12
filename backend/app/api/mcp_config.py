from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.core.security import generate_api_key, hash_api_key
from app.models.models import MCPKey, Setting
import secrets

router = APIRouter(prefix="/api/mcp", tags=["MCP"])

def _get_base_url(request: Request):
    host = request.headers.get("X-Forwarded-Host", request.headers.get("Host", ""))
    proto = request.headers.get("X-Forwarded-Proto", "http")
    return f"{proto}://{host}"

@router.get("/config")
def api_mcp_config(request: Request, db: Session = Depends(get_db)):
    display_key = ""
    setting = db.query(Setting).filter(Setting.category == "mcp", Setting.key == "display_key").first()
    if setting and setting.value:
        display_key = str(setting.value)
    
    base_url = _get_base_url(request)
    mcp_url = base_url + "/mcp?key=" + display_key if display_key else ""
    
    return {
        "name": settings.MCP_SERVER_NAME,
        "description": settings.MCP_SERVER_DESCRIPTION,
        "version": settings.MCP_SERVER_VERSION,
        "auth_type": "api_key",
        "mcp_key": display_key,
        "mcp_url": mcp_url,
        "endpoints": {
            "http": base_url + "/mcp",
            "sse": base_url + "/mcp/sse"
        }
    }

@router.post("/reset-key")
def api_reset_mcp_key(request: Request, db: Session = Depends(get_db)):
    new_raw_key = secrets.token_hex(16)
    new_key_hash = hash_api_key(new_raw_key)
    
    key_record = db.query(MCPKey).filter(MCPKey.name == "mcp-link-key").first()
    if key_record:
        key_record.key_hash = new_key_hash
    else:
        key_record = MCPKey(name="mcp-link-key", key_hash=new_key_hash, role="admin", is_active=1)
        db.add(key_record)
    
    setting = db.query(Setting).filter(Setting.category == "mcp", Setting.key == "display_key").first()
    if setting:
        setting.value = new_raw_key
    else:
        setting = Setting(category="mcp", key="display_key", value=new_raw_key)
        db.add(setting)
    
    db.commit()
    
    base_url = _get_base_url(request)
    mcp_url = base_url + "/mcp?key=" + new_raw_key
    
    return {
        "success": True,
        "mcp_key": new_raw_key,
        "mcp_url": mcp_url
    }

@router.get("/keys")
def api_list_keys(db: Session = Depends(get_db)):
    keys = db.query(MCPKey).all()
    return {"items": [{"id": k.id, "name": k.name, "role": k.role, "is_active": k.is_active, "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None, "created_at": k.created_at.isoformat() if k.created_at else None} for k in keys]}

@router.post("/keys")
def api_create_key(name: str, role: str = "agent", db: Session = Depends(get_db)):
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    key_record = MCPKey(name=name, key_hash=key_hash, role=role)
    db.add(key_record)
    db.commit()
    return {"name": name, "api_key": raw_key, "role": role}

@router.delete("/keys/{key_id}")
def api_delete_key(key_id: int, db: Session = Depends(get_db)):
    key = db.query(MCPKey).filter(MCPKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404)
    db.delete(key)
    db.commit()
    return {"message": "Deleted"}