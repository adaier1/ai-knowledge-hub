from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.models import Knowledge, Entity, Relation, Tag, KnowledgeTag, Collection

def get_graph_data(db: Session, center_id: Optional[int] = None, center_type: str = "knowledge",
                   depth: int = 1, limit: int = 200):
    nodes_dict, edges_dict = {}, {}
    added_ids = set()
    if center_id and center_type == "knowledge":
        kn = db.query(Knowledge).filter(Knowledge.id == center_id).first()
        if kn:
            _add_knowledge_node(db, kn, nodes_dict, added_ids)
            _expand_node(db, "knowledge", kn.id, depth, nodes_dict, edges_dict, added_ids, limit)
    else:
        knowledges = db.query(Knowledge).filter(Knowledge.is_active == True).limit(limit).all()
        for kn in knowledges:
            _add_knowledge_node(db, kn, nodes_dict, added_ids)
            if depth > 0:
                _expand_node(db, "knowledge", kn.id, depth, nodes_dict, edges_dict, added_ids, limit)
    
    # Build tag-based connections between knowledge nodes
    _add_tag_connections(db, nodes_dict, edges_dict, added_ids)
    
    return {"nodes": list(nodes_dict.values()), "edges": list(edges_dict.values())}

def _add_tag_connections(db: Session, nodes_dict: dict, edges_dict: dict, added_ids: set):
    # Find all knowledge IDs in the graph
    kn_ids = []
    for nid in nodes_dict:
        if nid.startswith('knowledge_'):
            try:
                kn_ids.append(int(nid.split('_')[1]))
            except:
                pass
    
    if not kn_ids:
        return
    
    # Get all knowledge-tag mappings for these knowledge items
    kts = db.query(KnowledgeTag).filter(KnowledgeTag.knowledge_id.in_(kn_ids)).all()
    
    # Build tag -> [knowledge_ids] mapping
    tag_to_knowledge = {}
    knowledge_tags = {}  # knowledge_id -> [tag_id]
    for kt in kts:
        if kt.tag_id not in tag_to_knowledge:
            tag_to_knowledge[kt.tag_id] = []
        tag_to_knowledge[kt.tag_id].append(kt.knowledge_id)
        if kt.knowledge_id not in knowledge_tags:
            knowledge_tags[kt.knowledge_id] = []
        if kt.tag_id not in knowledge_tags[kt.knowledge_id]:
            knowledge_tags[kt.knowledge_id].append(kt.tag_id)
    
    edge_num = 0
    added_edge_pairs = set()
    
    for tag_id, kn_ids_list in tag_to_knowledge.items():
        if len(kn_ids_list) < 2:
            continue
        
        # Get tag info
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            continue
        
        # Add tag node
        tag_nid = f"tag_{tag_id}"
        if tag_nid not in nodes_dict and (tag_nid not in added_ids):
            nodes_dict[tag_nid] = {"id": tag_nid, "label": f"#{tag.name}", "type": "tag", "group": "tag", "size": 20}
            added_ids.add(tag_nid)
        
        # Connect each knowledge to the tag
        for kn_id in kn_ids_list:
            kn_nid = f"knowledge_{kn_id}"
            if kn_nid in nodes_dict:
                eid = f"tag_edge_{tag_id}_{kn_id}"
                if eid not in edges_dict:
                    edges_dict[eid] = {"id": eid, "source": kn_nid, "target": tag_nid,
                                       "label": tag.name, "weight": 1, "type": "tag"}
        
        # Create direct knowledge-knowledge edges for items sharing this tag
        for i in range(len(kn_ids_list)):
            for j in range(i + 1, len(kn_ids_list)):
                src = f"knowledge_{kn_ids_list[i]}"
                tgt = f"knowledge_{kn_ids_list[j]}"
                if src in nodes_dict and tgt in nodes_dict:
                    pair_key = (src, tgt) if src < tgt else (tgt, src)
                    if pair_key not in added_edge_pairs:
                        edge_num += 1
                        eid = f"shared_tag_{edge_num}"
                        edges_dict[eid] = {"id": eid, "source": src, "target": tgt,
                                           "label": f"#{tag.name}", "weight": 0.5, "type": "shared_tag"}
                        added_edge_pairs.add(pair_key)

