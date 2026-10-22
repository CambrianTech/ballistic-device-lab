import unittest

import numpy as np

from physics_layers.noise import KB, equilibrium_output_noise


def resistors(edges):
    matrix = np.zeros((4, 4))
    for a, b, resistance in edges:
        d = np.eye(4)[a] - np.eye(4)[b]
        matrix += np.outer(d, d) / resistance
    return matrix


class NoiseTests(unittest.TestCase):
    def test_series_paths_shunted_by_warm_load(self):
        # Two grounded 1k legs form 2k differential resistance, shunted by 10k.
        g = resistors([(0, 2, 1000), (1, 3, 1000)])
        result = equilibrium_output_noise(g, 300, 10000)
        equivalent = 1 / (1 / 2000 + 1 / 10000)
        self.assertAlmostEqual(result.equivalent_resistance_ohm, equivalent)
        self.assertAlmostEqual(result.total_v2_per_hz / (4 * KB * 300 * equivalent), 1)
        self.assertGreater(result.load_v2_per_hz, 0)
        doubled = equilibrium_output_noise(g, 600, 10000)
        self.assertAlmostEqual(doubled.total_v2_per_hz / result.total_v2_per_hz, 2)

    def test_correlations_and_port_swap(self):
        g = resistors([(0, 2, 1000), (1, 3, 2000), (2, 3, 500)])
        a = equilibrium_output_noise(g, 300, 10000)
        order = [0, 1, 3, 2]
        b = equilibrium_output_noise(g[np.ix_(order, order)], 300, 10000)
        self.assertAlmostEqual(a.total_v2_per_hz / b.total_v2_per_hz, 1)
        expected = 1 / (1 / 3000 + 1 / 500 + 1 / 10000)
        self.assertAlmostEqual(a.total_v2_per_hz / (4 * KB * 300 * expected), 1)

    def test_invalid_and_floating_networks(self):
        for g in (np.eye(4), resistors([(2, 3, 1000)]), -resistors([(0, 2, 1000), (1, 3, 1000)])):
            with self.assertRaises(ValueError):
                equilibrium_output_noise(g, 300, 10000)
