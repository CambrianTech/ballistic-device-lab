"""Analytic electrical networks and forbidden spurious DC checks."""

import unittest

import numpy as np

from ballistic_lab.transport.reservoirs import (
    G_QUANTUM,
    ThermalRequest,
    conductance_matrix,
    solve_load,
    thermal_conductance,
)


class ReservoirChecks(unittest.TestCase):
    def test_conductance_quantum_and_gauge(self):
        g = conductance_matrix([[0, 1], [1, 0]], [1, 1])
        np.testing.assert_allclose(g, 2 * G_QUANTUM * np.array([[1, -1], [-1, 1]]))
        np.testing.assert_allclose(g @ np.ones(2), 0, atol=1e-20)

    def test_thermal_constant_channel(self):
        rows = [
            dict(energy_ev=e, transmission=[[0, 1], [1, 0]], modes=[1, 1])
            for e in np.linspace(-0.4, 0.4, 401)
        ]
        g, mass = thermal_conductance(rows, ThermalRequest(0, 300))
        self.assertAlmostEqual(mass, 1, delta=1e-6)
        self.assertAlmostEqual(g[0, 0] / (2 * G_QUANTUM), 1, delta=1e-6)
        with self.assertRaises(ValueError):
            thermal_conductance(rows[::50], ThermalRequest(0, 300))

    def test_known_series_network_and_no_ac_rectification(self):
        # L--B--load--T--R: two 1 kohm device resistors plus 2 kohm load.
        g = np.zeros((4, 4))
        for i, j in ((0, 3), (1, 2)):
            g[i, i] += 0.001
            g[j, j] += 0.001
            g[i, j] -= 0.001
            g[j, i] -= 0.001
        positive = solve_load(g, 0.001, 2000)
        negative = solve_load(g, -0.001, 2000)
        self.assertAlmostEqual(positive.output_voltage_v, 0.0005)
        self.assertAlmostEqual(positive.load_power_w, 1.25e-10, delta=1e-22)
        self.assertAlmostEqual(positive.input_power_w, 2.5e-10, delta=1e-22)
        self.assertEqual(positive.output_voltage_v + negative.output_voltage_v, 0)
        self.assertAlmostEqual(positive.power_residual_w, 0, delta=1e-22)

    def test_invalid_and_disconnected_models_fail(self):
        with self.assertRaises(ValueError):
            conductance_matrix([[0, 0.5], [1, 0]], [1, 1])
        with self.assertRaises(ValueError):
            solve_load(np.zeros((4, 4)), 0.001, 1000)
        with self.assertRaises(ValueError):
            ThermalRequest(0, 0)
