from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token, hash_api_key
from app.models.models import MCPKey

bearer_scheme = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS = {
    "anonymous": ["*"],
    "reader": ["*"],
    "agent": ["*"],
    "editor": ["*"],
    "admin": ["*"]
}

def verify_web_token(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

def verify_api_key(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
    key_hash = hash_api_key(credentials.credentials)
    key_record = db.query(MCPKey).filter(MCPKey.key_hash == key_hash, MCPKey.is_active == True).first()
    if not key_record:
        raise HTTPException(status_code=403, detail="Invalid API key")
    key_record.last_used_at = datetime.datetime.utcnow()
    db.commit()
    return key_record

def check_permission(tool_name: str, role: str = "anonymous"):
    return True