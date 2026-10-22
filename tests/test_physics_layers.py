import unittest

import numpy as np

from physics_layers.coupling import PassiveOpticalBudget, PhasorConvention, TerminalPhasor
from physics_layers.electrostatics import EPSILON_0, Poisson1DRequest, Poisson1DStage


class PhysicsLayersTests(unittest.TestCase):
    def test_uniform_charge_matches_parabolic_solution(self):
        x = np.linspace(0, 1e-7, 101)
        rho = 100.0
        r = Poisson1DStage().evaluate(
            Poisson1DRequest(x[1], (4.0,) * 100, (rho,) * 101, (0.0, 0.0))
        )
        np.testing.assert_allclose(
            r.potential_v, rho * x * (x[-1] - x) / (2 * 4 * EPSILON_0), atol=1e-14
        )
        self.assertLess(r.residual_c_m3, 1e-8)

    def test_dielectric_interface_conserves_displacement(self):
        eps = np.r_[np.ones(50) * 2, np.ones(50) * 8]
        r = Poisson1DStage().evaluate(Poisson1DRequest(1e-9, eps, (0.0,) * 101, (0.0, 1.0)))
        displacement = eps * EPSILON_0 * np.array(r.electric_field_v_m)
        np.testing.assert_allclose(displacement, displacement[0], rtol=1e-11)
        expected = 50 / 2 / (50 / 2 + 50 / 8)
        self.assertAlmostEqual(r.potential_v[50], expected)

    def test_peak_rms_equivalence_and_reactive_power(self):
        peak = TerminalPhasor(2 + 0j, 1 + 0j, 3e12, PhasorConvention.PEAK, "antenna")
        rms = TerminalPhasor(2 / np.sqrt(2), 1 / np.sqrt(2), 3e12, PhasorConvention.RMS, "antenna")
        self.assertAlmostEqual(peak.average_power_w, rms.average_power_w)
        reactive = TerminalPhasor(2 + 0j, 1j, 3e12, PhasorConvention.PEAK, "antenna")
        self.assertEqual(reactive.average_power_w, 0.0)

    def test_power_creation_rejected(self):
        with self.assertRaises(ValueError):
            PassiveOpticalBudget(1.0, 0.2, 0.2, 0.8).validate(
                absolute_tolerance_w=1e-10, relative_tolerance=1e-6
            )
        PassiveOpticalBudget(1.0, 0.2, 0.2, 0.6).validate(
            absolute_tolerance_w=1e-10, relative_tolerance=1e-6
        )
