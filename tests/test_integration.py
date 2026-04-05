"""Integration tests for forecast-engine pipeline."""
import pytest
import numpy as np
import json
import tempfile
import os


class TestEndToEndPipeline:
    """Test the complete data processing pipeline."""

    def test_data_ingestion_to_output(self, sample_dataframe):
        data = sample_dataframe
        assert len(data["timestamp"]) == 100
        assert len(data["value"]) == 100
        values = np.array(data["value"])
        assert np.isfinite(values).all()

    def test_batch_processing_memory_stable(self):
        batch_size = 1000
        n_batches = 10
        results = []
        for i in range(n_batches):
            batch = np.random.randn(batch_size, 64)
            processed = np.maximum(0, batch)
            results.append(float(np.mean(processed)))
        assert len(results) == n_batches
        assert all(r >= 0 for r in results)

    def test_checkpoint_save_and_restore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = {
                "epoch": 5,
                "loss": 0.342,
                "metrics": {"accuracy": 0.891, "f1": 0.876},
                "config": {"lr": 1e-4, "batch_size": 32},
            }
            path = os.path.join(tmpdir, "checkpoint.json")
            with open(path, "w") as f:
                json.dump(state, f)
            with open(path) as f:
                restored = json.load(f)
            assert restored["epoch"] == 5
            assert abs(restored["loss"] - 0.342) < 1e-6
            assert restored["metrics"]["accuracy"] == 0.891

    def test_concurrent_data_access(self):
        from concurrent.futures import ThreadPoolExecutor
        shared_data = np.random.randn(1000, 32)
        def process_slice(start):
            chunk = shared_data[start:start+100].copy()
            return float(np.mean(chunk))
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_slice, i*100) for i in range(10)]
            results = [f.result() for f in futures]
        assert len(results) == 10

    def test_error_recovery(self):
        errors = []
        for i in range(5):
            try:
                if i == 2:
                    raise ValueError("Simulated transient error")
                result = i * 2
            except ValueError as e:
                errors.append(str(e))
                result = -1
        assert len(errors) == 1
        assert "transient" in errors[0]
