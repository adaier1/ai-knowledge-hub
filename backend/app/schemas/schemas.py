from pydantic import BaseModel, Field
from typing import Optional, List, Any
import datetime

class KnowledgeCreate(BaseModel):
    title: str
    content: str
    summary: str = ""
    source: str = "manual"
    source_url: str = ""
    file_type: str = "markdown"
    metadata: dict = {}
    tags: List[str] = []
    collection_ids: List[int] = []

class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    file_type: Optional[str] = None
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    collection_ids: Optional[List[int]] = None

class KnowledgeResponse(BaseModel):
    id: int
    title: str
    content: str
    summary: str = ""
    source: str = "manual"
    source_url: str = ""
    file_type: str = "markdown"
    metadata: dict = {}
    token_count: int = 0
    chunk_count: int = 0
    is_active: bool = True
    tags: List[str] = []
    collections: List[dict] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    class Config:
        from_attributes = True

class KnowledgeListItem(BaseModel):
    id: int
    title: str
    summary: str = ""
    source: str = "manual"
    file_type: str = "markdown"
    token_count: int = 0
    chunk_count: int = 0
    tags: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    class Config:
        from_attributes = True

class ChunkResponse(BaseModel):
    id: int
    knowledge_id: int
    content: str
    chunk_index: int = 0
    token_count: int = 0
    metadata: dict = {}
    created_at: Optional[str] = None
    class Config:
        from_attributes = True

class CollectionCreate(BaseModel):
    name: str
    description: str = ""
    icon: str = "folder"
    color: str = "#1890ff"
    sort_order: int = 0

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None

class CollectionResponse(BaseModel):
    id: int
    name: str
    description: str = ""
    icon: str = "folder"
    color: str = "#1890ff"
    sort_order: int = 0
    knowledge_count: int = 0
    created_at: Optional[str] = None
    class Config:
        from_attributes = True

class TagCreate(BaseModel):
    name: str
    color: str = "#1890ff"

class TagResponse(BaseModel):
    id: int
    name: str
    color: str = "#1890ff"
    knowledge_count: int = 0
    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    query: str
    search_type: str = "hybrid"
    collections: List[int] = []
    tags: List[str] = []
    limit: int = 10
    offset: int = 0

class SearchResult(BaseModel):
    knowledge_id: int
    chunk_id: int
    title: str
    content: str
    score: float = 0.0
    source: str = ""

class GraphNode(BaseModel):
    id: str
    label: str
    type: str = "knowledge"
    group: str = ""
    size: int = 30

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str = ""
    weight: float = 1.0
    type: str = "relation"

class GraphResponse(BaseModel):
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []

class EntityCreate(BaseModel):
    name: str
    type: str = "general"
    description: str = ""
    metadata: dict = {}

class RelationCreate(BaseModel):
    source_id: int
    target_id: int
    source_type: str
    target_type: str
    relation_type: str
    score: float = 1.0
    source: str = "manual"

class MemoryCreate(BaseModel):
    agent_id: str
    memory_type: str = "episodic"
    content: str
    summary: str = ""
    importance: int = 5
    metadata: dict = {}

class AnalyticsResponse(BaseModel):
    knowledge_count: int = 0
    chunk_count: int = 0
    embedding_count: int = 0
    collection_count: int = 0
    graph_nodes: int = 0
    graph_relations: int = 0
    search_count: int = 0
    hit_rate: float = 0.0
    avg_latency: float = 0.0
    storage_size: str = "0 B"
    mcp_calls: int = 0

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MCPConfigResponse(BaseModel):
    name: str = "ai-knowledge-hub"
    description: str = "MCP Server for AI Knowledge Hub"
    version: str = "1.0.0"
    tools: List[dict] = []
    auth_type: str = "api_key"

class DatabaseTableInfo(BaseModel):
    name: str
    columns: List[dict] = []
    row_count: int = 0
    indexes: List[str] = []

class SQLQueryRequest(BaseModel):
    sql: str

class SQLQueryResponse(BaseModel):
    columns: List[str] = []
    rows: List[List[Any]] = []
    row_count: int = 0
    elapsed_ms: float = 0.0
