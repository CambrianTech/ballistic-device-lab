import unittest

import numpy as np

from physics_layers.site_acceleration import solve_accelerated
from physics_layers.site_feedback import solve_site_feedback
from tests.test_site_feedback import fixture


class AcceleratedFeedbackTests(unittest.TestCase):
    def test_broyden_matches_independent_mesh_iteration(self):
        mesh, mapping, provider = fixture()
        for mus in ([0.04, -0.02], [-0.04, 0.02], [0, 0]):
            with self.subTest(mus=mus):
                result = solve_accelerated(
                    mesh, mapping, provider, [1], mus, 300, method="broyden1"
                )
                direct = solve_site_feedback(mesh, mapping, provider, [1], mus, 300)
                np.testing.assert_allclose(
                    result.site_potential_v, direct.site_potential_v, atol=1e-6
                )
                np.testing.assert_allclose(
                    result.transport.electrons_per_site,
                    direct.transport.electrons_per_site,
                    atol=1e-6,
                )
                self.assertLess(result.history[-1].potential_residual_v, 1e-6)
                self.assertLess(result.history[-1].occupation_residual, 1e-6)

    def test_rejects_unknown_method(self):
        mesh, mapping, provider = fixture()
        with self.assertRaises(ValueError):
            solve_accelerated(mesh, mapping, provider, [1], [0, 0], 300, method="typo")

    def test_warm_start_matches_cold_at_changed_bias(self):
        mesh, mapping, provider = fixture()
        previous = solve_accelerated(mesh, mapping, provider, [1], [0.04, -0.02], 300)
        initial = np.array(previous.site_potential_v)
        saved = initial.copy()
        warm = solve_accelerated(
            mesh,
            mapping,
            provider,
            [1],
            [0.045, -0.025],
            300,
            initial_potential_v=initial,
        )
        cold = solve_accelerated(mesh, mapping, provider, [1], [0.045, -0.025], 300)
        np.testing.assert_array_equal(initial, saved)
        np.testing.assert_allclose(warm.site_potential_v, cold.site_potential_v, atol=1e-6)
        np.testing.assert_allclose(
            warm.transport.electrons_per_site, cold.transport.electrons_per_site, atol=1e-6
        )
        self.assertLess(warm.history[-1].potential_residual_v, 1e-6)
        self.assertLess(warm.history[-1].occupation_residual, 1e-6)

    def test_rejects_invalid_initial_potential(self):
        mesh, mapping, provider = fixture()
        for initial in ([float("nan")], [float("inf")], [], [[0]], [0, 0]):
            with self.subTest(initial=initial), self.assertRaises(ValueError):
                solve_accelerated(
                    mesh, mapping, provider, [1], [0, 0], 300, initial_potential_v=initial
                )

    def test_matches_direct_mesh_iteration(self):
        mesh, mapping, provider = fixture()
        a = solve_accelerated(mesh, mapping, provider, [1], [0.04, -0.02], 300, tolerance=1e-6)
        b = solve_site_feedback(mesh, mapping, provider, [1], [0.04, -0.02], 300)
        np.testing.assert_allclose(a.site_potential_v, b.site_potential_v, atol=1e-6)
        np.testing.assert_allclose(
            a.transport.electrons_per_site, b.transport.electrons_per_site, atol=1e-6
        )
        self.assertLess(a.history[-1].occupation_residual, 1e-6)
