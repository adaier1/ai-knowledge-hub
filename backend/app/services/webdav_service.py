import json, datetime, os, hashlib, logging, time, shutil, base64, tempfile, zipfile
from typing import Optional, List, Callable, TypeVar
from sqlalchemy.orm import Session

from webdav4.client import Client, HTTPError

from app.models.models import Knowledge, Chunk, Embedding, Tag, KnowledgeTag, Entity, Relation, Setting, SearchLog, Statistic

logger = logging.getLogger("webdav")

T = TypeVar("T")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

BACKUP_FILE_PREFIX = "knowledge_backup_"
BACKUP_FILE_SUFFIX = ".zip"


def create_webdav_client(base_url, username="", password=""):
    client = Client(base_url, auth=(username, password) if username else None, timeout=30)
    return client


def parse_webdav_error(status):
    errors = {
        400: "请求格式错误，请检查配置",
        401: "认证失败，请检查用户名和密码",
        403: "访问被拒绝，没有操作权限",
        404: "路径不存在，请检查备份路径",
        405: "服务器不支持该方法，请检查 WebDAV 服务配置",
        409: "文件冲突，目标文件已存在",
        423: "资源被锁定，请稍后重试",
        429: "请求过于频繁，请稍后重试",
        500: "服务器内部错误，请联系管理员",
        502: "网关错误，WebDAV 服务可能不可用",
        503: "服务暂时不可用，请稍后重试",
        507: "存储空间不足",
    }
    return errors.get(status, "WebDAV 错误 (HTTP {})".format(status))


def with_retry(fn, max_retries=3, *args, **kwargs):
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except HTTPError as e:
            status_code = e.status_code
            logger.debug("HTTPError: status=%s, message=%s", status_code, str(e), exc_info=True)
            last_exception = e
            if status_code == 429:
                if attempt < max_retries:
                    wait = 2 ** (attempt + 1)
                    logger.info("Rate limited (429), retrying in %ds", wait)
                    time.sleep(wait)
                    continue
            else:
                raise
        except (ConnectionError, TimeoutError, OSError) as e:
            logger.debug("Network error: %s", str(e), exc_info=True)
            last_exception = e
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                logger.info("Network error, retrying in %ds", wait)
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            logger.debug("Unexpected error: %s", str(e), exc_info=True)
            raise
    raise last_exception


