# AI Knowledge Hub — API 接口规范文档

> 版本: v1.0  
> 最后更新: 2026-07-08  
> 基础路径: /api  
> 认证方式: Bearer Token (JWT) / API Key  
> 后端框架: FastAPI (Python)

---

## 1. 认证模块 (Auth)

### POST /api/auth/login
登录获取 JWT Token。

**请求体:**
\`\`\`json
{
  "username": "string",
  "password": "string"
}
\`\`\`

**响应:**
\`\`\`json
{
  "access_token": "string",
  "token_type": "bearer"
}
\`\`\`

---

## 2. 知识库模块 (Knowledge)

### GET /api/knowledge
获取知识列表。

**查询参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |
| search | string | - | 搜索关键词 |
| tag | string | - | 按标签筛选 |
| sort | string | created_at | 排序字段 |
| order | string | desc | 排序方向 |

**响应:**
\`\`\`json
{
  "items": [
    {
      "id": "int",
      "title": "string",
      "summary": "string",
      "source": "string",
      "file_type": "string",
      "token_count": "int",
      "chunk_count": "int",
      "tags": [{"id": "int", "name": "string"}],
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ],
  "total": "int",
  "page": "int",
  "page_size": "int"
}
\`\`\`

### GET /api/knowledge/{id}
获取单条知识详情。

**响应:**
\`\`\`json
{
  "id": "int",
  "title": "string",
  "content": "string",
  "summary": "string",
  "source": "string",
  "source_url": "string",
  "file_type": "string",
  "metadata_json": "object",
  "token_count": "int",
  "chunk_count": "int",
  "tags": [{"id": "int", "name": "string", "color": "string"}],
  "created_at": "datetime",
  "updated_at": "datetime"
}
\`\`\`

### POST /api/knowledge
创建知识条目。

**请求体:**
\`\`\`json
{
  "title": "string (required)",
  "content": "string (required)",
  "summary": "string",
  "source": "string",
  "source_url": "string",
  "file_type": "string",
  "tags": ["string"]
}
\`\`\`

### PUT /api/knowledge/{id}
更新知识条目。

**请求体:** 同创建，所有字段可选

### DELETE /api/knowledge/{id}
删除知识条目。

### GET /api/knowledge/{id}/chunks
获取知识的 Chunk 列表。

### GET /api/knowledge/{id}/related
获取相关知识。

### POST /api/knowledge/{id}/embed
为知识生成向量嵌入。

---

## 3. 搜索模块 (Search)

### POST /api/search
执行混合搜索。

**请求体:**
\`\`\`json
{
  "query": "string (required)",
  "search_type": "string (hybrid|semantic|keyword|tag|collection)",
  "limit": "int (default: 10)",
  "tag": "string",
  "collection_id": "int",
  "min_score": "float"
}
\`\`\`

**响应:**
\`\`\`json
{
  "results": [
    {
      "id": "int",
      "knowledge_id": "int",
      "title": "string",
      "content": "string",
      "score": "float",
      "source": "string"
    }
  ],
  "total": "int",
  "search_type": "string"
}
\`\`\`

### GET /api/search/logs
获取搜索日志。

**查询参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | int | 50 | 返回条数 |
| offset | int | 0 | 偏移量 |
| query | string | - | 搜索关键词筛选 |

**响应:**
\`\`\`json
{
  "items": [
    {
      "id": "int",
      "query": "string",
      "search_type": "string",
      "results_count": "int",
      "latency_ms": "float",
      "hit": "bool",
      "source": "string",
      "created_at": "datetime"
    }
  ],
  "total": "int"
}
\`\`\`

---

## 4. 图表模块 (Graph)

### GET /api/graph
获取图谱数据。

**查询参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| center_id | int | - | 中心节点 ID |
| node_type | string | knowledge | 节点类型 |
| depth | int | 1 | 展开深度 |
| limit | int | 200 | 最大节点数 |

### GET /api/graph/statistics
获取图谱统计。

### GET /api/graph/entities
获取实体列表。

### GET /api/graph/relations
获取关系列表。

---

## 5. 合集模块 (Collections)

### GET /api/collections
获取所有合集。

### POST /api/collections
创建合集。

**请求体:**
\`\`\`json
{
  "name": "string (required)",
  "description": "string",
  "icon": "string",
  "color": "string"
}
\`\`\`

### PUT /api/collections/{id}
更新合集。

### DELETE /api/collections/{id}
删除合集。

---

## 6. 统计模块 (Analytics)

### GET /api/analytics/dashboard
获取仪表盘统计。

**响应:**
\`\`\`json
{
  "knowledge_count": "int",
  "chunk_count": "int",
  "embedding_count": "int",
  "collection_count": "int",
  "graph_nodes": "int",
  "graph_relations": "int",
  "search_count": "int",
  "hit_rate": "float",
  "avg_latency": "float",
  "storage_size": "string",
  "mcp_calls": "int"
}
\`\`\`

### GET /api/analytics/trends
获取搜索趋势。

**查询参数:** days (int, default: 30)

**响应:**
\`\`\`json
[
  {
    "date": "string (YYYY-MM-DD)",
    "count": "int",
    "hit_rate": "float",
    "avg_latency": "float"
  }
]
\`\`\`

### GET /api/analytics/top-queries
获取热门搜索词。

**查询参数:** limit (int, default: 10)

### GET /api/analytics/top-knowledge
获取热门知识。

**查询参数:** limit (int, default: 10)

---

## 7. 标签模块 (Tags)

### GET /api/tags
获取所有标签。

### POST /api/tags
创建标签。

**请求体:**
\`\`\`json
{
  "name": "string (required)",
  "color": "string"
}
\`\`\`

### DELETE /api/tags/{id}
删除标签。

---

## 8. 数据库浏览器 (Database)

### GET /api/database/files
列出所有 .db 文件。

### GET /api/database/tables
获取指定数据库的表列表。

**查询参数:** db_file (string)

### GET /api/database/tables/{table_name}
获取表数据。

### POST /api/database/query
执行 SQL 查询。

**请求体:**
\`\`\`json
{
  "sql": "string",
  "params": {}
}
\`\`\`

### GET /api/database/export
导出数据库文件 (blob)。

### POST /api/database/import
导入数据库文件 (multipart/form-data)。

---

## 9. 设置模块 (Settings)

### GET /api/settings/{category}
获取指定分类的所有设置。

### PUT /api/settings/{category}/{key}
更新指定设置。

**请求体:**
\`\`\`json
{
  "value": "any"
}
\`\`\`

---

## 10. MCP 服务模块 (MCP)

### GET /api/mcp/config
获取 MCP 配置信息。

### GET /api/mcp/keys
获取所有 API Key。

### POST /api/mcp/keys
创建 API Key。

**查询参数:** name (string), role (string, default: "agent")

### DELETE /api/mcp/keys/{id}
删除 API Key。

---

## 11. WebDAV 备份模块

### GET /api/webdav/config
获取 WebDAV 配置。

### PUT /api/webdav/config
保存 WebDAV 配置。

**请求体:**
\`\`\`json
{
  "url": "string",
  "username": "string",
  "password": "string",
  "backup_path": "string",
  "auto_backup": "bool",
  "backup_frequency": "string (daily|weekly|monthly)",
  "backup_time": "string (HH:MM)"
}
\`\`\`

### POST /api/webdav/test
测试 WebDAV 连接。

### POST /api/webdav/backup
立即执行备份。

### POST /api/webdav/backup-data
备份知识库数据（含数据库文件）。

### POST /api/webdav/restore-data
从备份恢复知识库数据。

**请求体:**
\`\`\`json
{
  "href": "string (备份文件URL)"
}
\`\`\`

### GET /api/webdav/backups
列出所有备份文件。

### POST /api/webdav/browse
浏览 WebDAV 目录。

### POST /api/webdav/import
从 WebDAV 导入备份。

### POST /api/webdav/import/local
从本地上传备份文件 (multipart/form-data)。

---

## 12. MCP 协议工具

MCP 服务端暴露的工具列表:

| 工具名 | 说明 | 必需参数 |
|--------|------|----------|
| search_knowledge | 混合搜索知识 | query |
| semantic_search | 语义搜索 | query |
| hybrid_search | 混合搜索 | query |
| keyword_search | 关键词搜索 | query |
| graph_search | 获取图谱数据 | - |
| search_by_tag | 按标签搜索 | tag |
| search_by_collection | 按合集搜索 | collection_id |
| get_document | 获取文档详情 | id |
| get_chunk | 获取 Chunk | id |
| get_related | 获取相关知识 | id |
| create_document | 创建文档 | title, content |
| update_document | 更新文档 | id |
| delete_document | 删除文档 | id |
| create_entity | 创建实体 | name |
| create_relation | 创建关系 | source_id, target_id |
| create_tag | 创建标签 | name |
| remember | 存储记忆 | agent_id, content |
| recall | 召回记忆 | agent_id |
| forget | 删除记忆 | memory_id |
| find_path | 查找路径 | source_id, target_id |
| graph_statistics | 图谱统计 | - |
| statistics | 知识统计 | - |

---

## 13. 系统

### GET /api/health
健康检查。

**响应:**
\`\`\`json
{
  "status": "ok",
  "app": "AI Knowledge Hub",
  "version": "1.0.0"
}
\`\`\`

---

## 14. 认证方式

### JWT Token
\`\`\`
Authorization: Bearer <jwt_token>
\`\`\`

### API Key (MCP)
\`\`\`
Authorization: Bearer <api_key>
\`\`\`

### 错误响应格式
\`\`\`json
{
  "detail": "错误信息"
}
\`\`\`
