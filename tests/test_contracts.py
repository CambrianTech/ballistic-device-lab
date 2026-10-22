"""CPU-only tests for typed contracts, metric mathematics, and validation gates."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from ballistic_lab.geometry.families import FAMILIES
from ballistic_lab.metrics.angular import angular_weights, measure_response
from ballistic_lab.models import RayConfig, SearchPlan, TraceBatch
from ballistic_lab.validation.receipts import model_fingerprint, require_validation


class AnalyticBackend:
    """Synthetic angular separator with an analytically integrable response."""

    def trace(self, geometries, port, config, seed):
        rng = np.random.default_rng(seed)
        rng.uniform(-0.3, 0.3, config.count)
        sine = rng.uniform(-1, 1, config.count)
        destinations = np.where(abs(sine) < 1 / np.sqrt(3), 3, 2)
        destinations = np.tile(destinations, (len(geometries), 1))
        return TraceBatch(
            np.zeros((len(geometries), 4)),
            np.full(destinations.shape, 2.0),
            destinations,
            np.zeros_like(destinations),
        )


class ContractChecks(unittest.TestCase):
    def test_config_rejects_invalid_physics_inputs(self):
        for values in [
            dict(count=0),
            dict(specularity=1.1),
            dict(spread=-1),
            dict(mean_free_path=0),
            dict(mean_free_path=float("nan")),
        ]:
            with self.assertRaises(ValueError):
                RayConfig(**values)
        with self.assertRaises(ValueError):
            SearchPlan(validation_seeds=1)

    def test_registry_checks_parameter_dimension(self):
        with self.assertRaises(ValueError):
            FAMILIES["triangle"].build(np.array([1.0, 2.0]))

    def test_metric_matches_analytic_response(self):
        result = measure_response([[]], AnalyticBackend(), RayConfig(count=200000), 53)
        self.assertAlmostEqual(result.derivative[0], 8 / (9 * np.sqrt(3)), delta=0.004)
        self.assertEqual(result.p99_path_over_width[0], 1.0)
        self.assertAlmostEqual(float(angular_weights(53, 200000).mean()), 0.0, delta=0.004)

    def test_metric_rejects_non_equilibrium_sampling(self):
        with self.assertRaises(ValueError):
            measure_response([[]], AnalyticBackend(), RayConfig(spread=0.5), 1)

    def test_validation_gate_rejects_missing_and_stale_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with self.assertRaises(RuntimeError):
                require_validation(output)
            receipt = output / "families-validation.json"
            receipt.write_text(json.dumps(dict(model_fingerprint={})))
            with self.assertRaises(RuntimeError):
                require_validation(output)
            receipt.write_text(json.dumps(dict(model_fingerprint=model_fingerprint())))
            require_validation(output)
