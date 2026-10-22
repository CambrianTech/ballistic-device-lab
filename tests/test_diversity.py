import unittest

from ballistic_lab.search.dc_space import WideDCPlan, proposals
from ballistic_lab.search.diversity import archive, describe


class DiversityChecks(unittest.TestCase):
    def test_union_and_symmetry(self):
        square = [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]]
        d = describe([square])
        self.assertAlmostEqual(d.blocked_fraction, 0.25)
        self.assertEqual(d.vertical_asymmetry, 0)
        self.assertEqual(d, describe([square, square]))
        self.assertEqual(d, describe([square[::-1]]))

    def test_weak_distinct_branch_survives_and_same_cell_improves(self):
        def row(key, power, polygon):
            return dict(
                candidate=dict(key=key, obstacles=[polygon]), levels=[dict(dc_power_w=power)]
            )

        small = [[0, 0], [0.1, 0], [0.1, 0.1], [0, 0.1]]
        large = [[-0.8, -0.8], [0.8, -0.8], [0.8, 0.8], [-0.8, 0.8]]
        rows = [row("weak", 1, small), row("strong", 100, large), row("better", 101, large)]
        self.assertEqual({r["candidate"]["key"] for r in archive(rows)}, {"weak", "better"})
        self.assertEqual(archive(rows), archive(rows[::-1]))

    def test_reproducible_proposals_preserve_global_exploration(self):
        plan = WideDCPlan(parent_strategy="diversity")
        first = proposals(plan, 0, 0, [])
        rows = [dict(candidate=c, levels=[dict(dc_power_w=i)]) for i, c in enumerate(first)]
        next_batch = proposals(plan, 0, 1, rows)
        self.assertEqual(next_batch, proposals(plan, 0, 1, rows[::-1]))
        self.assertEqual(sum(c["origin"] == "fresh global" for c in next_batch), 5)
