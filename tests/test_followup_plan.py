import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from followup_lab.plan import identity, leader, passes
from followup_lab.worker import evaluate


class FollowupPlanTests(unittest.TestCase):
    def test_geometry_dedup_ignores_arm_and_name(self):
        a = dict(key="elite-a", obstacles=[[[0, 0], [1, 0], [0, 1]]])
        b = dict(a, key="random-a")
        self.assertEqual(identity(a), identity(b))
        self.assertNotEqual(identity(a), identity(dict(a, obstacles=[])))

    def test_unconverged_score_cannot_promote(self):
        rows = [
            dict(
                candidate=dict(key="bad"),
                energy_converged=False,
                phase_converged=True,
                phase64=dict(dc_power_w=100),
            ),
            dict(
                candidate=dict(key="good"),
                energy_converged=True,
                phase_converged=True,
                phase64=dict(dc_power_w=1),
            ),
        ]
        self.assertEqual(leader(dict(histories=dict(elite=rows)))["key"], "good")

    def test_two_successive_refinements_required(self):
        self.assertFalse(passes([1e-5, 1e-5]))
        self.assertFalse(passes([2e-5, 1e-5, 1e-5]))
        self.assertTrue(passes([1e-5, 1.001e-5, 1.002e-5]))

    def test_case_matrix_checkpoint_and_resume(self):
        candidate = dict(key="test-uncached", obstacles=[])

        def spectrum(system, request):
            return [dict(energy_ev=e) for e in request.energies_ev]

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with (
                patch("followup_lab.worker.build_system", return_value=None),
                patch("followup_lab.worker.solve_spectrum", side_effect=spectrum) as solver,
                patch(
                    "followup_lab.worker.cycle",
                    return_value=dict(dc_v=1e-6, dc_power_w=1e-16, max_kcl_a=0),
                ),
            ):
                evaluate(candidate, ("wide-contact", 0.4, (0, 0)), root)
                calls = solver.call_count
                evaluate(candidate, ("wide-contact", 0.4, (0, 0)), root)
                self.assertEqual(solver.call_count, calls)
            result = json.loads((root / identity(candidate) / "wide-contact.json").read_text())
            self.assertEqual([r["count"] for r in result["levels"]], [257, 513, 1025])
            self.assertEqual(len(result["results"]), 9)
            self.assertTrue(
                all(r["energy_converged"] and r["phase_converged"] for r in result["results"])
            )


if __name__ == "__main__":
    unittest.main()
