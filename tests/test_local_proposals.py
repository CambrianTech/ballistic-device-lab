import unittest

import numpy as np

from ballistic_lab.geometry.families import FAMILIES, geometry
from local_lab.worker import proposals


class LocalProposalTests(unittest.TestCase):
    def test_reproducible_bounded_parent_preserving(self):
        bounds = np.array(FAMILIES["profile"].bounds)
        values = bounds[:, 1].copy()
        parent = dict(key="parent", family="profile", parameters=values.tolist())
        children = proposals(parent)
        self.assertEqual(children, proposals(parent))
        self.assertEqual(len(children), 24)
        self.assertEqual(len({c["key"] for c in children}), 24)
        np.testing.assert_array_equal(parent["parameters"], values)
        for child in children:
            p = np.array(child["parameters"])
            self.assertTrue(np.all(p >= bounds[:, 0]) and np.all(p <= bounds[:, 1]))
            self.assertFalse(np.array_equal(p, values))
            self.assertEqual(child["parent_key"], "parent")
            self.assertEqual(child["obstacles"], [p.tolist() for p in geometry("profile", p)])
        self.assertNotEqual(children, proposals(parent, 123))
