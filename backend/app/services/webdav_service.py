import json, datetime, os, hashlib, time
from typing import Optional, List
import httpx
from lxml import etree
from sqlalchemy.orm import Session
from app.models.models import Knowledge, Tag, KnowledgeTag

WEBDAV_XML_NS = "DAV:"


def _request_with_retry(method: str, url: str, username: str, password: str,
                         data=None, headers=None, timeout=60, max_retries=3):
    """Make a WebDAV request with retry on 429 (rate limit)."""
    auth = (username, password) if username else None
    h = headers or {}
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            with httpx.Client(auth=auth, verify=False, timeout=timeout) as client:
                resp = client.request(method, url, content=data, headers=h)
                if resp.status_code == 429:
                    if attempt < max_retries:
                        wait = (attempt + 1) * 2
                        time.sleep(wait)
                        continue
                resp.raise_for_status()
                return resp
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_retries:
                wait = (attempt + 1) * 2
                time.sleep(wait)
                continue
            last_exc = e
            if e.response.status_code != 429:
                raise
        except Exception as e:
            last_exc = e
            if attempt < max_retries:
                time.sleep(1)
                continue
    raise last_exc if last_exc else Exception("Request failed after retries")


def _request(method: str, url: str, username: str, password: str, data=None, headers=None, timeout=15, verify=False):
    """Low-level WebDAV HTTP request with 429 retry."""
    auth = (username, password) if username else None
    h = headers or {}
    for attempt in range(4):
        try:
            with httpx.Client(auth=auth, verify=verify, timeout=timeout) as client:
                resp = client.request(method, url, content=data, headers=h)
                if resp.status_code == 429:
                    if attempt < 3:
                        time.sleep((attempt + 1) * 2)
                        continue
                resp.raise_for_status()
                return resp
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < 3:
                time.sleep((attempt + 1) * 2)
                continue
            raise
    raise Exception("Max retries exceeded")


def _resolve_webdav_base(url: str, username: str, password: str) -> str:
    """Quickly find the actual WebDAV base URL. Short timeouts with delays between attempts."""
    base = url.rstrip("/")
    from urllib.parse import urlparse
    parsed = urlparse(base)
    server_root = parsed.scheme + "://" + parsed.netloc
    path_part = parsed.path.strip("/")
    dav_url = server_root + "/dav"
    if path_part:
        dav_url += "/" + path_part
    auth = (username, password) if username else None
    candidates = [dav_url, base, server_root + "/dav"]
    for idx, c in enumerate(candidates):
        if idx > 0:
            time.sleep(0.5)
        try:
            with httpx.Client(auth=auth, verify=False, timeout=3) as client:
                body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/></d:prop></d:propfind>'
                resp = client.request("PROPFIND", c + "/", content=body, headers={"Depth": "0"})
                if resp.status_code < 500:
                    return c
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403, 405, 429):
                return c
        except Exception:
            pass
    return dav_url


def test_connection(url: str, username: str, password: str) -> dict:
    """Test WebDAV connection."""
    time.sleep(0.3)
    resolved = _resolve_webdav_base(url, username, password)
    base = resolved + "/"
    auth = (username, password) if username else None
    try:
        with httpx.Client(auth=auth, verify=False, timeout=8) as client:
            body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/></d:prop></d:propfind>'
            resp = client.request("PROPFIND", base, content=body, headers={"Depth": "0"})
            return {"success": True, "message": "WebDAV 连接成功", "status": resp.status_code}
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            return {"success": True, "message": "WebDAV 连接成功（需要认证）", "status": e.response.status_code}
    except Exception:
        pass
    try:
        with httpx.Client(auth=auth, verify=False, timeout=8) as client:
            resp = client.request("OPTIONS", base)
            if resp.status_code < 400:
                return {"success": True, "message": "WebDAV 连接成功", "status": resp.status_code}
            return {"success": False, "message": "服务器返回" + str(resp.status_code)}
    except httpx.ConnectError:
        return {"success": False, "message": "无法连接到服务器，请检查地址是否正确"}
    except Exception as e:
        return {"success": False, "message": "连接失败: " + str(e)[:200]}


