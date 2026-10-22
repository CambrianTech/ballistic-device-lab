"""Ranking policy must not promote a pretty but unconverged candidate."""

import gzip
import json
import unittest
from unittest.mock import patch

from ballistic_lab.experiments.coverage import CoveragePlan
from ballistic_lab.experiments.dc_refine import refine
from ballistic_lab.experiments.dc_search import initial_candidates, offspring
from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.reporting.dc_search import promoted


class DcSearchChecks(unittest.TestCase):
    def test_refinement_stops_on_gates_and_has_a_hard_cap(self):
        row = dict(candidate=dict(key="test"), energy_converged=False, phase_converged=True)
        passed = dict(row, energy_converged=True)
        with patch("ballistic_lab.experiments.dc_refine.evaluate", return_value=passed) as evaluate:
            self.assertEqual(refine(row), passed)
            evaluate.assert_called_once_with(row["candidate"], (2049,))
        with patch("ballistic_lab.experiments.dc_refine.evaluate", return_value=row) as evaluate:
            self.assertEqual(refine(row), row)
            self.assertEqual([c.args[1] for c in evaluate.call_args_list], [(2049,), (4097,)])

    def test_controls_match_archived_physical_identity(self):
        for item in initial_candidates():
            if item["key"] not in ("D00", "D14"):
                continue
            with gzip.open(
                f"results/2026-10-22-coverage/{item['key']}-nominal.json.gz", "rt", encoding="utf-8"
            ) as stream:
                archived = json.load(stream)
            self.assertEqual(
                SquareDevice(item["obstacles"], CoveragePlan().width_m, 0.3).fingerprint,
                archived["device_fingerprint"],
            )

    def test_promotion_requires_both_gates(self):
        rows = [
            dict(
                candidate=dict(key=key),
                energy_converged=energy,
                phase_converged=phase,
                phase64=dict(dc_power_w=power),
            )
            for key, energy, phase, power in (
                ("unresolved", False, True, 100),
                ("phase-fail", True, False, 90),
                ("triangle", True, True, 2),
                ("islands", True, True, 1),
            )
        ]
        self.assertEqual([r["candidate"]["key"] for r in promoted(rows)], ["triangle", "islands"])
        self.assertEqual(promoted(rows[:2]), [])

    def test_seeded_proposals_and_dc_parent_selection(self):
        items = initial_candidates()
        self.assertEqual(items, initial_candidates())
        rows = [dict(candidate=item, levels=[dict(dc_power_w=i)]) for i, item in enumerate(items)]
        children = offspring(rows)
        self.assertEqual(children, offspring(rows))
        self.assertEqual(len(children), 4)
        for child in children:
            self.assertIn("global-1", child["origin"])
