from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import get_dashboard_stats, get_trends, get_top_queries, get_top_knowledge

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dashboard")
def api_dashboard(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)

@router.get("/trends")
def api_trends(days: int = 30, db: Session = Depends(get_db)):
    return get_trends(db, days)

@router.get("/top-queries")
def api_top_queries(limit: int = 10, db: Session = Depends(get_db)):
    return get_top_queries(db, limit)

@router.get("/top-knowledge")
def api_top_knowledge(limit: int = 10, db: Session = Depends(get_db)):
    return get_top_knowledge(db, limit)
