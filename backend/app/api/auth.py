from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import create_access_token, verify_password, hash_password
from app.schemas.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])

DEFAULT_USER = "admin"
DEFAULT_PASS = "admin123"

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    if data.username != DEFAULT_USER:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": data.username, "role": "admin"})
    return TokenResponse(access_token=token)
