import unittest

import numpy as np

from physics_layers.electrostatics import EPSILON_0
from physics_layers.poisson2d import Poisson2DRequest, Poisson2DStage


def request(n, offset=0.0):
    x = np.linspace(0, 100e-9, n)
    y = np.linspace(0, 70e-9, n)
    xx, yy = np.meshgrid(x, y)
    exact = np.sin(np.pi * xx / x[-1]) * np.sin(np.pi * yy / y[-1])
    rho = EPSILON_0 * 4 * np.pi**2 * (1 / x[-1] ** 2 + 1 / y[-1] ** 2) * exact
    fixed = exact + offset
    fixed[1:-1, 1:-1] = np.nan
    return Poisson2DRequest(
        x[1], y[1], np.full((n, n - 1), 4), np.full((n - 1, n), 4), rho, fixed
    ), exact + offset


class Poisson2DTests(unittest.TestCase):
    def test_layered_dielectric_displacement_continuity(self):
        eps = np.r_[np.full(10, 2.0), np.full(10, 8.0)]
        profile = np.r_[0, np.cumsum(1 / eps)] / np.sum(1 / eps)
        fixed = np.tile(profile, (9, 1))
        fixed[1:-1, 1:-1] = np.nan
        req = Poisson2DRequest(
            1e-9, 2e-9, np.tile(eps, (9, 1)), np.ones((8, 21)), np.zeros((9, 21)), fixed
        )
        result = Poisson2DStage().evaluate(req)
        np.testing.assert_allclose(result.potential_v, np.tile(profile, (9, 1)), atol=1e-13)
        displacement = np.array(result.electric_field_x_v_m) * eps * EPSILON_0
        np.testing.assert_allclose(displacement, displacement[0, 0], rtol=1e-12)

    def test_manufactured_solution_second_order_convergence(self):
        errors = []
        for n in (17, 33, 65):
            req, exact = request(n)
            result = Poisson2DStage().evaluate(req)
            errors.append(np.max(abs(np.array(result.potential_v) - exact)))
            self.assertLess(result.residual_c_m3 / np.max(req.charge_density_c_m3), 1e-10)
        self.assertGreater(errors[0] / errors[1], 3.9)
        self.assertGreater(errors[1] / errors[2], 3.9)

    def test_gauge_shift_leaves_fields_unchanged(self):
        a = Poisson2DStage().evaluate(request(17)[0])
        b = Poisson2DStage().evaluate(request(17, 0.37)[0])
        np.testing.assert_allclose(np.array(b.potential_v) - a.potential_v, 0.37, atol=1e-13)
        np.testing.assert_allclose(b.electric_field_x_v_m, a.electric_field_x_v_m, atol=1e-6)

    def test_internal_electrode_and_maximum_principle(self):
        fixed = np.zeros((21, 21))
        fixed[1:-1, 1:-1] = np.nan
        fixed[8:13, 8:13] = 1.0
        req = Poisson2DRequest(
            1e-9, 1e-9, np.ones((21, 20)), np.ones((20, 21)), np.zeros((21, 21)), fixed
        )
        fixed[8:13, 8:13] = 2.0  # Request owns an immutable snapshot.
        phi = np.array(Poisson2DStage().evaluate(req).potential_v)
        self.assertEqual(phi[10, 10], 1.0)
        self.assertGreaterEqual(phi.min(), 0)
        self.assertLessEqual(phi.max(), 1)
        np.testing.assert_allclose(phi, phi[::-1], atol=1e-14)

    def test_missing_outer_boundary_rejected(self):
        req, _ = request(5)
        fixed = np.array(req.fixed_potential_v)
        fixed[0, 2] = np.nan
        with self.assertRaises(ValueError):
            Poisson2DRequest(
                req.spacing_x_m,
                req.spacing_y_m,
                req.relative_permittivity_x,
                req.relative_permittivity_y,
                req.charge_density_c_m3,
                fixed,
            )
