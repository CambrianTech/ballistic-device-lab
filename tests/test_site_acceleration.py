import unittest

import numpy as np

from physics_layers.site_acceleration import solve_accelerated
from physics_layers.site_feedback import solve_site_feedback
from tests.test_site_feedback import fixture


class AcceleratedFeedbackTests(unittest.TestCase):
    def test_matches_direct_mesh_iteration(self):
        mesh, mapping, provider = fixture()
        a = solve_accelerated(mesh, mapping, provider, [1], [0.04, -0.02], 300, tolerance=1e-6)
        b = solve_site_feedback(mesh, mapping, provider, [1], [0.04, -0.02], 300)
        np.testing.assert_allclose(a.site_potential_v, b.site_potential_v, atol=1e-6)
        np.testing.assert_allclose(
            a.transport.electrons_per_site, b.transport.electrons_per_site, atol=1e-6
        )
        self.assertLess(a.history[-1].occupation_residual, 1e-6)
