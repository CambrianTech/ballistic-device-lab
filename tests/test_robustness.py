import unittest

from ballistic_lab.reporting.robustness import compare


class RobustnessTests(unittest.TestCase):
    def test_only_matched_converged_positive_reference_cases_enter(self):
        def row(power, passed=True):
            return dict(dc_power_w=power, energy_converged=passed, phase_converged=True)

        a = {1: row(8), 2: row(1), 3: row(100, False), 4: row(1), 5: row(999)}
        b = {1: row(2), 2: row(2), 3: row(2), 4: row(0)}
        self.assertEqual(
            compare(a, b), dict(matched=2, higher=1, median_ratio=2.25, worst_ratio=0.5)
        )

    def test_missing_results_remain_pending(self):
        self.assertIsNone(compare({}, {})["median_ratio"])
