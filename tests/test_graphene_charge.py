import unittest

import numpy as np
from scipy.constants import Boltzmann, elementary_charge, hbar

from physics_layers.graphene_charge import DiracSheet, solve_planar_gate


class GrapheneChargeTests(unittest.TestCase):
    def test_zero_temperature_density(self):
        sheet = DiracSheet(0, 1e6)
        expected = (0.1 * elementary_charge / (hbar * 1e6)) ** 2 / np.pi
        self.assertAlmostEqual(sheet.net_density_m2(0.1) / expected, 1)
        self.assertEqual(sheet.net_density_m2(-0.1), -sheet.net_density_m2(0.1))

    def test_neutrality_and_quantum_capacitance_derivative(self):
        sheet = DiracSheet(300, 1e6)
        self.assertEqual(sheet.net_density_m2(0), 0)
        for mu in (0, 0.001, 0.1, 0.8):
            derivative = (
                elementary_charge
                * (sheet.net_density_m2(mu + 1e-6) - sheet.net_density_m2(mu - 1e-6))
                / 2e-6
            )
            self.assertAlmostEqual(derivative / sheet.quantum_capacitance_f_m2(mu), 1, delta=1e-7)
        expected = (
            4 * elementary_charge**2 * Boltzmann * 300 * np.log(2) / (np.pi * (hbar * 1e6) ** 2)
        )
        self.assertAlmostEqual(sheet.quantum_capacitance_f_m2(0) / expected, 1)

    def test_zero_temperature_gate_matches_quadratic_root(self):
        sheet = DiracSheet(0, 1e6)
        capacitance, voltage = 0.002, 0.7
        a = elementary_charge**3 / (np.pi * (hbar * 1e6) ** 2)
        expected = (
            2
            * capacitance
            * voltage
            / (capacitance + np.sqrt(capacitance**2 + 4 * a * capacitance * voltage))
        )
        result = solve_planar_gate(sheet, voltage, capacitance)
        self.assertAlmostEqual(result.potential_v, expected, delta=1e-13)

    def test_finite_temperature_gate_balance_and_series_capacitance(self):
        sheet = DiracSheet(300, 1e6)
        c, v, dv = 0.002, 0.5, 1e-5
        result = solve_planar_gate(sheet, v, c)
        self.assertLess(abs(result.balance_residual_c_m2), 1e-14)
        self.assertTrue(0 < result.potential_v < v)
        negative = solve_planar_gate(sheet, -v, c)
        self.assertAlmostEqual(negative.net_density_m2 / result.net_density_m2, -1)
        measured = -(
            solve_planar_gate(sheet, v + dv, c).sheet_charge_c_m2
            - solve_planar_gate(sheet, v - dv, c).sheet_charge_c_m2
        ) / (2 * dv)
        cq = sheet.quantum_capacitance_f_m2(result.chemical_potential_ev)
        self.assertAlmostEqual(measured / (1 / (1 / c + 1 / cq)), 1, delta=1e-7)
