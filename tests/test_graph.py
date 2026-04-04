"""Tests for knowledge graph builder."""
import pytest

class TestKnowledgeGraph:
    def _make_graph(self):
        from graph.builder import KnowledgeGraph, Entity, Relation
        g = KnowledgeGraph()
        g.add_entity(Entity(entity_id="e1", entity_type="disease", name="Malaria"))
        g.add_entity(Entity(entity_id="e2", entity_type="vector", name="Anopheles"))
        g.add_entity(Entity(entity_id="e3", entity_type="country", name="Bangladesh"))
        g.add_relation(Relation(source_id="e2", target_id="e1", relation_type="transmits"))
        g.add_relation(Relation(source_id="e1", target_id="e3", relation_type="endemic_in"))
        return g
    def test_add_and_get(self):
        g = self._make_graph()
        e = g.get_entity("e1"); assert e is not None; assert e.name == "Malaria"
    def test_search(self):
        g = self._make_graph()
        results = g.search_entities("malaria"); assert len(results) == 1
    def test_neighbors(self):
        g = self._make_graph()
        neighbors = g.get_neighbors("e1", direction="both")
        assert len(neighbors) == 2
    def test_shortest_path(self):
        g = self._make_graph()
        path = g.shortest_path("e2", "e3")
        assert path == ["e2", "e1", "e3"]
    def test_merge_entities(self):
        from graph.builder import KnowledgeGraph, Entity
        g = KnowledgeGraph()
        g.add_entity(Entity(entity_id="a", entity_type="disease", name="Malaria"))
        g.add_entity(Entity(entity_id="b", entity_type="disease", name="Plasmodium falciparum malaria"))
        g.merge_entities("a", "b")
        assert g.get_entity("b") is None
        assert "Plasmodium falciparum malaria" in g.get_entity("a").aliases
    def test_stats(self):
        g = self._make_graph()
        stats = g.get_stats()
        assert stats.entity_count == 3; assert stats.relation_count == 2
    def test_export_triples(self):
        g = self._make_graph()
        triples = g.export_triples()
        assert ("Anopheles", "transmits", "Malaria") in triples
