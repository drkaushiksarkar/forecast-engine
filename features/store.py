"""Feature store for ML training: versioned feature computation, storage, and retrieval."""
from __future__ import annotations
import hashlib, json, time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

@dataclass
class FeatureDefinition:
    name: str
    description: str
    compute_fn: Callable
    dependencies: list[str] = field(default_factory=list)
    version: str = "1.0"
    ttl_seconds: int = 3600
    tags: list[str] = field(default_factory=list)

@dataclass
class FeatureValue:
    name: str
    value: Any
    version: str
    computed_at: str
    entity_id: str
    expires_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

@dataclass
class FeatureVector:
    entity_id: str
    features: dict[str, Any]
    computed_at: str
    version_hash: str

class FeatureStore:
    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self._definitions: dict[str, FeatureDefinition] = {}
        self._cache: dict[str, FeatureValue] = {}
        self._storage_dir = storage_dir
        self._compute_count = 0
        self._cache_hits = 0

    def register(self, definition: FeatureDefinition) -> None:
        self._definitions[definition.name] = definition

    def compute(self, name: str, entity_id: str, context: Optional[dict] = None) -> FeatureValue:
        defn = self._definitions.get(name)
        if defn is None: raise KeyError(f"Feature '{name}' not registered")
        cache_key = f"{name}:{entity_id}:{defn.version}"
        cached = self._cache.get(cache_key)
        if cached and not cached.is_expired:
            self._cache_hits += 1; return cached
        dep_values = {}
        for dep_name in defn.dependencies:
            dep_val = self.compute(dep_name, entity_id, context)
            dep_values[dep_name] = dep_val.value
        self._compute_count += 1
        value = defn.compute_fn(entity_id, dep_values, context or {})
        fv = FeatureValue(name=name, value=value, version=defn.version,
            computed_at=datetime.utcnow().isoformat(), entity_id=entity_id,
            expires_at=time.time() + defn.ttl_seconds)
        self._cache[cache_key] = fv
        return fv

    def get_vector(self, entity_id: str, feature_names: Sequence[str],
                   context: Optional[dict] = None) -> FeatureVector:
        features = {}
        for name in feature_names:
            fv = self.compute(name, entity_id, context)
            features[name] = fv.value
        version_str = ":".join(f"{n}={self._definitions[n].version}" for n in sorted(feature_names))
        version_hash = hashlib.md5(version_str.encode()).hexdigest()[:8]
        return FeatureVector(entity_id=entity_id, features=features,
            computed_at=datetime.utcnow().isoformat(), version_hash=version_hash)

    def invalidate(self, name: str, entity_id: Optional[str] = None) -> int:
        keys_to_remove = []
        for key in self._cache:
            if key.startswith(f"{name}:"):
                if entity_id is None or f":{entity_id}:" in key:
                    keys_to_remove.append(key)
        for key in keys_to_remove: del self._cache[key]
        return len(keys_to_remove)

    @property
    def stats(self) -> dict[str, Any]:
        total = self._compute_count + self._cache_hits
        return {"registered_features": len(self._definitions), "cached_values": len(self._cache),
            "compute_count": self._compute_count, "cache_hits": self._cache_hits,
            "hit_rate": self._cache_hits / total if total > 0 else 0.0}
