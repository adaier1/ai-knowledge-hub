import json, datetime
from typing import Any
from sqlalchemy.orm import Session
from app.services.knowledge_service import create_knowledge, update_knowledge, delete_knowledge, get_knowledge, list_knowledge, get_related_knowledge
from app.services.search_service import hybrid_search, search_by_tag, search_by_collection, log_search
from app.services.graph_service import get_graph_data, find_path, get_graph_statistics
from app.services.embedding_service import embedding_service
from app.services.memory_service import create_memory, recall_memories, search_memories, update_memory, delete_memory, pin_memory
from app.models.models import Knowledge, Chunk, Tag, KnowledgeTag, Collection, CollectionItem, Entity, Relation
from app.schemas.schemas import KnowledgeCreate

MCP_TOOL_DEFS = [
    {"name": "search_knowledge", "description": "Search knowledge by keyword or hybrid search", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "search_type": {"type": "string", "default": "hybrid"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}},
    {"name": "semantic_search", "description": "Semantic/vector search", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}},
    {"name": "hybrid_search", "description": "Hybrid keyword + semantic search", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}},
    {"name": "keyword_search", "description": "Pure keyword FTS5 search", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}},
    {"name": "graph_search", "description": "Get knowledge graph data", "input_schema": {"type": "object", "properties": {"center_id": {"type": "integer"}, "depth": {"type": "integer", "default": 1}, "limit": {"type": "integer", "default": 100}}}},
    {"name": "search_by_tag", "description": "Search by tag", "input_schema": {"type": "object", "properties": {"tag": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["tag"]}},
    {"name": "search_by_collection", "description": "Search by collection", "input_schema": {"type": "object", "properties": {"collection_id": {"type": "integer"}, "limit": {"type": "integer", "default": 10}}, "required": ["collection_id"]}},
    {"name": "get_document", "description": "Get full document by ID", "input_schema": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}},
    {"name": "get_chunk", "description": "Get document chunk by ID", "input_schema": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}},
    {"name": "get_related", "description": "Get related documents", "input_schema": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}},
    {"name": "create_document", "description": "Create a new knowledge document", "input_schema": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}, "summary": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}, "required": ["title", "content"]}},
    {"name": "update_document", "description": "Update a knowledge document", "input_schema": {"type": "object", "properties": {"id": {"type": "integer"}, "title": {"type": "string"}, "content": {"type": "string"}, "summary": {"type": "string"}}, "required": ["id"]}},
    {"name": "delete_document", "description": "Delete a knowledge document", "input_schema": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}},
    {"name": "create_entity", "description": "Create an entity", "input_schema": {"type": "object", "properties": {"name": {"type": "string"}, "type": {"type": "string", "default": "general"}, "description": {"type": "string"}}, "required": ["name"]}},
    {"name": "create_relation", "description": "Create a relation", "input_schema": {"type": "object", "properties": {"source_id": {"type": "integer"}, "target_id": {"type": "integer"}, "source_type": {"type": "string"}, "target_type": {"type": "string"}, "relation_type": {"type": "string"}}, "required": ["source_id", "target_id", "source_type", "target_type", "relation_type"]}},
    {"name": "create_tag", "description": "Create a tag", "input_schema": {"type": "object", "properties": {"name": {"type": "string"}, "color": {"type": "string"}}, "required": ["name"]}},
    {"name": "remember", "description": "Store an agent memory", "input_schema": {"type": "object", "properties": {"agent_id": {"type": "string"}, "content": {"type": "string"}, "importance": {"type": "integer", "default": 5}}, "required": ["agent_id", "content"]}},
    {"name": "recall", "description": "Recall agent memories", "input_schema": {"type": "object", "properties": {"agent_id": {"type": "string"}, "limit": {"type": "integer", "default": 20}}, "required": ["agent_id"]}},
    {"name": "forget", "description": "Delete a memory", "input_schema": {"type": "object", "properties": {"memory_id": {"type": "integer"}}, "required": ["memory_id"]}},
    {"name": "find_neighbors", "description": "Find neighbor nodes in graph", "input_schema": {"type": "object", "properties": {"node_id": {"type": "integer"}, "node_type": {"type": "string"}, "depth": {"type": "integer", "default": 1}}, "required": ["node_id"]}},
    {"name": "find_path", "description": "Find path between two nodes", "input_schema": {"type": "object", "properties": {"source_id": {"type": "integer"}, "target_id": {"type": "integer"}}, "required": ["source_id", "target_id"]}},
    {"name": "graph_statistics", "description": "Get graph statistics", "input_schema": {"type": "object", "properties": {}}},
    {"name": "statistics", "description": "Get knowledge statistics", "input_schema": {"type": "object", "properties": {}}},
]

