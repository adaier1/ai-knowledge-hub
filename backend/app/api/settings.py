from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Setting
from app.services.embedding_service import embedding_service
import json, urllib.request, urllib.error, time

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/{category}")
def api_get_settings(category: str, db: Session = Depends(get_db)):
    settings = db.query(Setting).filter(Setting.category == category).all()
    return {s.key: s.value for s in settings}

@router.put("/{category}/{key}")
def api_update_setting(category: str, key: str, value: dict, db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.category == category, Setting.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(category=category, key=key, value=value)
        db.add(setting)
    db.commit()
    return {"message": "Saved"}

class TestEmbeddingRequest(BaseModel):
    provider: str = "openai"
    model: str = ""
    api_key: str = ""
    api_url: str = ""

PROVIDER_DEFAULTS = {
    "openai": {"api_url": "https://api.openai.com/v1", "model": "text-embedding-3-small"},
    "siliconflow": {"api_url": "https://api.siliconflow.cn/v1", "model": "BAAI/bge-large-zh-v1.5"},
    "ollama": {"api_url": "http://localhost:11434/v1", "model": "nomic-embed-text"},
    "doubao": {"api_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-embedding-vision-251215"},
}

def _parse_embedding_from_response(result):
    if "data" in result and isinstance(result["data"], list) and len(result["data"]) > 0:
        if "embedding" in result["data"][0]:
            return result["data"][0]["embedding"]
    if "data" in result and isinstance(result["data"], dict):
        if "embedding" in result["data"]:
            return result["data"]["embedding"]
    if "embedding" in result:
        return result["embedding"]
    return None

@router.post("/embedding/test")
def test_embedding_config(req: TestEmbeddingRequest):
    import traceback
    provider = req.provider or "openai"
    model = req.model or ""
    api_key = req.api_key or ""
    api_url = req.api_url or ""
    defaults = PROVIDER_DEFAULTS.get(provider, {})
    if not api_url:
        api_url = defaults.get("api_url", "")
    if not model:
        model = defaults.get("model", "text-embedding-3-small")
    if not api_url:
        return {"success": False, "message": "请填写 API 地址", "detail": {"provider": provider}}
    if not api_key:
        return {"success": False, "message": "请填写 API 密钥", "detail": {"provider": provider, "api_url": api_url}}
    try:
        import socket
        base_host = api_url.replace("https://", "").replace("http://", "").split("/")[0]
        socket.getaddrinfo(base_host, 443 if api_url.startswith("https") else 80)
    except Exception as e:
        return {"success": False, "message": "DNS 解析失败", "detail": {"api_url": api_url, "error": str(e)}}
    is_multimodal = provider == "doubao" or "vision" in model.lower() or "multimodal" in model.lower()
    if is_multimodal:
        return _test_multimodal(api_url, api_key, model)
    else:
        return _test_standard(api_url, api_key, model, provider)

def _test_standard(api_url, api_key, model, provider):
    import openai, traceback
    try:
        client = openai.OpenAI(api_key=api_key, base_url=api_url)
        resp = client.embeddings.create(model=model, input="test")
        vec = resp.data[0].embedding
        dim = len(vec)
        return {"success": True, "message": "连接成功！向量维度: " + str(dim),
                "detail": {"api_url": api_url, "provider": provider, "model": model, "dimension": dim, "key_prefix": api_key[:10] + "..."}}
    except Exception as e:
        return {"success": False, "message": "连接失败: " + str(e),
                "detail": {"api_url": api_url, "provider": provider, "model": model, "error": str(e), "traceback": traceback.format_exc()}}

def _test_multimodal(api_url, api_key, model):
    import traceback
    multimodal_url = api_url.rstrip("/") + "/embeddings/multimodal"
    request_body = json.dumps({"model": model, "input": [{"type": "text", "text": "测试向量连接"}]}).encode("utf-8")
    try:
        req = urllib.request.Request(multimodal_url, data=request_body,
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        vec = _parse_embedding_from_response(result)
        if vec and len(vec) > 0:
            return {"success": True, "message": "连接成功！向量维度: " + str(len(vec)),
                    "detail": {"api_url": multimodal_url, "model": model, "dimension": len(vec), "key_prefix": api_key[:10] + "..."}}
        return {"success": True, "message": "连接成功", "detail": {"api_url": multimodal_url}}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        status = e.code
        friendly_msg = "HTTP " + str(status) + ": " + (error_body[:300] if error_body else str(e))
        if status >= 500:
            friendly_msg = "服务端暂时不可用，请稍后重试"
        elif status == 429:
            friendly_msg = "请求频率超限，请稍后重试"
        elif status == 401:
            friendly_msg = "认证失败，请检查 API 密钥是否正确"
        return {"success": False, "message": friendly_msg,
                "detail": {"api_url": multimodal_url, "model": model, "error_detail": error_body[:500] if error_body else str(e),
                          "key_prefix": api_key[:10] + "..." if api_key else "未设置"}}
    except Exception as e:
        return {"success": False, "message": "连接失败: " + str(e),
                "detail": {"api_url": multimodal_url, "model": model, "error": str(e), "traceback": traceback.format_exc()}}

# ===== 向量重建 API =====

@router.post("/embedding/rebuild")
def api_rebuild_embeddings(db: Session = Depends(get_db)):
    """重建所有向量：保留原文档，创建新版向量"""
    # 确定新版本号
    versions = embedding_service.get_versions(db)
    exist = [v["name"] for v in versions["versions"]]
    # 查找下一个可用版本号
    v_num = 1
    while f"v{v_num}" in exist:
        v_num += 1
    new_version = f"v{v_num}"
    # 重建所有向量
    result = embedding_service.rebuild_all_embeddings(db, new_version)
    return {"message": f"重建完成，共处理 {result['completed']}/{result['total']} 条知识", "version": new_version}

@router.get("/embedding/rebuild/status")
def api_rebuild_status(db: Session = Depends(get_db)):
    """查询向量版本状态"""
    versions = embedding_service.get_versions(db)
    return versions

@router.post("/embedding/switch-version")
def api_switch_version(version: str, db: Session = Depends(get_db)):
    """切换到指定向量版本"""
    if version == embedding_service.switch_version(db, version):
        return {"message": "已切换到版本 " + version, "version": version}
    return {"message": "切换失败"}

@router.delete("/embedding/old-version")
def api_delete_old_version(version: str, db: Session = Depends(get_db)):
    """删除指定旧版本的向量（保护 v1）"""
    if version == "v1":
        raise HTTPException(status_code=400, detail="v1 是基础版本，不能删除")
    ok = embedding_service.delete_version(db, version)
    if ok:
        return {"message": "版本 " + version + " 已删除"}
    raise HTTPException(status_code=404, detail="版本不存在")
