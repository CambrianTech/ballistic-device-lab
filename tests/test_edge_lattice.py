"""Quantum tests run in the isolated Kwant interpreter."""

import importlib.util
import unittest

import numpy as np


@unittest.skipUnless(importlib.util.find_spec("kwant"), "Requires Kwant")
class EdgeTests(unittest.TestCase):
    def test_induced_graph_and_transport(self):
        from ballistic_lab.pipeline.contracts import SquareDevice
        from ballistic_lab.transport.quantum import LatticeRequest, build_system, solve_spectrum
        from edge_lab.lattice import VacancySystem, edge_sites

        polygons = (((-0.5, 0.35), (0.5, 0.35), (0, -0.35)),)
        original = build_system(SquareDevice(polygons, 30 * 0.246e-9), LatticeRequest((0.9,)))
        edges = edge_sites(original, polygons, 15)
        self.assertGreater(len(edges), 3)
        unchanged = VacancySystem(original, ())
        a = solve_spectrum(original, LatticeRequest((0.9,)))[0]
        b = solve_spectrum(unchanged, LatticeRequest((0.9,)))[0]
        np.testing.assert_allclose(a["transmission"], b["transmission"], atol=1e-9)
        changed = VacancySystem(original, edges[:1])
        self.assertEqual(len(changed.sites), len(original.sites) - 1)
        h = original.hamiltonian_submatrix()
        np.testing.assert_array_equal(
            changed.hamiltonian_submatrix(), h[np.ix_(changed.indices, changed.indices)]
        )
        self.assertEqual(changed.components(), 1)
        solve_spectrum(changed, LatticeRequest((0.9,)))
        with self.assertRaises(ValueError):
            VacancySystem(original, [original.lead_interfaces[0][0]])


if __name__ == "__main__":
    unittest.main()
