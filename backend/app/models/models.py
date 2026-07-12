import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean, Index
)
from sqlalchemy.orm import relationship
from app.database import Base

class Knowledge(Base):
    __tablename__ = "knowledge"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, default="")
    source = Column(String(100), default="manual")
    source_url = Column(String(1000), default="")
    file_type = Column(String(20), default="markdown")
    metadata_json = Column(JSON, default=dict)
    token_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    chunks = relationship("Chunk", back_populates="knowledge", cascade="all, delete-orphan")
    tags = relationship("KnowledgeTag", back_populates="knowledge", cascade="all, delete-orphan")

    @classmethod
    def setup_fts(cls, engine):
        conn = engine.raw_connection()
        try:
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(title, content, summary, content=knowledge, content_rowid=id)")
        except Exception:
            pass
        finally:
            conn.close()

    FTS_COLUMNS = ["title", "content", "summary"]

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    knowledge = relationship("Knowledge", back_populates="chunks")

class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), default="openai")
    model = Column(String(100), default="text-embedding-3-small")
    dimension = Column(Integer, default=1536)
    vector_blob = Column(Text, default="")
    vector_version = Column(String(20), default="v1", index=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, default="")
    icon = Column(String(50), default="folder")
    color = Column(String(20), default="#1890ff")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class CollectionItem(Base):
    __tablename__ = "collection_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(Integer, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    color = Column(String(20), default="#1890ff")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class KnowledgeTag(Base):
    __tablename__ = "knowledge_tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
    knowledge = relationship("Knowledge", back_populates="tags")
    tag = relationship("Tag")

class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False, index=True)
    type = Column(String(50), default="general")
    description = Column(Text, default="")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Relation(Base):
    __tablename__ = "relations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, nullable=False, index=True)
    target_id = Column(Integer, nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    target_type = Column(String(50), nullable=False)
    relation_type = Column(String(50), nullable=False, index=True)
    score = Column(Float, default=1.0)
    source = Column(String(50), default="manual")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SearchLog(Base):
    __tablename__ = "search_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(500), nullable=False, index=True)
    search_type = Column(String(50), default="hybrid")
    results_count = Column(Integer, default=0)
    top_chunk_ids = Column(JSON, default=list)
    final_context = Column(Text, default="")
    latency_ms = Column(Float, default=0.0)
    hit = Column(Boolean, default=True)
    score = Column(Float, default=0.0)
    source = Column(String(50), default="webui")
    agent_name = Column(String(100), default="")
    llm_model = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Statistic(Base):
    __tablename__ = "statistics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)
    metric = Column(String(100), nullable=False, index=True)
    value = Column(Float, default=0.0)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False, index=True)
    key = Column(String(200), nullable=False)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    __table_args__ = (Index("idx_settings_category_key", "category", "key", unique=True),)

class MCPKey(Base):
    __tablename__ = "mcp_keys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    key_hash = Column(String(128), nullable=False, unique=True)
    role = Column(String(50), default="agent")
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Memory(Base):
    __tablename__ = "memory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(200), nullable=False, index=True)
    memory_type = Column(String(50), default="episodic")
    content = Column(Text, nullable=False)
    summary = Column(Text, default="")
    importance = Column(Integer, default=5)
    is_pinned = Column(Boolean, default=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

ALL_MODELS = [
    Knowledge, Chunk, Embedding, Collection, CollectionItem,
    Tag, KnowledgeTag, Entity, Relation,
    SearchLog, Statistic, Setting, MCPKey, Memory
]