def execute_mcp_tool(db: Session, tool_name: str, arguments: dict) -> Any:
    if tool_name in ("search_knowledge", "keyword_search"):
        results = hybrid_search(db, arguments.get("query", ""), arguments.get("limit", 10))
        return {"results": results}
    elif tool_name == "semantic_search":
        results = embedding_service.semantic_search(db, arguments.get("query", ""), arguments.get("limit", 10))
        return {"results": results}
    elif tool_name == "hybrid_search":
        results = hybrid_search(db, arguments.get("query", ""), arguments.get("limit", 10))
        return {"results": results}
    elif tool_name == "graph_search":
        data = get_graph_data(db, arguments.get("center_id"), "knowledge", arguments.get("depth", 1), arguments.get("limit", 100))
        return data
    elif tool_name == "search_by_tag":
        results = search_by_tag(db, arguments["tag"], arguments.get("limit", 10))
        return {"results": results}
    elif tool_name == "search_by_collection":
        results = search_by_collection(db, arguments["collection_id"], arguments.get("limit", 10))
        return {"results": results}
    elif tool_name == "get_document":
        kn = get_knowledge(db, arguments["id"])
        return {"document": {"id": kn.id, "title": kn.title, "content": kn.content, "summary": kn.summary} if kn else None}
    elif tool_name == "get_chunk":
        chunk = db.query(Chunk).filter(Chunk.id == arguments["id"]).first()
        return {"chunk": {"id": chunk.id, "content": chunk.content, "chunk_index": chunk.chunk_index} if chunk else None}
    elif tool_name == "get_related":
        related = get_related_knowledge(db, arguments["id"])
        return {"related": [{"id": k.id, "title": k.title} for k in related]}
    elif tool_name == "create_document":
        data = KnowledgeCreate(title=arguments["title"], content=arguments["content"], summary=arguments.get("summary", ""), tags=arguments.get("tags", []))
        kn = create_knowledge(db, data)
        return {"id": kn.id, "title": kn.title, "message": "Created"}
    elif tool_name == "update_document":
        kn = get_knowledge(db, arguments["id"])
        if not kn:
            return {"error": "Not found"}
        from app.schemas.schemas import KnowledgeUpdate
        data = KnowledgeUpdate(title=arguments.get("title"), content=arguments.get("content"), summary=arguments.get("summary"))
        kn = update_knowledge(db, arguments["id"], data)
        return {"id": kn.id, "message": "Updated"}
    elif tool_name == "delete_document":
        ok = delete_knowledge(db, arguments["id"])
        return {"success": ok}
    elif tool_name == "create_entity":
        ent = Entity(name=arguments["name"], type=arguments.get("type", "general"), description=arguments.get("description", ""))
        db.add(ent)
        db.commit()
        return {"id": ent.id, "name": ent.name}
    elif tool_name == "create_relation":
        rel = Relation(source_id=arguments["source_id"], target_id=arguments["target_id"],
                       source_type=arguments["source_type"], target_type=arguments["target_type"],
                       relation_type=arguments["relation_type"])
        db.add(rel)
        db.commit()
        return {"id": rel.id, "type": rel.relation_type}
    elif tool_name == "create_tag":
        tag = Tag(name=arguments["name"], color=arguments.get("color", "#1890ff"))
        db.add(tag)
        db.commit()
        return {"id": tag.id, "name": tag.name}
    elif tool_name == "remember":
        mem = create_memory(db, arguments["agent_id"], arguments["content"], importance=arguments.get("importance", 5))
        return {"id": mem.id, "message": "Remembered"}
    elif tool_name == "recall":
        mems = recall_memories(db, arguments["agent_id"], arguments.get("limit", 20))
        return {"memories": [{"id": m.id, "content": m.content, "importance": m.importance, "is_pinned": m.is_pinned, "created_at": m.created_at.isoformat() if m.created_at else None} for m in mems]}
    elif tool_name == "forget":
        ok = delete_memory(db, arguments["memory_id"])
        return {"success": ok}
    elif tool_name in ("find_neighbors",):
        data = get_graph_data(db, arguments.get("node_id"), arguments.get("node_type", "knowledge"), arguments.get("depth", 1), 100)
        return data
    elif tool_name == "find_path":
        result = find_path(db, arguments["source_id"], arguments["target_id"])
        return result
    elif tool_name == "graph_statistics":
        return get_graph_statistics(db)
    elif tool_name == "statistics":
        from app.services.analytics_service import get_dashboard_stats
        return get_dashboard_stats(db)
    return {"error": f"Unknown tool: {tool_name}"}
