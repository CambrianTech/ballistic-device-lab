import unittest

import numpy as np
from scipy.constants import Boltzmann, elementary_charge, h
from scipy.integrate import quad
from scipy.special import digamma, expit

from physics_layers.negf_reference import WideBandDevice, solve_hartree


class NEGFReferenceTests(unittest.TestCase):
    def test_resonant_level_charge_and_current(self):
        energy, left, right, temperature = 0.07, 0.08, 0.12, 300
        mus = np.array([0.1, -0.04])
        width = left + right
        kt = Boltzmann * temperature / elementary_charge
        device = WideBandDevice([[energy]], [[[left]], [[right]]])
        result = device.solve([0], mus, temperature)
        occupation = (
            0.5
            - np.imag(
                digamma(0.5 + width / (4 * np.pi * kt) + 1j * (energy - mus) / (2 * np.pi * kt))
            )
            / np.pi
        )
        expected = 2 * np.dot([left, right], occupation) / width
        self.assertAlmostEqual(result.electrons_per_site[0], expected, delta=1e-8)
        integral = quad(
            lambda e: (
                left
                * right
                / ((e - energy) ** 2 + (width / 2) ** 2)
                * (expit((mus[0] - e) / kt) - expit((mus[1] - e) / kt))
            ),
            -2,
            2,
            epsabs=1e-11,
        )[0]
        expected_current = 2 * elementary_charge**2 / h * integral
        np.testing.assert_allclose(
            result.currents_a, [expected_current, -expected_current], atol=1e-13
        )

    def test_gauge_invariance_and_equilibrium(self):
        device = WideBandDevice(
            [[0.1, -0.2], [-0.2, -0.03]], [np.diag([0.1, 0]), np.diag([0, 0.12])]
        )
        a = device.solve([0, 0], [0.05, -0.02], 300)
        b = device.solve([0.37, 0.37], [0.42, 0.35], 300)
        np.testing.assert_allclose(a.electrons_per_site, b.electrons_per_site, atol=1e-8)
        np.testing.assert_allclose(a.currents_a, b.currents_a, atol=1e-13)
        equilibrium = device.solve([0, 0], [0, 0], 300)
        np.testing.assert_allclose(equilibrium.currents_a, 0, atol=1e-20)

    def test_charge_feedback_screens_and_converges(self):
        device = WideBandDevice([[0]], [[[0.1]], [[0.1]]])
        result = solve_hartree(device, [0, 0], 300, [1], [[0.4]], [-0.1])
        self.assertTrue(-0.1 < result.onsite_shift_ev[0] < 0)
        self.assertGreater(result.transport.electrons_per_site[0], 1)
        self.assertLessEqual(result.residual_history_ev[-1], 1e-7)
        finer = solve_hartree(
            device, [0, 0], 300, [1], [[0.4]], [-0.1], tolerance_ev=1e-9, quadrature_tolerance=1e-11
        )
        np.testing.assert_allclose(result.onsite_shift_ev, finer.onsite_shift_ev, atol=1e-7)
        with self.assertRaises(ArithmeticError):
            solve_hartree(device, [0, 0], 300, [1], [[0.4]], [-0.1], max_iterations=1)

    def test_invalid_bound_state_case_rejected(self):
        with self.assertRaises(ValueError):
            WideBandDevice(np.zeros((2, 2)), [np.diag([0.1, 0])])