def _ensure_dir(url: str, path: str, username: str, password: str):
    """Ensure a directory exists on WebDAV (MKCOL if not exists)."""
    parts = [p for p in path.split("/") if p]
    current = url.rstrip("/")
    for part in parts:
        current += "/" + part
        try:
            _request_with_retry("PROPFIND", current, username, password,
                     data='<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/></d:prop></d:propfind>',
                     headers={"Depth": "0"}, timeout=5)
            continue
        except httpx.HTTPStatusError:
            pass
        try:
            _request_with_retry("MKCOL", current, username, password, timeout=5)
        except httpx.HTTPStatusError as e:
            if e.response.status_code not in (405, 409, 301, 302, 404):
                raise
            try:
                time.sleep(0.5)
                _request_with_retry("MKCOL", current, username, password, timeout=5)
            except Exception:
                pass


def backup_to_webdav(db: Session, url: str, username: str, password: str, backup_path: str) -> dict:
    """Backup all knowledge to WebDAV."""
    resolved = _resolve_webdav_base(url, username, password)
    _ensure_dir(resolved, backup_path, username, password)
    backup_dir_url = resolved.rstrip("/") + "/" + backup_path.strip("/")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"knowledge_backup_{timestamp}.json"
    file_url = backup_dir_url + "/" + filename
    knowledge_list = db.query(Knowledge).filter(Knowledge.is_active == True).all()
    data = []
    for kn in knowledge_list:
        item = {
            "title": kn.title, "content": kn.content, "summary": kn.summary or "",
            "source": kn.source or "manual", "source_url": kn.source_url or "",
            "file_type": kn.file_type or "markdown", "metadata": kn.metadata_json or {},
            "tags": [kt.tag.name for kt in kn.tags if kt.tag],
        }
        data.append(item)
    body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
    try:
        _request_with_retry("PUT", file_url, username, password, data=body,
                 headers={"Content-Type": "application/json"}, timeout=30)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return {"success": False, "message": "备份失败: 服务器频率限制(429)，请等待几分钟后重试", "status": 429}
        elif e.response.status_code in (405, 500, 502):
            return {"success": False, "message": f"备份失败: HTTP {e.response.status_code} - 服务器不支持PUT方法，请检查WebDAV配置", "status": e.response.status_code}
        return {"success": False, "message": f"备份失败: HTTP {e.response.status_code}", "status": e.response.status_code}
    except Exception as e:
        return {"success": False, "message": f"备份失败: {str(e)[:200]}"}
    return {"success": True, "message": f"备份成功，共 {len(data)} 条知识", "filename": filename}


def list_backups(url: str, username: str, password: str, backup_path: str) -> list:
    """List backup files on WebDAV."""
    try:
        resolved = _resolve_webdav_base(url, username, password)
        backup_dir_url = resolved.rstrip("/") + "/" + backup_path.strip("/")
        body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:displayname/><d:getcontentlength/><d:getlastmodified/><d:resourcetype/></d:prop></d:propfind>'
        time.sleep(0.5)
        try:
            resp = _request_with_retry("PROPFIND", backup_dir_url, username, password,
                     data=body, headers={"Depth": "1"}, timeout=15)
        except Exception:
            return []
        root = etree.fromstring(resp.content)
        ns = {"d": "DAV:"}
        files = []
        for resp_elem in root.findall(".//d:response", ns):
            href = resp_elem.findtext("d:href", "", ns)
            if not href:
                continue
            props = resp_elem.find("d:propstat/d:prop", ns)
            if props is None:
                continue
            rt = props.find("d:resourcetype", ns)
            is_dir = rt is not None and rt.find("d:collection", ns) is not None
            if is_dir:
                continue
            name = href.split("/")[-1]
            if not name or not name.endswith(".json"):
                continue
            size_text = props.findtext("d:getcontentlength", "0", ns)
            modified_text = props.findtext("d:getlastmodified", "", ns)
            files.append({
                "name": name, "href": href,
                "size": int(size_text) if size_text.isdigit() else 0,
                "modified": modified_text,
            })
        return sorted(files, key=lambda f: f["name"], reverse=True)
    except Exception:
        return []


