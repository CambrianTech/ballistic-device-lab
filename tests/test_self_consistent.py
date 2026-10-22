import unittest

import numpy as np

from physics_layers.electrostatics import EPSILON_0
from physics_layers.poisson2d import Poisson2DRequest
from physics_layers.self_consistent import ConvergenceError, IterationPlan, solve_charge_field


class LinearScreening:
    """Manufactured linear charge response, not a graphene transport model."""

    def __init__(self, source, susceptibility, reference=0.0):
        self.source = source
        self.susceptibility = susceptibility
        self.reference = reference

    def charge_density_c_m3(self, potential_v):
        return self.source - self.susceptibility * (np.array(potential_v) - self.reference)


def fixture(offset=0.0):
    n, h = 17, 1e-9
    yy, xx = np.mgrid[:n, :n]
    phi = 0.01 * np.sin(np.pi * xx / (n - 1)) * np.sin(np.pi * yy / (n - 1))
    fixed = phi + offset
    fixed[1:-1, 1:-1] = np.nan
    # Exact discrete eigenvalue: tests the nonlinear coordinator independently
    # of the continuum discretization error tested in test_poisson2d.
    eigenvalue = 8 * EPSILON_0 * np.sin(np.pi / (2 * (n - 1))) ** 2 / h**2
    susceptibility = 0.5 * eigenvalue
    mesh = Poisson2DRequest(h, h, np.ones((n, n - 1)), np.ones((n - 1, n)), np.zeros((n, n)), fixed)
    return (
        mesh,
        LinearScreening((eigenvalue + susceptibility) * phi, susceptibility, offset),
        phi + offset,
    )


class SelfConsistentTests(unittest.TestCase):
    def test_screened_solution_and_gauge_shift(self):
        for offset in (0.0, 0.3):
            mesh, provider, expected = fixture(offset)
            result = solve_charge_field(
                mesh,
                provider,
                np.full(expected.shape, offset),
                IterationPlan(potential_tolerance_v=1e-10),
            )
            np.testing.assert_allclose(result.field.potential_v, expected, atol=1e-10)
            self.assertLessEqual(result.history[-1].charge_residual_c_m3, 1e-5)
            self.assertLess(result.field.residual_c_m3, 1e-7)

    def test_tiny_mixing_does_not_fake_convergence(self):
        mesh, provider, expected = fixture()
        with self.assertRaises(ConvergenceError) as caught:
            solve_charge_field(
                mesh,
                provider,
                np.zeros_like(expected),
                IterationPlan(mixing=1e-12, max_iterations=3),
            )
        self.assertEqual(len(caught.exception.history), 3)
        self.assertGreater(caught.exception.history[-1].unmixed_potential_residual_v, 0.01)

    def test_inner_failure_propagates(self):
        class Broken:
            def charge_density_c_m3(self, potential_v):
                raise ArithmeticError("Transport failed")

        mesh, _, expected = fixture()
        with self.assertRaisesRegex(ArithmeticError, "Transport failed"):
            solve_charge_field(mesh, Broken(), expected, IterationPlan())

    def test_invalid_charge_rejected(self):
        class Broken:
            def charge_density_c_m3(self, potential_v):
                return np.full(np.shape(potential_v), np.nan)

        mesh, _, expected = fixture()
        with self.assertRaises(ValueError):
            solve_charge_field(mesh, Broken(), expected, IterationPlan())
