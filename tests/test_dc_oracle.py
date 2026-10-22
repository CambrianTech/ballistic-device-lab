"""Closed-form energy-linear pair current, separate from numerical integrators."""

import unittest

import numpy as np

from ballistic_lab.transport.finite_bias import FrozenPotentialModel
from ballistic_lab.transport.reservoirs import ThermalRequest
from ballistic_lab.validation.dc_score import PairCurrentOracle
from tests.test_finite_bias import spectrum


class OracleChecks(unittest.TestCase):
    def test_energy_linear_transmission_matches_closed_form(self):
        rows = spectrum(True)
        voltage = np.array([0.02, -0.015, 0.003, -0.008])
        expected = np.zeros(4)
        for i, j, a in ((0, 2, 0.2), (1, 2, 0.2), (0, 3, 0.3), (1, 3, 0.3), (2, 3, 0.1)):
            b = 0.4 * a if j == 3 else 0.0
            flow = (
                2
                * (1.602176634e-19) ** 2
                / 6.62607015e-34
                * (a * (voltage[i] - voltage[j]) + b / 2 * (voltage[i] ** 2 - voltage[j] ** 2))
            )
            expected[i] += flow
            expected[j] -= flow
        oracle = PairCurrentOracle.from_spectrum(rows, fermi_ev=0)
        production = FrozenPotentialModel.from_spectrum(rows, ThermalRequest(0, 300))
        np.testing.assert_allclose(oracle.currents(voltage), expected, rtol=1e-12, atol=1e-19)
        np.testing.assert_allclose(production.currents(voltage), expected, rtol=1e-12, atol=1e-19)
