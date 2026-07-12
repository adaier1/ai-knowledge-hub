import os, sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    from app.api.webdav import start_scheduler
    from app.database import SessionLocal
    start_scheduler(SessionLocal)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.BACKUP_DIR, exist_ok=True)
    init_db()

@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}

from app.api import auth, knowledge, search, graph, collections, analytics, database_browser, settings as settings_api, mcp_config, tags, webdav
from app.mcp import server as mcp_server

app.include_router(auth.router)
app.include_router(knowledge.router)
app.include_router(search.router)
app.include_router(graph.router)
app.include_router(collections.router)
app.include_router(analytics.router)
app.include_router(database_browser.router)
app.include_router(settings_api.router)
app.include_router(mcp_config.router)
app.include_router(tags.router)
app.include_router(mcp_server.router)
app.include_router(webdav.router)

# Serve frontend static files if dist exists
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