def _add_knowledge_node(db: Session, kn, nodes_dict: dict, added_ids: set):
    nid = f"knowledge_{kn.id}"
    if nid not in added_ids:
        added_ids.add(nid)
        nodes_dict[nid] = {"id": nid, "label": kn.title[:50], "type": "knowledge", "group": "knowledge", "size": 40}

def _expand_node(db: Session, node_type: str, node_id: int, depth: int,
                 nodes_dict: dict, edges_dict: dict, added_ids: set, limit: int):
    if depth <= 0 or len(nodes_dict) >= limit:
        return
    relations = db.query(Relation).filter(
        or_(and_(Relation.source_id == node_id, Relation.source_type == node_type),
            and_(Relation.target_id == node_id, Relation.target_type == node_type))
    ).limit(50).all()
    for rel in relations:
        eid = f"relation_{rel.id}"
        if eid not in edges_dict:
            s_type, s_id, t_type, t_id = rel.source_type, rel.source_id, rel.target_type, rel.target_id
            src_nid = f"{s_type}_{s_id}"
            tgt_nid = f"{t_type}_{t_id}"
            edges_dict[eid] = {"id": eid, "source": src_nid, "target": tgt_nid,
                               "label": rel.relation_type, "weight": rel.score, "type": rel.relation_type}
            if (s_type, s_id) not in added_ids:
                _add_knowledge_node_by_type(db, s_type, s_id, nodes_dict, added_ids)
            if (t_type, t_id) not in added_ids:
                _add_knowledge_node_by_type(db, t_type, t_id, nodes_dict, added_ids)

def _add_knowledge_node_by_type(db: Session, node_type: str, node_id: int, nodes_dict: dict, added_ids: set):
    key = (node_type, node_id)
    if key in added_ids:
        return
    added_ids.add(key)
    nid = f"{node_type}_{node_id}"
    if node_type == "knowledge":
        kn = db.query(Knowledge).filter(Knowledge.id == node_id).first()
        if kn:
            nodes_dict[nid] = {"id": nid, "label": kn.title[:50], "type": "knowledge", "group": "knowledge", "size": 40}
    elif node_type == "entity":
        ent = db.query(Entity).filter(Entity.id == node_id).first()
        if ent:
            nodes_dict[nid] = {"id": nid, "label": ent.name[:30], "type": "entity", "group": "entity", "size": 30}
    elif node_type == "tag":
        tag = db.query(Tag).filter(Tag.id == node_id).first()
        if tag:
            nodes_dict[nid] = {"id": nid, "label": f"#{tag.name}", "type": "tag", "group": "tag", "size": 25}

def find_path(db: Session, source_id: int, target_id: int, source_type: str = "knowledge", target_type: str = "knowledge", max_depth: int = 5):
    visited = set()
    queue = [(source_id, source_type, [f"{source_type}_{source_id}"])]
    while queue:
        nid, ntype, path = queue.pop(0)
        key = (ntype, nid)
        if key in visited:
            continue
        visited.add(key)
        if nid == target_id and ntype == target_type:
            return {"found": True, "path": path}
        if len(path) >= max_depth:
            continue
        relations = db.query(Relation).filter(
            or_(and_(Relation.source_id == nid, Relation.source_type == ntype),
                and_(Relation.target_id == nid, Relation.target_type == ntype))
        ).limit(50).all()
        for rel in relations:
            if rel.source_id == nid and rel.source_type == ntype:
                queue.append((rel.target_id, rel.target_type, path + [f"relation_{rel.id}", f"{rel.target_type}_{rel.target_id}"]))
            elif rel.target_id == nid and rel.target_type == ntype:
                queue.append((rel.source_id, rel.source_type, path + [f"relation_{rel.id}", f"{rel.source_type}_{rel.source_id}"]))
    return {"found": False, "path": []}

def get_graph_statistics(db: Session):
    kn_count = db.query(Knowledge).count()
    rel_count = db.query(Relation).count()
    entity_count = db.query(Entity).count()
    tag_count = db.query(Tag).count()
    return {"knowledge_count": kn_count, "relation_count": rel_count, "entity_count": entity_count, "tag_count": tag_count}