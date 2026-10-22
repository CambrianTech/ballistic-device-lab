"""Family coverage and exploration persist independently of incumbent shape."""

import unittest

import numpy as np

from ballistic_lab.geometry.families import FAMILIES
from ballistic_lab.search.dc_space import WideDCPlan, proposals


class WideSpaceChecks(unittest.TestCase):
    def test_seeded_coverage_and_fresh_injection(self):
        plan = WideDCPlan()
        first = proposals(plan, 0, 0, [])
        self.assertEqual(first, proposals(plan, 0, 0, []))
        self.assertEqual(len(first), 20)
        self.assertIn("beveled", {r["family"] for r in first})
        history = [
            dict(candidate=r, levels=[dict(dc_power_w=float(i))]) for i, r in enumerate(first)
        ]
        second = proposals(plan, 0, 1, history)
        self.assertEqual(len(second), 10)
        self.assertEqual(sum(r["origin"] == "fresh global" for r in second), 5)
        for row in first + second:
            bounds = np.array(FAMILIES[row["family"]].bounds)
            values = np.array(row["parameters"])
            self.assertTrue(np.all(values >= bounds[:, 0]) and np.all(values <= bounds[:, 1]))
        self.assertNotEqual(first, proposals(plan, 1, 0, []))

    def test_mutation_parents_maximize_power_not_signed_voltage(self):
        plan = WideDCPlan(families=("triangle",))
        candidates = proposals(plan, 0, 0, [])
        history = [
            dict(candidate=c, levels=[dict(dc_power_w=p, dc_v=v)])
            for c, p, v in zip(candidates, (1, 100, 81, 4), (1, -10, 9, -2), strict=True)
        ]
        allowed = {f"mutation of {candidates[i]['key']}" for i in (1, 2)}
        for round_index in range(1, 20):
            mutation = proposals(plan, 0, round_index, history)[1]
            self.assertIn(mutation["origin"], allowed)
