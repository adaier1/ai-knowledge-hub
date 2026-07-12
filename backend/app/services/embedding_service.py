from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Embedding, Chunk, Knowledge, Setting
from app.config import settings
import json, hashlib, urllib.request, urllib.error

def _parse_multimodal_response(result):
    if "data" in result and isinstance(result["data"], list) and len(result["data"]) > 0:
        if "embedding" in result["data"][0]:
            return result["data"][0]["embedding"]
    if "data" in result and isinstance(result["data"], dict):
        if "embedding" in result["data"]:
            return result["data"]["embedding"]
    if "embedding" in result:
        return result["embedding"]
    return None

def _extract_embedding_config(db_settings):
    cfg = db_settings
    if isinstance(cfg, dict):
        if "value" in cfg and isinstance(cfg["value"], dict) and "provider" in cfg["value"]:
            cfg = cfg["value"]
        if "settings" in cfg and isinstance(cfg["settings"], dict):
            inner = cfg["settings"]
            if "value" in inner and isinstance(inner["value"], dict) and "provider" in inner["value"]:
                cfg = inner["value"]
            elif "provider" in inner:
                cfg = inner
    return cfg

class EmbeddingService:
    def __init__(self):
        self.client = None
        self.provider = settings.EMBEDDING_PROVIDER
        self._db_settings = {}
        self._active_version = "v1"

    def _load_db_settings(self, db=None):
        if db is None:
            return
        try:
            rows = db.query(Setting).filter(Setting.category == "embedding").all()
            for row in rows:
                val = row.value
                if isinstance(val, dict):
                    self._db_settings.update(val)
                elif isinstance(val, str):
                    self._db_settings[row.key] = val
        except Exception:
            pass

    def _get_config(self, db=None):
        self._load_db_settings(db)
        cfg = _extract_embedding_config(self._db_settings)
        provider = cfg.get("provider", settings.EMBEDDING_PROVIDER)
        api_key = cfg.get("api_key", "") or settings.EMBEDDING_API_KEY
        api_url = cfg.get("api_url", "") or settings.EMBEDDING_API_URL
        model = cfg.get("model", settings.EMBEDDING_MODEL)
        return provider, api_key, api_url, model

    def _is_multimodal(self, provider, model):
        return provider == "doubao" or "vision" in model.lower() or "multimodal" in model.lower()

    def _embed_multimodal(self, texts, api_key, api_url, model):
        multimodal_url = api_url.rstrip("/") + "/embeddings/multimodal"
        results = []
        for text in texts:
            try:
                req = urllib.request.Request(
                    multimodal_url,
                    data=json.dumps({"model": model, "input": [{"type": "text", "text": text[:8000]}]}).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                vec = _parse_multimodal_response(result)
                if vec and len(vec) > 0:
                    results.append(vec)
                else:
                    results.append([0.0] * settings.EMBEDDING_DIMENSION)
            except Exception:
                results.append([0.0] * settings.EMBEDDING_DIMENSION)
        return results

    def _init_client(self, db=None):
        provider, api_key, api_url, model = self._get_config(db)
        if self._is_multimodal(provider, model):
            self.client = None
            self._multimodal_mode = True
            self._model = model
            self._provider = provider
            self._api_key = api_key
            self._api_url = api_url
            return
        if self.client is not None and db is None:
            return
        self._multimodal_mode = False
        import openai
        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if api_url:
            kwargs["base_url"] = api_url
        self.client = openai.OpenAI(**kwargs) if kwargs else openai.OpenAI()
        self._model = model
        self._provider = provider

    def embed_text(self, text, db=None):
        self._init_client(db)
        try:
            if getattr(self, "_multimodal_mode", False):
                return self._embed_multimodal([text], self._api_key, self._api_url, self._model)[0]
            resp = self.client.embeddings.create(model=self._model, input=text[:8000])
            return resp.data[0].embedding
        except Exception:
            return [0.0] * settings.EMBEDDING_DIMENSION

    def embed_batch(self, texts, db=None):
        self._init_client(db)
        try:
            if getattr(self, "_multimodal_mode", False):
                return self._embed_multimodal(texts, self._api_key, self._api_url, self._model)
            resp = self.client.embeddings.create(model=self._model, input=[t[:8000] for t in texts])
            return [d.embedding for d in resp.data]
        except Exception:
            return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]

    def _vector_to_blob(self, vec):
        return json.dumps(vec)

    def _blob_to_vector(self, blob):
        return json.loads(blob)

    def cosine_similarity(self, a, b):
        import numpy as np
        a_np, b_np = np.array(a), np.array(b)
        return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np) + 1e-10))

    def build_embeddings_for_knowledge(self, db, knowledge_id, version="v1"):
        self._init_client(db)
        chunks = db.query(Chunk).filter(Chunk.knowledge_id == knowledge_id).all()
        if not chunks:
            return
        texts = [c.content[:8000] for c in chunks]
        vectors = self.embed_batch(texts, db)
        actual_dim = len(vectors[0]) if vectors and len(vectors) > 0 and len(vectors[0]) > 0 else settings.EMBEDDING_DIMENSION
        # 删除该文档的同版本旧向量
        db.query(Embedding).filter(
            Embedding.knowledge_id == knowledge_id,
            Embedding.vector_version == version
        ).delete()
        for chunk, vec in zip(chunks, vectors):
            emb = Embedding(chunk_id=chunk.id, knowledge_id=knowledge_id,
                          provider=self._provider, model=self._model,
                          dimension=actual_dim, vector_blob=self._vector_to_blob(vec),
                          vector_version=version, is_active=1)
            db.add(emb)
        db.commit()

    def rebuild_all_embeddings(self, db, version="v2"):
        """重建所有知识的向量（保留原始文档和旧向量）"""
        from app.models.models import Knowledge
        all_knowledge = db.query(Knowledge).filter(Knowledge.is_active == True).all()
        total = len(all_knowledge)
        completed = 0
        for idx, kn in enumerate(all_knowledge):
            try:
                self.build_embeddings_for_knowledge(db, kn.id, version)
                completed += 1
            except Exception as e:
                print(f"Rebuild error for {kn.id}: {e}")
        return {"total": total, "completed": completed, "version": version}

    def switch_version(self, db, version):
        """切换活跃向量版本：激活目标版本，停用其他版本"""
        db.query(Embedding).update({"is_active": 0})
        db.query(Embedding).filter(Embedding.vector_version == version).update({"is_active": 1})
        db.commit()
        self._active_version = version
        return version

    def get_versions(self, db):
        """查询所有向量版本及其统计"""
        from sqlalchemy import func
        versions = db.query(
            Embedding.vector_version,
            func.count(Embedding.id).label("count"),
            func.max(Embedding.created_at).label("latest")
        ).group_by(Embedding.vector_version).all()
        active = db.query(Embedding.vector_version).filter(Embedding.is_active == 1).first()
        return {
            "versions": [{"name": v[0], "count": v[1], "latest": str(v[2]) if v[2] else None} for v in versions],
            "active": active[0] if active else None
        }

    def delete_version(self, db, version):
        """删除指定版本的向量"""
        if version == "v1":
            return False  # 保护基础版本
        count = db.query(Embedding).filter(Embedding.vector_version == version).delete()
        db.commit()
        return count > 0

    def semantic_search(self, db, query, limit=10):
        query_vec = self.embed_text(query, db)
        embeddings = db.query(Embedding).filter(
            Embedding.is_active == 1
        ).limit(500).all()
        scored = []
        for emb in embeddings:
            try:
                vec = self._blob_to_vector(emb.vector_blob)
                sim = self.cosine_similarity(query_vec, vec)
                scored.append((sim, emb.knowledge_id, emb.chunk_id))
            except Exception:
                continue
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:limit]
        results = []
        for sim, kid, cid in top:
            kn = db.query(Knowledge).filter(Knowledge.id == kid).first()
            if kn:
                results.append({"knowledge_id": kid, "chunk_id": cid, "title": kn.title,
                              "content": (kn.content or "")[:300], "score": sim, "source": "semantic"})
        return results

embedding_service = EmbeddingService()
