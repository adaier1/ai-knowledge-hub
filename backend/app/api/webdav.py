from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Setting
from app.services.webdav_service import (
    test_connection, backup_to_webdav, list_backups,
    import_from_webdav, import_backup_data
)
import json, os, threading, datetime, time

router = APIRouter(prefix=\"/api/webdav\", tags=[\"WebDAV\"])

class WebDAVConfig(BaseModel):
    url: str = \"\"
    username: str = \"\"
    password: str = \"\"
    backup_path: str = \"akh-backups\"
    schedule_time: str = \"\"  # HH:MM format, empty = disabled
    schedule_frequency: str = \"daily\"  # daily, weekly, monthly
    schedule_day: int = 1  # day of week (0=Mon..6=Sun) for weekly, day of month (1-31) for monthly
    schedule_enabled: bool = False

def get_config(db: Session) -> dict:
    s = db.query(Setting).filter(Setting.category == \"webdav\", Setting.key == \"config\").first()
    if s and isinstance(s.value, dict):
        return s.value
    return {\"url\": \"\", \"username\": \"\", \"password\": \"\", \"backup_path\": \"akh-backups\", \"schedule_time\": \"\", \"schedule_frequency\": \"daily\", \"schedule_day\": 1, \"schedule_enabled\": False}

def save_config(db: Session, cfg: dict):
    s = db.query(Setting).filter(Setting.category == \"webdav\", Setting.key == \"config\").first()
    if s:
        s.value = cfg
    else:
        s = Setting(category=\"webdav\", key=\"config\", value=cfg)
        db.add(s)
    db.commit()

@router.get(\"/config\")
def api_get_webdav_config(db: Session = Depends(get_db)):
    cfg = get_config(db)
    # Mask password
    pwd = cfg.get(\"password\", \"\")
    return {**cfg, \"password\": \"******\" if pwd else \"\"}

@router.put(\"/config\")
def api_save_webdav_config(cfg: WebDAVConfig, db: Session = Depends(get_db)):
    data = cfg.model_dump()
    # Fix: if password is the masked placeholder, keep the existing DB password
    if data[\"password\"] == \"******\" or not data[\"password\"]:
        existing = get_config(db)
        data[\"password\"] = existing.get(\"password\", \"\")
    save_config(db, data)
    # Reschedule
    _schedule_backup(db)
    return {\"success\": True, \"message\": \"配置已保存\"}

@router.post(\"/test\")
def api_test_webdav(cfg: WebDAVConfig):
    result = test_connection(cfg.url, cfg.username, cfg.password)
    return result

@router.post(\"/backup\")
def api_trigger_backup(db: Session = Depends(get_db)):
    cfg = get_config(db)
    if not cfg.get(\"url\"):
        raise HTTPException(status_code=400, detail=\"请先配置 WebDAV\")
    result = backup_to_webdav(db, cfg[\"url\"], cfg.get(\"username\", \"\"),
                               cfg.get(\"password\", \"\"), cfg.get(\"backup_path\", \"akh-backups\"))
    return result

@router.get(\"/backups\")
def api_list_backups(db: Session = Depends(get_db)):
    cfg = get_config(db)
    if not cfg.get(\"url\"):
        return {\"files\": []}
    files = list_backups(cfg[\"url\"], cfg.get(\"username\", \"\"),
                          cfg.get(\"password\", \"\"), cfg.get(\"backup_path\", \"akh-backups\"))
    return {\"files\": files}

@router.post(\"/import\")
def api_import_from_webdav(data: dict, db: Session = Depends(get_db)):
    \"\"\"Import from WebDAV by file href.\"\"\"
    cfg = get_config(db)
    if not cfg.get(\"url\"):
        raise HTTPException(status_code=400, detail=\"请先配置 WebDAV\")
    file_href = data.get(\"href\", \"\")
    if not file_href:
        raise HTTPException(status_code=400, detail=\"请指定备份文件\")
    result = import_from_webdav(db, cfg[\"url\"], cfg.get(\"username\", \"\"),
                                 cfg.get(\"password\", \"\"), file_href)
    return result

@router.post(\"/import/local\")
async def api_import_local(file: UploadFile = File(...), db: Session = Depends(get_db)):
    \"\"\"Import from local file upload.\"\"\"
    try:
        content = await file.read()
        data = json.loads(content.decode(\"utf-8\"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f\"文件解析失败: {str(e)[:100]}\")
    result = import_backup_data(db, data)
    return {\"success\": True, \"message\": f\"导入完成：新增{result['imported']}条，跳过{result['skipped']}条\", **result}


@router.post(\"/browse\")
def api_browse_webdav(data: dict, db: Session = Depends(get_db)):
    \"\"\"List WebDAV directories for browsing.\"\"\"
    cfg = get_config(db)
    path = data.get(\"path\", \"\")
    url = data.get(\"url\") or cfg.get(\"url\", \"\")
    username = data.get(\"username\") or cfg.get(\"username\", \"\")
    password = data.get(\"password\") or cfg.get(\"password\", \"\")
    if not url:
        raise HTTPException(status_code=400, detail=\"请先配置 WebDAV\")
    from app.services.webdav_service import list_directories
    dirs = list_directories(url, username, password, path)
    return {\"directories\": dirs, \"current_path\": path}
# ===== Scheduled backup =====
_scheduler_thread = None
_scheduler_stop = False

def _backup_job(db_session_factory):
    \"\"\"Run backup with a new DB session.\"\"\"
    try:
        db = db_session_factory()
        cfg = get_config(db)
        if cfg.get(\"url\") and cfg.get(\"schedule_time\"):
            backup_to_webdav(db, cfg[\"url\"], cfg.get(\"username\", \"\"),
                              cfg.get(\"password\", \"\"), cfg.get(\"backup_path\", \"akh-backups\"))
        db.close()
    except Exception:
        pass

def _should_backup_now(cfg: dict, last_key: str) -> tuple:
    \"\"\"Check if backup should run now. Returns (should_run, new_key).\"\"\"
    if not cfg.get(\"schedule_enabled\", False):
        return False, last_key
    sched = cfg.get(\"schedule_time\", \"\")
    if not sched or \":\" not in sched:
        return False, last_key
    now = datetime.datetime.now()
    time_str = now.strftime(\"%H:%M\")
    if time_str != sched:
        return False, last_key
    freq = cfg.get(\"schedule_frequency\", \"daily\")
    if freq == \"daily\":
        key = now.strftime(\"%Y-%m-%d\")
    elif freq == \"weekly\":
        key = now.strftime(\"%Y-%W\")  # Week number
        target_day = int(cfg.get(\"schedule_day\", 1)) % 7
        if now.weekday() != target_day:
            return False, last_key
    elif freq == \"monthly\":
        key = now.strftime(\"%Y-%m\")
        target_day = min(int(cfg.get(\"schedule_day\", 1)), 28)
        if now.day != target_day:
            return False, last_key
    else:
        key = now.strftime(\"%Y-%m-%d\")
    if key == last_key:
        return False, last_key
    return True, key

def _scheduler_loop(factory):
    global _scheduler_stop
    _scheduler_stop = False
    last_key = \"\"
    while not _scheduler_stop:
        try:
            db = factory()
            cfg = get_config(db)
            db.close()
            should_run, new_key = _should_backup_now(cfg, last_key)
            if should_run:
                _backup_job(factory)
                last_key = new_key
        except Exception:
            pass
        for _ in range(60):
            if _scheduler_stop:
                return
            time.sleep(1)

def start_scheduler(factory):
    global _scheduler_thread, _scheduler_stop
    _scheduler_stop = True
    if _scheduler_thread and _scheduler_thread.is_alive():
        _scheduler_thread.join(timeout=3)
    _scheduler_stop = False
    _scheduler_thread = threading.Thread(target=_scheduler_loop, args=(factory,), daemon=True)
    _scheduler_thread.start()

def _schedule_backup(db):
    \"\"\"Reschedule based on current config.\"\"\"
    from app.database import SessionLocal
    start_scheduler(SessionLocal)
