from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.models import Knowledge, Chunk, Embedding, Collection, Relation, Entity, SearchLog, Statistic
import os

def get_dashboard_stats(db: Session):
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    one_week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    knowledge_count = db.query(Knowledge).count()
    chunk_count = db.query(Chunk).count()
    embedding_count = db.query(Embedding).count()
    collection_count = db.query(Collection).count()
    graph_nodes = db.query(Knowledge).filter(Knowledge.is_active == True).count() + db.query(Entity).count()
    graph_relations = db.query(Relation).count()
    search_count = db.query(SearchLog).count()
    total_searches = search_count
    hit_searches = db.query(SearchLog).filter(SearchLog.hit == True).count()
    hit_rate = hit_searches / total_searches if total_searches > 0 else 0.0
    avg_latency = db.query(func.avg(SearchLog.latency_ms)).scalar() or 0.0
    storage = _get_storage_size()
    mcp_calls = db.query(SearchLog).filter(SearchLog.source == "mcp").count()

    # Current week (now - 7 days)
    cur_week_search = db.query(func.count(SearchLog.id)).filter(SearchLog.created_at >= one_week_ago).scalar() or 0
    cur_week_hit = db.query(func.count(SearchLog.id)).filter(SearchLog.created_at >= one_week_ago, SearchLog.hit == True).scalar() or 0
    cur_week_latency = db.query(func.avg(SearchLog.latency_ms)).filter(SearchLog.created_at >= one_week_ago).scalar() or 0
    cur_week_knowledge = db.query(func.count(Knowledge.id)).filter(Knowledge.created_at >= one_week_ago).scalar() or 0

    # Last week (7-14 days ago)
    last_week_search = db.query(func.count(SearchLog.id)).filter(SearchLog.created_at < one_week_ago, SearchLog.created_at >= two_weeks_ago).scalar() or 0
    last_week_hit = db.query(func.count(SearchLog.id)).filter(SearchLog.created_at < one_week_ago, SearchLog.created_at >= two_weeks_ago, SearchLog.hit == True).scalar() or 0
    last_week_latency = db.query(func.avg(SearchLog.latency_ms)).filter(SearchLog.created_at < one_week_ago, SearchLog.created_at >= two_weeks_ago).scalar() or 0
    last_week_knowledge = db.query(func.count(Knowledge.id)).filter(Knowledge.created_at < one_week_ago, Knowledge.created_at >= two_weeks_ago).scalar() or 0

    # Week-over-week: cur_week vs last_week
    search_change = _calc_change(cur_week_search, last_week_search)
    cur_rate = cur_week_hit / cur_week_search if cur_week_search > 0 else 0
    last_rate = last_week_hit / last_week_search if last_week_search > 0 else 0
    hit_change = _calc_change(cur_rate, last_rate)
    latency_change = _calc_change(cur_week_latency, last_week_latency)
    knowledge_change = _calc_change(cur_week_knowledge, last_week_knowledge)

    return {
        "knowledge_count": knowledge_count, "chunk_count": chunk_count,
        "embedding_count": embedding_count, "collection_count": collection_count,
        "graph_nodes": graph_nodes, "graph_relations": graph_relations,
        "search_count": search_count, "hit_rate": round(hit_rate, 4),
        "avg_latency": round(float(avg_latency), 2), "storage_size": storage,
        "mcp_calls": mcp_calls,
        "search_change": round(search_change, 1),
        "hit_change": round(hit_change, 1),
        "latency_change": round(latency_change, 1),
        "knowledge_change": round(knowledge_change, 1),
    }

def _calc_change(current, previous):
    if previous == 0 and current == 0:
        return 0
    if previous == 0:
        return 100
    return (current - previous) / previous * 100
def _get_storage_size() -> str:
    total = 0
    for root, dirs, files in os.walk("./data"):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except:
                pass
    for unit in ["B", "KB", "MB", "GB"]:
        if total < 1024:
            return f"{total:.1f} {unit}"
        total /= 1024
    return f"{total:.1f} TB"

def get_trends(db: Session, days: int = 30):
    from datetime import datetime, timedelta
    start = datetime.utcnow() - timedelta(days=days)
    logs = db.query(SearchLog).filter(SearchLog.created_at >= start).order_by(SearchLog.created_at).all()
    daily = {}
    for log in logs:
        day = log.created_at.strftime("%Y-%m-%d")
        daily.setdefault(day, {"count": 0, "hits": 0, "latency": 0.0})
        daily[day]["count"] += 1
        if log.hit:
            daily[day]["hits"] += 1
        daily[day]["latency"] += log.latency_ms
    result = []
    for day in sorted(daily.keys()):
        d = daily[day]
        result.append({
            "date": day, "count": d["count"],
            "hit_rate": round(d["hits"] / d["count"], 4) if d["count"] > 0 else 0,
            "avg_latency": round(d["latency"] / d["count"], 2) if d["count"] > 0 else 0
        })
    return result

def get_top_queries(db: Session, limit: int = 10):
    results = db.query(SearchLog.query, func.count(SearchLog.id).label("count")).group_by(SearchLog.query).order_by(desc("count")).limit(limit).all()
    return [{"query": r[0], "count": r[1]} for r in results]

def get_top_knowledge(db: Session, limit: int = 10):
    from collections import Counter
    logs = db.query(SearchLog).order_by(SearchLog.created_at.desc()).limit(500).all()
    counts = Counter()
    for log in logs:
        for chunk_id in (log.top_chunk_ids or []):
            counts[chunk_id] += 1
    top_chunk_ids = [cid for cid, _ in counts.most_common(limit)]
    knowledges = []
    for cid in top_chunk_ids:
        chunk = db.query(Chunk).filter(Chunk.id == cid).first()
        if chunk:
            kn = db.query(Knowledge).filter(Knowledge.id == chunk.knowledge_id).first()
            if kn:
                knowledges.append({"id": kn.id, "title": kn.title, "count": counts[cid]})
    return knowledges
