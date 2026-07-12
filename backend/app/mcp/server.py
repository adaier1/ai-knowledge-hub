from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.mcp.tools import MCP_TOOL_DEFS, execute_mcp_tool
from app.core.deps import verify_api_key, check_permission
from app.models.models import MCPKey
import json, asyncio, datetime

router = APIRouter(prefix="/mcp", tags=["MCP Server"])

def _resolve_role(request: Request, db: Session, key: str = None):
    api_key = key or request.headers.get("Authorization", "").replace("Bearer ", "")
    if api_key:
        from app.core.security import hash_api_key
        key_hash = hash_api_key(api_key)
        key_record = db.query(MCPKey).filter(MCPKey.key_hash == key_hash, MCPKey.is_active == True).first()
        if key_record:
            role = key_record.role
            key_record.last_used_at = datetime.datetime.utcnow()
            db.commit()
            return role
    return "anonymous"

@router.get("")
def mcp_info(request: Request, db: Session = Depends(get_db), key: str = Query(None)):
    return {
        "name": "ai-knowledge-hub", "version": "1.0.0",
        "description": "MCP Server for AI Knowledge Hub",
        "tools": MCP_TOOL_DEFS,
        "key": key or None
    }

@router.get("/tools")
def mcp_tools(request: Request, db: Session = Depends(get_db), key: str = Query(None)):
    return {"tools": MCP_TOOL_DEFS}

@router.post("/tools/{tool_name}")
async def mcp_call_tool(tool_name: str, request: Request, db: Session = Depends(get_db), key: str = Query(None)):
    body = await request.json()
    if isinstance(body, dict):
        # Direct format: {"arguments": {...}}
        arguments = body.get("arguments")
        # JSON-RPC format: {"params": {"arguments": {...}}}
        if arguments is None and "params" in body:
            arguments = body["params"].get("arguments", {})
        if arguments is None:
            arguments = body.get("params", body)
        if not isinstance(arguments, dict):
            arguments = {}
    else:
        arguments = {}
    role = _resolve_role(request, db, key)
    if not check_permission(tool_name, role):
        raise HTTPException(status_code=403, detail="No permission")
    try:
        result = execute_mcp_tool(db, tool_name, arguments)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return {"tool": tool_name, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sse")
async def mcp_sse(request: Request, db: Session = Depends(get_db), key: str = Query(None)):
    async def event_stream():
        yield f"event: connected\ndata: {json.dumps({'message': 'MCP Server connected', 'tools': len(MCP_TOOL_DEFS)})}\n\n"
        while True:
            try:
                if await request.is_disconnected():
                    break
                await asyncio.sleep(30)
                yield f"event: heartbeat\ndata: {json.dumps({'time': str(datetime.datetime.utcnow())})}\n\n"
            except Exception:
                break
    return StreamingResponse(event_stream(), media_type="text/event-stream")