"""Topology validity and budget accounting for population search."""

import unittest
from unittest.mock import patch

import numpy as np

from ballistic_lab.geometry.families import FAMILIES, geometry
from ballistic_lab.models import AngularResponse
from ballistic_lab.search.discovery import DiscoveryPlan, breed, discover


class DiscoveryChecks(unittest.TestCase):
    def test_separated_islands_never_overlap(self):
        for values in FAMILIES["islands"].sample(np.random.default_rng(42), 1000):
            left, right = geometry("islands", values)
            self.assertLess(left[:, 0].max(), right[:, 0].min())

    def test_population_keeps_bounds_after_large_mutations(self):
        for family in ("profile", "radial", "islands"):
            rng = np.random.default_rng(43)
            bounds = np.asarray(FAMILIES[family].bounds)
            parents = FAMILIES[family].sample(rng, 32)
            children = breed(parents, np.arange(32), bounds, rng, 1000, 5.0)
            self.assertTrue(np.isfinite(children).all())
            self.assertTrue(np.all(children >= bounds[:, 0]))
            self.assertTrue(np.all(children <= bounds[:, 1]))

    def test_equal_cost_and_two_seed_training(self):
        calls = []

        def objective(polygons, backend, config, seed):
            calls.append((len(polygons), seed))
            return AngularResponse(np.arange(len(polygons), dtype=float), np.ones(len(polygons)))

        plan = DiscoveryPlan(families=("profile",), rounds=3, batch=8, repeats=1, rays=16)
        with patch("ballistic_lab.search.discovery.measure_response", objective):
            finalists, records = discover(plan, backend=None)
        self.assertEqual(len(finalists), 2)
        self.assertEqual(len(calls), 12)
        self.assertEqual(len(set(seed for _, seed in calls)), 2)
        for method in ("random", "population"):
            self.assertEqual(sum(len(r["x"]) for r in records if r["method"] == method), 24)


if __name__ == "__main__":
    unittest.main()