def download_backup(url: str, username: str, password: str, file_href: str) -> Optional[bytes]:
    """Download a backup file from WebDAV."""
    try:
        resp = _request("GET", file_href, username, password, timeout=30)
        return resp.content
    except Exception:
        return None


def import_backup_data(db: Session, data: list) -> dict:
    """Import knowledge data from a backup JSON list."""
    imported = 0
    skipped = 0
    for item in data:
        title = item.get("title", "").strip()
        content = item.get("content", "").strip()
        if not title or not content:
            skipped += 1
            continue
        existing = db.query(Knowledge).filter(Knowledge.title == title).first()
        if existing:
            skipped += 1
            continue
        kn = Knowledge(
            title=title, content=content,
            summary=item.get("summary", ""),
            source=item.get("source", "manual"),
            source_url=item.get("source_url", ""),
            file_type=item.get("file_type", "markdown"),
            metadata_json=item.get("metadata", {}),
            token_count=len(content) // 2,
        )
        db.add(kn)
        db.flush()
        from app.services.knowledge_service import _chunk_text
        chunks_text = _chunk_text(content)
        from app.models.models import Chunk
        for i, ct in enumerate(chunks_text):
            chunk = Chunk(knowledge_id=kn.id, content=ct, chunk_index=i, token_count=len(ct) // 2)
            db.add(chunk)
        kn.chunk_count = len(chunks_text)
        tags = item.get("tags", [])
        if tags:
            for tname in tags:
                tag = db.query(Tag).filter(Tag.name == tname).first()
                if not tag:
                    tag = Tag(name=tname)
                    db.add(tag)
                    db.flush()
                db.add(KnowledgeTag(knowledge_id=kn.id, tag_id=tag.id))
        imported += 1
    db.commit()
    return {"imported": imported, "skipped": skipped}


def import_from_webdav(db: Session, url: str, username: str, password: str, file_href: str) -> dict:
    """Download a backup file from WebDAV and import."""
    content = download_backup(url, username, password, file_href)
    if content is None:
        return {"success": False, "message": "下载备份文件失败"}
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception as e:
        return {"success": False, "message": "解析备份文件失败: " + str(e)[:100]}
    result = import_backup_data(db, data)
    return {"success": True, "message": "导入完成：新增" + str(result['imported']) + "条，跳过 " + str(result['skipped']) + "条"}


def list_directories(url: str, username: str, password: str, path: str = "") -> list:
    """List subdirectories on WebDAV."""
    try:
        resolved_url = _resolve_webdav_base(url, username, password)
        from urllib.parse import urlparse
        parsed = urlparse(resolved_url)
        server_root = parsed.scheme + "://" + parsed.netloc

        if not path:
            targets = [resolved_url.rstrip("/") + "/", url.rstrip("/") + "/"]
        else:
            if path.startswith("http"):
                targets = [path]
            elif path.startswith("/"):
                targets = [server_root + path, url.rstrip("/") + path]
            else:
                targets = [resolved_url.rstrip("/") + "/" + path, url.rstrip("/") + "/" + path]

        body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:displayname/><d:resourcetype/></d:prop></d:propfind>'

        for idx, target in enumerate(targets):
            if idx > 0:
                time.sleep(0.5)
            target = target.rstrip("/") + "/"
            try:
                resp = _request_with_retry("PROPFIND", target, username, password,
                                 data=body, headers={"Depth": "1"}, timeout=10)
            except Exception:
                continue

            root = etree.fromstring(resp.content)
            ns = {"d": "DAV:"}
            dirs = []
            for resp_elem in root.findall(".//d:response", ns):
                href = resp_elem.findtext("d:href", "", ns)
                if not href:
                    continue
                props = resp_elem.find("d:propstat/d:prop", ns)
                if props is None:
                    continue
                rt = props.find("d:resourcetype", ns)
                is_dir = rt is not None and rt.find("d:collection", ns) is not None
                if not is_dir:
                    continue
                name = href.rstrip("/").split("/")[-1]
                if not name:
                    continue
                dirs.append({"name": name, "path": href})
            return sorted(dirs, key=lambda d: d["name"])

        return []
    except Exception:
        return []
