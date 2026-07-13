from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import get_dashboard_stats, get_trends, get_top_queries, get_top_knowledge
import os, glob

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


@router.get("/logs")
def api_get_logs(lines: int = Query(200, ge=10, le=1000)):
    log_files = []
    candidates = ["./app.log", "./logs/app.log", "/tmp/akh_backend.log", "../app.log"]
    for p in candidates:
        ap = os.path.abspath(p)
        if os.path.isfile(ap):
            log_files.append(ap)
    if not log_files:
        for pattern in ["./**/*.log", "./logs/**/*.log"]:
            for f in glob.glob(pattern, recursive=True):
                if os.path.isfile(f):
                    log_files.append(os.path.abspath(f))
    log_files = list(set(log_files))[:3]
    all_lines = []
    for lf in log_files:
        try:
            with open(lf, "r", errors="replace") as fh:
                all_lines.extend(fh.readlines())
        except Exception:
            pass
    all_lines = all_lines[-lines:]
    entries = []
    import re as _re
    for line in all_lines:
        line = line.rstrip("\n\r ")
        if not line:
            continue
        entry = {"time": "", "level": "INFO", "message": line, "raw": line}
        m = _re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,\.]?\d*)\s+", line)
        if m:
            entry["time"] = m.group(1)
            rest = line[m.end():]
        else:
            rest = line
        rest = rest.strip()
        for lvl in ["ERROR", "WARNING", "WARN", "INFO", "DEBUG", "CRITICAL"]:
            if rest.startswith(lvl) or rest.startswith(lvl.lower()):
                entry["level"] = lvl
                rest = rest[len(lvl):].strip(" :")
                break
        entry["message"] = rest
        entries.append(entry)
    entries.reverse()
    return {"logs": entries}