def _get_db_data(db):
    data = {
        "version": "2.0",
        "exported_at": datetime.datetime.utcnow().isoformat(),
        "knowledge": [], "chunks": [], "embeddings": [],
        "tags": [], "knowledge_tags": [],
        "entities": [], "relations": [],
        "settings": [], "search_logs": [], "statistics": [],
    }
    for k in db.query(Knowledge).all():
        data["knowledge"].append({
            "id": k.id, "title": k.title, "content": k.content,
            "summary": k.summary, "source": k.source,
            "source_url": k.source_url, "file_type": k.file_type,
            "metadata_json": k.metadata_json, "token_count": k.token_count,
            "chunk_count": k.chunk_count, "is_active": k.is_active,
            "created_at": k.created_at.isoformat() if k.created_at else None,
            "updated_at": k.updated_at.isoformat() if k.updated_at else None,
        })
    for c in db.query(Chunk).all():
        data["chunks"].append({
            "id": c.id, "knowledge_id": c.knowledge_id,
            "content": c.content, "chunk_index": c.chunk_index,
            "token_count": c.token_count, "metadata_json": c.metadata_json,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    for e in db.query(Embedding).all():
        data["embeddings"].append({
            "id": e.id, "chunk_id": e.chunk_id, "knowledge_id": e.knowledge_id,
            "provider": e.provider, "model": e.model, "dimension": e.dimension,
            "vector_blob": e.vector_blob, "vector_version": e.vector_version,
            "is_active": e.is_active,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })
    for t in db.query(Tag).all():
        data["tags"].append({
            "id": t.id, "name": t.name, "color": t.color,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    for kt in db.query(KnowledgeTag).all():
        data["knowledge_tags"].append({
            "id": kt.id, "knowledge_id": kt.knowledge_id, "tag_id": kt.tag_id,
        })
    for en in db.query(Entity).all():
        data["entities"].append({
            "id": en.id, "name": en.name, "type": en.type,
            "description": en.description, "metadata_json": en.metadata_json,
            "created_at": en.created_at.isoformat() if en.created_at else None,
            "updated_at": en.updated_at.isoformat() if en.updated_at else None,
        })
    for r in db.query(Relation).all():
        data["relations"].append({
            "id": r.id, "source_id": r.source_id, "target_id": r.target_id,
            "source_type": r.source_type, "target_type": r.target_type,
            "relation_type": r.relation_type, "score": r.score,
            "source": r.source, "metadata_json": r.metadata_json,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    for s in db.query(Setting).all():
        data["settings"].append({
            "id": s.id, "category": s.category, "key": s.key,
            "value": s.value,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        })
    for sl in db.query(SearchLog).all():
        data["search_logs"].append({
            "id": sl.id, "query": sl.query, "search_type": sl.search_type,
            "results_count": sl.results_count, "top_chunk_ids": sl.top_chunk_ids,
            "final_context": sl.final_context, "latency_ms": sl.latency_ms,
            "hit": sl.hit, "score": sl.score, "source": sl.source,
            "agent_name": sl.agent_name, "llm_model": sl.llm_model,
            "created_at": sl.created_at.isoformat() if sl.created_at else None,
        })
    for st in db.query(Statistic).all():
        data["statistics"].append({
            "id": st.id, "date": st.date, "metric": st.metric,
            "value": st.value, "metadata_json": st.metadata_json,
            "created_at": st.created_at.isoformat() if st.created_at else None,
        })
    return data


def _import_db_data(db, data):
    result = {"imported": 0, "skipped": 0}
    existing_ids = set()
    for row in db.query(Knowledge.id).all():
        existing_ids.add(row[0])
    for k_data in data.get("knowledge", []):
        kid = k_data.get("id")
        if kid and kid in existing_ids:
            result["skipped"] += 1
            continue
        parsed = {}
        for key in ["title", "content", "summary", "source", "source_url",
                     "file_type", "metadata_json", "token_count", "chunk_count", "is_active"]:
            v = k_data.get(key)
            if key in ("metadata_json",) and v is None:
                v = {}
            parsed[key] = v
        for dt_key in ["created_at", "updated_at"]:
            v = k_data.get(dt_key)
            if v and isinstance(v, str):
                try:
                    parsed[dt_key] = datetime.datetime.fromisoformat(v)
                except (ValueError, TypeError):
                    parsed[dt_key] = datetime.datetime.utcnow()
            else:
                parsed[dt_key] = datetime.datetime.utcnow()
        if kid:
            parsed["id"] = kid
        db.add(Knowledge(**parsed))
        result["imported"] += 1
    db.flush()
    for c_data in data.get("chunks", []):
        cid = c_data.get("id", 0)
        if db.query(Chunk).filter(Chunk.id == cid).first():
            result["skipped"] += 1
            continue
        parsed = {
            "knowledge_id": c_data.get("knowledge_id", 0),
            "content": c_data.get("content", ""),
            "chunk_index": c_data.get("chunk_index", 0),
            "token_count": c_data.get("token_count", 0),
            "metadata_json": c_data.get("metadata_json") or {},
        }
        created = c_data.get("created_at")
        if created and isinstance(created, str):
            try:
                parsed["created_at"] = datetime.datetime.fromisoformat(created)
            except (ValueError, TypeError):
                parsed["created_at"] = datetime.datetime.utcnow()
        else:
            parsed["created_at"] = datetime.datetime.utcnow()
        if cid:
            parsed["id"] = cid
        db.add(Chunk(**parsed))
        result["imported"] += 1
    db.flush()
    for e_data in data.get("embeddings", []):
        eid = e_data.get("id", 0)
        if db.query(Embedding).filter(Embedding.id == eid).first():
            result["skipped"] += 1
            continue
        parsed = {
            "chunk_id": e_data.get("chunk_id", 0),
            "knowledge_id": e_data.get("knowledge_id", 0),
            "provider": e_data.get("provider", "openai"),
            "model": e_data.get("model", "text-embedding-3-small"),
            "dimension": e_data.get("dimension", 1536),
            "vector_blob": e_data.get("vector_blob", ""),
            "vector_version": e_data.get("vector_version", "v1"),
            "is_active": e_data.get("is_active", 1),
        }
        created = e_data.get("created_at")
        if created and isinstance(created, str):
            try:
                parsed["created_at"] = datetime.datetime.fromisoformat(created)
            except (ValueError, TypeError):
                parsed["created_at"] = datetime.datetime.utcnow()
        else:
            parsed["created_at"] = datetime.datetime.utcnow()
        if eid:
            parsed["id"] = eid
        db.add(Embedding(**parsed))
        result["imported"] += 1
    db.flush()
    for t_data in data.get("tags", []):
        tid = t_data.get("id", 0)
        if db.query(Tag).filter(Tag.id == tid).first():
            result["skipped"] += 1
            continue
        name = t_data.get("name", "")
        if db.query(Tag).filter(Tag.name == name).first():
            result["skipped"] += 1
            continue
        parsed = {"name": name, "color": t_data.get("color", "#1890ff")}
        created = t_data.get("created_at")
        if created and isinstance(created, str):
            try:
                parsed["created_at"] = datetime.datetime.fromisoformat(created)
            except (ValueError, TypeError):
                parsed["created_at"] = datetime.datetime.utcnow()
        else:
            parsed["created_at"] = datetime.datetime.utcnow()
        if tid:
            parsed["id"] = tid
        db.add(Tag(**parsed))
        result["imported"] += 1
    db.flush()
    for kt_data in data.get("knowledge_tags", []):
        if db.query(KnowledgeTag).filter(
            KnowledgeTag.knowledge_id == kt_data["knowledge_id"],
            KnowledgeTag.tag_id == kt_data["tag_id"],
        ).first():
            result["skipped"] += 1
            continue
        db.add(KnowledgeTag(knowledge_id=kt_data["knowledge_id"], tag_id=kt_data["tag_id"]))
        result["imported"] += 1
    db.flush()
    for en_data in data.get("entities", []):
        eid = en_data.get("id", 0)
        if db.query(Entity).filter(Entity.id == eid).first():
            result["skipped"] += 1
            continue
        parsed = {
            "name": en_data.get("name", ""),
            "type": en_data.get("type", "general"),
            "description": en_data.get("description", ""),
            "metadata_json": en_data.get("metadata_json") or {},
        }
        for dt_key in ["created_at", "updated_at"]:
            v = en_data.get(dt_key)
            if v and isinstance(v, str):
                try:
                    parsed[dt_key] = datetime.datetime.fromisoformat(v)
                except (ValueError, TypeError):
                    parsed[dt_key] = datetime.datetime.utcnow()
            else:
                parsed[dt_key] = datetime.datetime.utcnow()
        if eid:
            parsed["id"] = eid
        db.add(Entity(**parsed))
        result["imported"] += 1
    db.flush()
    for r_data in data.get("relations", []):
        rid = r_data.get("id", 0)
        if db.query(Relation).filter(Relation.id == rid).first():
            result["skipped"] += 1
            continue
        parsed = {
            "source_id": r_data.get("source_id", 0),
            "target_id": r_data.get("target_id", 0),
            "source_type": r_data.get("source_type", "knowledge"),
            "target_type": r_data.get("target_type", "knowledge"),
            "relation_type": r_data.get("relation_type", "related"),
            "score": r_data.get("score", 1.0),
            "source": r_data.get("source", "manual"),
            "metadata_json": r_data.get("metadata_json") or {},
        }
        created = r_data.get("created_at")
        if created and isinstance(created, str):
            try:
                parsed["created_at"] = datetime.datetime.fromisoformat(created)
            except (ValueError, TypeError):
                parsed["created_at"] = datetime.datetime.utcnow()
        else:
            parsed["created_at"] = datetime.datetime.utcnow()
        if rid:
            parsed["id"] = rid
        db.add(Relation(**parsed))
        result["imported"] += 1
    db.flush()
    for s_data in data.get("settings", []):
        sid = s_data.get("id", 0)
        if db.query(Setting).filter(Setting.id == sid).first():
            result["skipped"] += 1
            continue
        parsed = {
            "category": s_data.get("category", "general"),
            "key": s_data.get("key", ""),
            "value": s_data.get("value", {}),
        }
        for dt_key in ["created_at", "updated_at"]:
            v = s_data.get(dt_key)
            if v and isinstance(v, str):
                try:
                    parsed[dt_key] = datetime.datetime.fromisoformat(v)
                except (ValueError, TypeError):
                    parsed[dt_key] = datetime.datetime.utcnow()
            else:
                parsed[dt_key] = datetime.datetime.utcnow()
        if sid:
            parsed["id"] = sid
        db.add(Setting(**parsed))
        result["imported"] += 1
    db.commit()
    return result


def _create_backup_archive(db, temp_dir):
    data = _get_db_data(db)
    data_json = os.path.join(temp_dir, "data.json")
    with open(data_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)
    files_dir = os.path.join(temp_dir, "files")
    if os.path.isdir(DATA_DIR):
        shutil.copytree(DATA_DIR, files_dir, dirs_exist_ok=True)
    zip_path = os.path.join(tempfile.gettempdir(), "akh_backup_temp.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(temp_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, temp_dir)
                zf.write(fpath, arcname)
    return zip_path


def _extract_backup_archive(zip_path, extract_dir):
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        data_json = os.path.join(extract_dir, "data.json")
        return data_json if os.path.isfile(data_json) else None
    except Exception as e:
        logger.error("Failed to extract backup archive: %s", str(e), exc_info=True)
        return None


def test_connection(url, username="", password=""):
    try:
        client = create_webdav_client(url, username, password)
        with_retry(lambda: client.exists("/"))
        return {"success": True, "message": "连接成功"}
    except HTTPError as e:
        msg = parse_webdav_error(e.status_code)
        logger.error("WebDAV test failed: status=%s, url=%s", e.status_code, url)
        return {"success": False, "message": "连接失败: " + msg}
    except Exception as e:
        logger.error("WebDAV test exception: %s", str(e), exc_info=True)
        return {"success": False, "message": "连接失败: " + str(e)[:200]}


def list_directories(url, username="", password="", path=""):
    try:
        client = create_webdav_client(url, username, password)
        clean = path.strip("/")
        bp = "/" + clean if clean else "/"
        items = with_retry(lambda: client.ls(bp))
        dirs = []
        for item in items:
            if isinstance(item, dict) and item.get("is_collection"):
                name = item.get("name", "")
                href = item.get("href", "")
                if name:
                    dirs.append({"name": name, "href": href})
        dirs.sort(key=lambda d: d["name"].lower())
        return dirs
    except Exception as e:
        logger.error("list_directories exception: %s", str(e), exc_info=True)
        return []


def backup_to_webdav(db, url, username="", password="", backup_path="akh-backups", retention_days=30):
    temp_dir = None
    try:
        client = create_webdav_client(url, username, password)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = BACKUP_FILE_PREFIX + timestamp + BACKUP_FILE_SUFFIX
        remote_path = backup_path.rstrip("/") + "/" + filename
        logger.info("Starting backup to %s/%s", url, remote_path)
        try:
            with_retry(lambda: client.mkdir(backup_path))
        except HTTPError:
            pass
        temp_dir = tempfile.mkdtemp(prefix="akh_backup_")
        zip_path = _create_backup_archive(db, temp_dir)
        with open(zip_path, "rb") as f:
            with_retry(lambda: client.upload_fileobj(f, remote_path, overwrite=True))
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        logger.info("Backup complete: %s (%.2f MB)", remote_path, size_mb)
        _cleanup_old_backups(client, backup_path, retention_days)
        data = _get_db_data(db)
        count = len(data.get("knowledge", []))
        return {
            "success": True,
            "message": "备份完成：{} ({:.1f} MB, {} 条知识)".format(filename, size_mb, count),
            "filename": filename, "size_mb": round(size_mb, 2), "count": count,
        }
    except HTTPError as e:
        msg = parse_webdav_error(e.status_code)
        logger.error("Backup HTTP error: status=%s", e.status_code)
        return {"success": False, "message": "备份失败: " + msg}
    except Exception as e:
        logger.error("Backup failed: %s", str(e), exc_info=True)
        return {"success": False, "message": "备份失败: " + str(e)[:200]}
    finally:
        if temp_dir and os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        zt = os.path.join(tempfile.gettempdir(), "akh_backup_temp.zip")
        if os.path.isfile(zt):
            try:
                os.remove(zt)
            except Exception:
                pass


def _cleanup_old_backups(client, backup_path, retention_days=30):
    if retention_days <= 0:
        return
    try:
        clean_path = backup_path.strip("/")
        items = client.ls("/" + clean_path if clean_path else "/")
        now = datetime.datetime.now().astimezone()
        deleted = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            if not (name.startswith(BACKUP_FILE_PREFIX) and name.endswith(BACKUP_FILE_SUFFIX)):
                continue
            modified = item.get("last_modified", None)
            if modified is None:
                continue
            if isinstance(modified, str):
                try:
                    modified = datetime.datetime.fromisoformat(modified)
                except (ValueError, TypeError):
                    continue
            if isinstance(modified, datetime.datetime) and modified.tzinfo is None:
                modified = modified.replace(tzinfo=now.tzinfo)
            age = (now - modified).total_seconds() / 86400
            if age > retention_days:
                try:
                    old_path = backup_path.rstrip("/") + "/" + name
                    client.remove(old_path)
                    deleted += 1
                    logger.info("Deleted old backup: %s (%.1f days)", old_path, age)
                except Exception as e:
                    logger.warning("Failed to delete old backup %s: %s", name, str(e))
        if deleted:
            logger.info("Cleaned up %d old backups (>%d days)", deleted, retention_days)
    except Exception as e:
        logger.warning("Backup cleanup error: %s", str(e))


def list_backups(url, username="", password="", backup_path="akh-backups"):
    try:
        client = create_webdav_client(url, username, password)
        clean_path = backup_path.strip("/")
        bp = "/" + clean_path if clean_path else "/"
        items = with_retry(lambda: client.ls(bp))
        files = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            if not (name.startswith(BACKUP_FILE_PREFIX) and name.endswith(BACKUP_FILE_SUFFIX)):
                continue
            href = item.get("href", "")
            size = item.get("content_length", 0) or 0
            modified = item.get("last_modified", None) or ""
            if isinstance(modified, datetime.datetime):
                modified = modified.isoformat()
            files.append({
                "name": name, "href": href, "size": size,
                "size_display": _format_size(size), "modified": str(modified),
            })
        files.sort(key=lambda f: f.get("modified", ""), reverse=True)
        return files
    except Exception as e:
        logger.error("list_backups exception: %s", str(e), exc_info=True)
        return []


def _format_size(size_bytes):
    if size_bytes < 1024:
        return str(size_bytes) + " B"
    elif size_bytes < 1024 * 1024:
        return "{:.1f} KB".format(size_bytes / 1024)
    else:
        return "{:.1f} MB".format(size_bytes / (1024 * 1024))


def download_backup(url, username="", password="", file_path=""):
    if not file_path:
        return None
    try:
        client = create_webdav_client(url, username, password)
        import io
        buf = io.BytesIO()
        with_retry(lambda: client.download_fileobj(file_path, buf))
        buf.seek(0)
        content = buf.read()
        logger.info("Downloaded backup: %s (%d bytes)", file_path, len(content))
        return content
    except Exception as e:
        logger.error("download_backup exception: %s", str(e), exc_info=True)
        return None


def import_backup_data(db, data):
    result = _import_db_data(db, data)
    files_data = data.get("files", [])
    if files_data:
        restored = 0
        for fi in files_data:
            rp = fi.get("path", "")
            cb = fi.get("content_base64", "")
            if not rp or not cb:
                continue
            ap = os.path.join(DATA_DIR, rp)
            try:
                os.makedirs(os.path.dirname(ap), exist_ok=True)
                with open(ap, "wb") as fh:
                    fh.write(base64.b64decode(cb))
                restored += 1
            except Exception as e:
                logger.warning("Could not restore file %s: %s", rp, str(e))
        if restored:
            logger.info("Restored %d data directory files", restored)
    return result


def _import_from_zip(db, zip_bytes):
    extract_dir = None
    try:
        zip_path = os.path.join(tempfile.gettempdir(), "akh_restore_temp.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)
        extract_dir = tempfile.mkdtemp(prefix="akh_restore_")
        data_json = _extract_backup_archive(zip_path, extract_dir)
        if data_json is None:
            return {"success": False, "message": "备份文件格式错误：未找到 data.json"}
        with open(data_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = _import_db_data(db, data)
        result["success"] = True
        files_src = os.path.join(extract_dir, "files")
        if os.path.isdir(files_src):
            for root, dirs, files in os.walk(files_src):
                for fname in files:
                    src_path = os.path.join(root, fname)
                    rel = os.path.relpath(src_path, files_src)
                    dst = os.path.join(DATA_DIR, rel)
                    try:
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src_path, dst)
                    except Exception as e:
                        logger.warning("Could not restore file %s: %s", rel, str(e))
            logger.info("Restored files to %s", DATA_DIR)
        return {"success": True, "message": "导入完成：新增{}条，跳过{}条".format(result["imported"], result["skipped"]), **result}
    except Exception as e:
        logger.error("Import from zip failed: %s", str(e), exc_info=True)
        return {"success": False, "message": "导入失败: " + str(e)[:200]}
    finally:
        if extract_dir and os.path.isdir(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)
        zt = os.path.join(tempfile.gettempdir(), "akh_restore_temp.zip")
        if os.path.isfile(zt):
            try:
                os.remove(zt)
            except Exception:
                pass


def import_from_webdav(db, url, username="", password="", file_path=""):
    content = download_backup(url, username, password, file_path)
    if content is None:
        return {"success": False, "message": "下载备份文件失败"}
    if content[:4] == b"PK\x03\x04":
        return _import_from_zip(db, content)
    try:
        data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error("Backup file parse error: %s", str(e))
        return {"success": False, "message": "备份文件解析失败: " + str(e)[:100]}
    result = import_backup_data(db, data)
    return {"success": True, "message": "导入完成：新增{}条，跳过{}条".format(result["imported"], result["skipped"]), **result}
