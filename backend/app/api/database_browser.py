from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from app.database import engine, get_db
from app.schemas.schemas import SQLQueryRequest, SQLQueryResponse
import os, glob, time

router = APIRouter(prefix="/api/database", tags=["Database"])

@router.get("/tables")
def api_list_tables():
    inspector = inspect(engine)
    tables = []
    for name in inspector.get_table_names():
        if name.endswith("_fts") or name.startswith("sqlite_"):
            continue
        columns = [{"name": c["name"], "type": str(c["type"])} for c in inspector.get_columns(name)]
        indexes = [ix["name"] for ix in inspector.get_indexes(name)]
        with engine.connect() as conn:
            row_count = conn.execute(text(f"SELECT COUNT(*) FROM \"{name}\"")).scalar() or 0
        tables.append({"name": name, "columns": columns, "row_count": row_count, "indexes": indexes})
    return {"items": tables}

@router.get("/tables/{table_name}")
def api_get_table(table_name: str, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    try:
        cols = [c["name"] for c in inspect(engine).get_columns(table_name)]
        result = db.execute(text(f"SELECT * FROM \"{table_name}\" LIMIT {limit} OFFSET {skip}")).fetchall()
        total = db.execute(text(f"SELECT COUNT(*) FROM \"{table_name}\"")).scalar() or 0
        rows = [dict(zip(cols, r)) for r in result]
        return {"columns": cols, "rows": rows, "total": total}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/query", response_model=SQLQueryResponse)
def api_execute_sql(req: SQLQueryRequest):
    start = time.time()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(req.sql))
            if result.returns_rows:
                columns = list(result.keys())
                rows = [list(r) for r in result.fetchall()]
                return {"columns": columns, "rows": rows, "row_count": len(rows), "elapsed_ms": round((time.time() - start) * 1000, 2)}
            conn.commit()
            return {"columns": [], "rows": [], "row_count": result.rowcount, "elapsed_ms": round((time.time() - start) * 1000, 2)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/files")
def api_list_db_files():
    data_dir = "./data"
    files = []
    for fpath in glob.glob(os.path.join(data_dir, "*.db")):
        name = os.path.basename(fpath)
        size_bytes = os.path.getsize(fpath)
        modified = os.path.getmtime(fpath)
        active = (os.path.abspath(fpath) == os.path.abspath("./data/knowledge.db"))
        files.append({
            "name": name,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "size_bytes": size_bytes,
            "modified": modified,
            "active": active
        })
    files.sort(key=lambda f: f["modified"], reverse=True)
    return {"files": files}

@router.get("/export")
def api_export_db(db_file: str):
    safe_path = os.path.normpath(os.path.join("./data", db_file))
    if not safe_path.startswith(os.path.normpath("./data")) or not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(safe_path, filename=db_file, media_type="application/octet-stream")

@router.post("/import")
async def api_import_db(file: UploadFile = File(...)):
    data_dir = "./data"
    dst = os.path.join(data_dir, file.filename)
    if os.path.exists(dst):
        base, ext = os.path.splitext(file.filename)
        dst = os.path.join(data_dir, f"{base}_{int(time.time())}{ext}")
    with open(dst, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"success": True, "message": "Import success: " + os.path.basename(dst), "filename": os.path.basename(dst)}

@router.get("/fts")
def api_get_fts_status():
    try:
        with engine.connect() as conn:
            tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts%'")).fetchall()
            return {"fts_tables": [t[0] for t in tables]}
    except Exception as e:
        return {"fts_tables": [], "error": str(e)}
