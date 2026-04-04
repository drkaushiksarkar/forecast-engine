"""Tests for feature store."""
import pytest

class TestFeatureStore:
    def test_register_and_compute(self):
        from features.store import FeatureStore, FeatureDefinition
        store = FeatureStore()
        store.register(FeatureDefinition(name="age", description="User age",
            compute_fn=lambda eid, deps, ctx: 30))
        fv = store.compute("age", "user-1")
        assert fv.value == 30; assert fv.name == "age"
    def test_cache_hit(self):
        from features.store import FeatureStore, FeatureDefinition
        store = FeatureStore(); calls = [0]
        def compute(eid, deps, ctx): calls[0] += 1; return 42
        store.register(FeatureDefinition(name="x", description="test", compute_fn=compute))
        store.compute("x", "e1"); store.compute("x", "e1")
        assert calls[0] == 1; assert store.stats["cache_hits"] == 1
    def test_dependencies(self):
        from features.store import FeatureStore, FeatureDefinition
        store = FeatureStore()
        store.register(FeatureDefinition(name="base", description="base val",
            compute_fn=lambda eid, deps, ctx: 10))
        store.register(FeatureDefinition(name="derived", description="derived",
            compute_fn=lambda eid, deps, ctx: deps["base"] * 2, dependencies=["base"]))
        fv = store.compute("derived", "e1")
        assert fv.value == 20
    def test_get_vector(self):
        from features.store import FeatureStore, FeatureDefinition
        store = FeatureStore()
        store.register(FeatureDefinition(name="a", description="", compute_fn=lambda e, d, c: 1))
        store.register(FeatureDefinition(name="b", description="", compute_fn=lambda e, d, c: 2))
        vec = store.get_vector("e1", ["a", "b"])
        assert vec.features == {"a": 1, "b": 2}
    def test_invalidate(self):
        from features.store import FeatureStore, FeatureDefinition
        store = FeatureStore()
        store.register(FeatureDefinition(name="x", description="", compute_fn=lambda e, d, c: 1))
        store.compute("x", "e1"); count = store.invalidate("x")
        assert count == 1; assert store.stats["cached_values"] == 0
    def test_missing_feature_raises(self):
        from features.store import FeatureStore
        store = FeatureStore()
        with pytest.raises(KeyError): store.compute("nonexistent", "e1")
