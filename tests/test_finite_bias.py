"""Finite-bias physical oracles, independent of graphene geometry."""

import unittest

import numpy as np

from ballistic_lab.transport.circuit import sinusoidal_cycle
from ballistic_lab.transport.finite_bias import FrozenPotentialModel
from ballistic_lab.transport.reservoirs import ThermalRequest, thermal_conductance


def spectrum(dispersive=False):
    rows = []
    for energy in np.linspace(-1, 1, 1001):
        t = np.zeros((4, 4))
        for i, j, weight in ((0, 2, 0.2), (1, 2, 0.2), (0, 3, 0.3), (1, 3, 0.3), (2, 3, 0.1)):
            t[i, j] = t[j, i] = weight * (1 + 0.4 * energy if dispersive and j == 3 else 1)
        np.fill_diagonal(t, 1 - t.sum(axis=0))
        rows.append(dict(energy_ev=energy, transmission=t.tolist(), modes=[1] * 4))
    return rows


class FiniteBiasChecks(unittest.TestCase):
    def test_equilibrium_gauge_and_linear_limit(self):
        rows = spectrum(True)
        request = ThermalRequest(0, 300)
        model = FrozenPotentialModel.from_spectrum(rows, request)
        np.testing.assert_array_equal(model.currents(np.full(4, 0.01)), np.zeros(4))
        v = np.array([0.01, -0.01, 0.002, -0.003])
        shifted = FrozenPotentialModel.from_spectrum(rows, request, reference_v=0.2)
        np.testing.assert_allclose(model.currents(v), shifted.currents(v + 0.2), atol=1e-19)
        g, _ = thermal_conductance(rows, request)
        small = v * 1e-4
        np.testing.assert_allclose(model.currents(small), g @ small, atol=1e-16, rtol=1e-5)
        self.assertLess(abs(model.currents(v).sum()), 1e-19)
        self.assertGreater(v @ model.currents(v), 0)

    def test_constant_spectrum_has_zero_dc_and_dispersive_can_rectify(self):
        request = ThermalRequest(0, 300)
        constant = sinusoidal_cycle(
            FrozenPotentialModel.from_spectrum(spectrum(), request), 0.02, 1e4, 32
        )
        self.assertLess(abs(constant.dc_output_v), 1e-12)
        model = FrozenPotentialModel.from_spectrum(spectrum(True), request)
        coarse = sinusoidal_cycle(model, 0.02, 1e4, 32)
        fine = sinusoidal_cycle(model, 0.02, 1e4, 64)
        self.assertGreater(abs(fine.dc_output_v), 1e-8)
        self.assertAlmostEqual(coarse.dc_output_v, fine.dc_output_v, delta=1e-12)

    def test_window_and_conservation_rejected(self):
        rows = spectrum()
        model = FrozenPotentialModel.from_spectrum(rows, ThermalRequest(0, 300))
        with self.assertRaises(ValueError):
            model.currents(np.array([1.0, 0, 0, 0]))
        rows[0]["transmission"][0][1] += 0.1
        with self.assertRaises(ValueError):
            FrozenPotentialModel.from_spectrum(rows, ThermalRequest(0, 300))

    def test_output_exchange_reverses_dc_and_small_signal_is_quadratic(self):
        rows = spectrum(True)
        request = ThermalRequest(0, 300)
        model = FrozenPotentialModel.from_spectrum(rows, request)
        first = sinusoidal_cycle(model, 0.01, 1e4, 32)
        second = sinusoidal_cycle(model, 0.02, 1e4, 32)
        self.assertAlmostEqual(second.dc_output_v / first.dc_output_v, 4, delta=0.001)
        permutation = [0, 1, 3, 2]
        for row in rows:
            row["transmission"] = np.array(row["transmission"])[np.ix_(permutation, permutation)]
        exchanged = sinusoidal_cycle(
            FrozenPotentialModel.from_spectrum(rows, request), 0.01, 1e4, 32
        )
        self.assertAlmostEqual(exchanged.dc_output_v, -first.dc_output_v, delta=1e-12)
