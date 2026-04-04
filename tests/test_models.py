"""Tests for model interfaces and ensemble."""
import pytest
from models.base import BaseModel, ModelConfig, ModelRegistry
from models.ensemble import WeightedEnsemble


class DummyModel(BaseModel):
    def fit(self, X, y):
        self.is_fitted = True
        self._predictions = y

    def predict(self, X):
        return self._predictions if hasattr(self, "_predictions") else [0.0] * len(X)


class TestModelConfig:
    def test_creation(self):
        cfg = ModelConfig("test-001", "linear", "1.0.0", {"alpha": 0.1})
        assert cfg.model_id == "test-001"
        assert cfg.parameters["alpha"] == 0.1


class TestBaseModel:
    def test_not_fitted_by_default(self):
        model = DummyModel(ModelConfig("test", "dummy"))
        assert model.is_fitted is False

    def test_fit_marks_fitted(self):
        model = DummyModel(ModelConfig("test", "dummy"))
        model.fit([1, 2, 3], [10, 20, 30])
        assert model.is_fitted is True


class TestModelRegistry:
    def test_register_and_create(self):
        reg = ModelRegistry()
        reg.register("dummy", DummyModel)
        model = reg.create("dummy", ModelConfig("test", "dummy"))
        assert isinstance(model, DummyModel)

    def test_missing_model(self):
        reg = ModelRegistry()
        with pytest.raises(KeyError):
            reg.create("missing", ModelConfig("test", "missing"))

    def test_list_models(self):
        reg = ModelRegistry()
        reg.register("dummy", DummyModel)
        reg.register("dummy2", DummyModel)
        assert len(reg.list_models()) == 2


class TestWeightedEnsemble:
    def test_ensemble_prediction(self):
        cfg = ModelConfig("ensemble", "weighted_ensemble")
        ensemble = WeightedEnsemble(cfg)
        m1 = DummyModel(ModelConfig("m1", "dummy"))
        m2 = DummyModel(ModelConfig("m2", "dummy"))
        ensemble.add_model(m1)
        ensemble.add_model(m2)
        ensemble.fit([1, 2, 3], [10, 20, 30])
        preds = ensemble.predict([1, 2, 3])
        assert len(preds) == 3

    def test_not_fitted_raises(self):
        cfg = ModelConfig("ensemble", "weighted_ensemble")
        ensemble = WeightedEnsemble(cfg)
        with pytest.raises(RuntimeError):
            ensemble.predict([1, 2])
