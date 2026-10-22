import unittest

import numpy as np

from ballistic_lab.geometry.basic import cross
from ballistic_lab.geometry.families import FAMILIES, geometry, sample
from ballistic_lab.transport.cpu import trace


class GeometryChecks(unittest.TestCase):
    def test_generated_polygons_have_no_self_crossings(self):
        for family in FAMILIES:
            for x in sample(family, np.random.default_rng(19), 128):
                for p in geometry(family, x):
                    self.assertTrue(np.all(abs(p) <= 1))
                    edges = np.roll(p, -1, axis=0) - p
                    self.assertTrue(np.all(np.linalg.norm(edges, axis=1) > 1e-8))
                    for i in range(len(p)):
                        for j in range(i + 1, len(p)):
                            if j == i + 1 or (i == 0 and j == len(p) - 1):
                                continue
                            den = cross(edges[i], edges[j])
                            if abs(den) < 1e-12:
                                continue
                            delta = p[j] - p[i]
                            t = cross(delta, edges[j]) / den
                            u = cross(delta, edges[i]) / den
                            self.assertFalse(0 < t < 1 and 0 < u < 1, (family, x, p))

    def test_cpu_new_topologies_conserve_particles(self):
        for family in FAMILIES:
            x = sample(family, np.random.default_rng(20), 1)[0]
            for port in range(4):
                probabilities, lengths, _ = trace(
                    geometry(family, x), port, n=1024, mfp=2, specularity=0.8
                )
                self.assertAlmostEqual(float(probabilities.sum()), 1.0)
                self.assertTrue(np.isfinite(lengths).all())
