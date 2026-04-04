"""Knowledge graph builder with entity resolution and relation extraction."""
from __future__ import annotations
import hashlib, json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Sequence

@dataclass
class Entity:
    entity_id: str
    entity_type: str
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    source: str = ""
    confidence: float = 1.0

@dataclass
class Relation:
    source_id: str
    target_id: str
    relation_type: str
    attributes: dict[str, Any] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    confidence: float = 1.0
    source: str = ""

@dataclass
class GraphStats:
    entity_count: int
    relation_count: int
    entity_types: dict[str, int]
    relation_types: dict[str, int]
    avg_degree: float
    connected_components: int

class KnowledgeGraph:
    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._relations: list[Relation] = []
        self._adjacency: dict[str, list[int]] = defaultdict(list)
        self._reverse_adj: dict[str, list[int]] = defaultdict(list)
        self._name_index: dict[str, list[str]] = defaultdict(list)

    def add_entity(self, entity: Entity) -> str:
        self._entities[entity.entity_id] = entity
        normalized = entity.name.lower().strip()
        self._name_index[normalized].append(entity.entity_id)
        for alias in entity.aliases:
            self._name_index[alias.lower().strip()].append(entity.entity_id)
        return entity.entity_id

    def add_relation(self, relation: Relation) -> int:
        if relation.source_id not in self._entities or relation.target_id not in self._entities:
            raise ValueError("Both source and target entities must exist")
        idx = len(self._relations)
        self._relations.append(relation)
        self._adjacency[relation.source_id].append(idx)
        self._reverse_adj[relation.target_id].append(idx)
        return idx

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self._entities.get(entity_id)

    def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 10) -> list[Entity]:
        q = query.lower().strip()
        candidates = set()
        for name, ids in self._name_index.items():
            if q in name: candidates.update(ids)
        results = [self._entities[eid] for eid in candidates if eid in self._entities]
        if entity_type: results = [e for e in results if e.entity_type == entity_type]
        results.sort(key=lambda e: e.confidence, reverse=True)
        return results[:limit]

    def get_neighbors(self, entity_id: str, relation_type: Optional[str] = None,
                      direction: str = "outgoing") -> list[tuple[Entity, Relation]]:
        results = []
        if direction in ("outgoing", "both"):
            for idx in self._adjacency.get(entity_id, []):
                rel = self._relations[idx]
                if relation_type and rel.relation_type != relation_type: continue
                target = self._entities.get(rel.target_id)
                if target: results.append((target, rel))
        if direction in ("incoming", "both"):
            for idx in self._reverse_adj.get(entity_id, []):
                rel = self._relations[idx]
                if relation_type and rel.relation_type != relation_type: continue
                source = self._entities.get(rel.source_id)
                if source: results.append((source, rel))
        return results

    def shortest_path(self, source_id: str, target_id: str, max_depth: int = 6) -> Optional[list[str]]:
        if source_id not in self._entities or target_id not in self._entities: return None
        if source_id == target_id: return [source_id]
        from collections import deque
        visited = {source_id}
        queue = deque([(source_id, [source_id])])
        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth: continue
            for idx in self._adjacency.get(current, []):
                rel = self._relations[idx]
                neighbor = rel.target_id
                if neighbor == target_id: return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor); queue.append((neighbor, path + [neighbor]))
        return None

    def merge_entities(self, keep_id: str, merge_id: str) -> None:
        keep = self._entities.get(keep_id)
        merge = self._entities.get(merge_id)
        if not keep or not merge: raise ValueError("Both entities must exist")
        keep.aliases.extend([merge.name] + merge.aliases)
        keep.aliases = list(set(keep.aliases))
        for k, v in merge.attributes.items():
            if k not in keep.attributes: keep.attributes[k] = v
        for rel in self._relations:
            if rel.source_id == merge_id: rel.source_id = keep_id
            if rel.target_id == merge_id: rel.target_id = keep_id
        for name, ids in self._name_index.items():
            self._name_index[name] = [keep_id if eid == merge_id else eid for eid in ids]
        del self._entities[merge_id]

    def get_stats(self) -> GraphStats:
        entity_types = defaultdict(int)
        for e in self._entities.values(): entity_types[e.entity_type] += 1
        relation_types = defaultdict(int)
        for r in self._relations: relation_types[r.relation_type] += 1
        degrees = defaultdict(int)
        for r in self._relations: degrees[r.source_id] += 1; degrees[r.target_id] += 1
        avg_deg = sum(degrees.values()) / max(len(self._entities), 1)
        visited = set(); components = 0
        for eid in self._entities:
            if eid not in visited:
                components += 1; stack = [eid]
                while stack:
                    node = stack.pop()
                    if node in visited: continue
                    visited.add(node)
                    for idx in self._adjacency.get(node, []):
                        stack.append(self._relations[idx].target_id)
                    for idx in self._reverse_adj.get(node, []):
                        stack.append(self._relations[idx].source_id)
        return GraphStats(entity_count=len(self._entities), relation_count=len(self._relations),
            entity_types=dict(entity_types), relation_types=dict(relation_types),
            avg_degree=round(avg_deg, 2), connected_components=components)

    def export_triples(self) -> list[tuple[str, str, str]]:
        return [(self._entities[r.source_id].name, r.relation_type, self._entities[r.target_id].name)
                for r in self._relations if r.source_id in self._entities and r.target_id in self._entities]
