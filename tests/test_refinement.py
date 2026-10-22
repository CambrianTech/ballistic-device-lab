"""Search guardrails: bounded proposals, equal cost, and incumbent preservation."""

import unittest
from unittest.mock import patch

import numpy as np

from ballistic_lab.geometry.families import FAMILIES
from ballistic_lab.models import AngularResponse, Candidate
from ballistic_lab.search.refinement import RefinementPlan, proposals, refine


class RefinementChecks(unittest.TestCase):
    def test_proposals_at_boundary_remain_inside_without_clipping_atoms(self):
        for family in ("triangle", "beveled"):
            bounds = np.asarray(FAMILIES[family].bounds)
            for center in (bounds[:, 0], bounds[:, 1]):
                values = proposals(family, center, np.random.default_rng(19), 1000, 0.1)
                self.assertTrue(np.all(values >= bounds[:, 0]))
                self.assertTrue(np.all(values <= bounds[:, 1]))
                self.assertFalse(np.any(values == bounds[:, 0]))
                self.assertFalse(np.any(values == bounds[:, 1]))

    def test_equal_budgets_and_anchor_survives_worse_proposals(self):
        anchor = Candidate("control", "triangle", (1.0, 0.5, 0.0, 0.0))
        plan = RefinementPlan(rounds=2, batch=8, repeats=1, rays=16)
        calls = []

        def objective(geometries, backend, config, seed):
            calls.append((len(geometries), seed))
            # First candidate in each arm's first batch is the anchor; all
            # subsequent proposals are worse, so neither arm may lose it.
            scores = np.zeros(len(geometries))
            if len(calls) in (1, 3):
                scores[0] = 1.0
            return AngularResponse(scores, np.ones(len(geometries)))

        with patch("ballistic_lab.search.refinement.measure_response", objective):
            finalists, records = refine([anchor], plan, backend=None)
        self.assertEqual([c.parameters for c in finalists], [anchor.parameters] * 2)
        for method in ("global", "mutation"):
            self.assertEqual(sum(len(r["x"]) for r in records if r["method"] == method), 16)
        self.assertEqual(len(set(seed for _, seed in calls)), 1)


if __name__ == "__main__":
    unittest.main()
