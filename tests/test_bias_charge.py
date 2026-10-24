import unittest

import numpy as np

from physics_layers.bias_charge import BiasChargeDevice
from physics_layers.lead_charge import LeadChargeDevice
from tests.test_lead_charge import chain


class BiasChargeTests(unittest.TestCase):
    def test_independent_full_band_and_reference_invariance(self):
        system = chain()
        expected = LeadChargeDevice(system, (-2, 2)).solve([0], [0.08, -0.02], 300, tolerance=1e-7)
        for reference in [-0.02, 0.03, 0.08]:
            actual = BiasChargeDevice(system, reference_mu_ev=reference).solve(
                [0], [0.08, -0.02], 300, tolerance=1e-7
            )
            np.testing.assert_allclose(
                actual.electrons_per_site, expected.electrons_per_site, atol=2e-6
            )
            np.testing.assert_allclose(actual.currents_a, expected.currents_a, atol=1e-11)

    def test_gauge(self):
        original = BiasChargeDevice(chain(), reference_mu_ev=0.03).solve(
            [0], [0.08, -0.02], 300, tolerance=1e-7
        )
        shifted = BiasChargeDevice(chain(), reference_mu_ev=0.4, lead_shifts_ev=[0.37, 0.37]).solve(
            [0.37], [0.45, 0.35], 300, tolerance=1e-7
        )
        np.testing.assert_allclose(
            original.electrons_per_site, shifted.electrons_per_site, atol=2e-6
        )
        np.testing.assert_allclose(original.currents_a, shifted.currents_a, atol=1e-11)

    def test_reject_bad_inputs(self):
        with self.assertRaises(ValueError):
            BiasChargeDevice(chain(), reference_mu_ev=float("nan"))
        with self.assertRaises(ValueError):
            BiasChargeDevice(chain(), reference_mu_ev=0).solve([0], [0], 300)

    def test_bound_state_policy_is_explicit(self):
        import kwant
        from scipy.constants import Boltzmann, elementary_charge
        from scipy.special import expit

        lat = kwant.lattice.chain(norbs=1)
        b = kwant.Builder()
        b[lat(0)] = 0.0
        b[lat(10)] = 0.04
        lead = kwant.Builder(kwant.TranslationalSymmetry([-1]))
        lead[lat(0)] = 0.0
        lead[lat(0), lat(1)] = -1.0
        b.attach_lead(lead)
        b.attach_lead(lead.reversed(), origin=lat(0))
        system = b.finalized()
        isolated = list(system.sites).index(lat(10))
        for reference in [-0.02, 0.02]:
            result = BiasChargeDevice(system, reference_mu_ev=reference).solve(
                np.zeros(len(system.sites)), [0.05, -0.05], 300, tolerance=1e-7
            )
            expected = 2 * expit((reference - 0.04) / (Boltzmann * 300 / elementary_charge))
            self.assertAlmostEqual(result.electrons_per_site[isolated], expected, places=6)

    def test_bound_state_gauge_and_unshifted_reference_control(self):
        """A bound occupation closure must transform with the energy gauge."""
        import kwant
        from scipy.constants import Boltzmann, elementary_charge
        from scipy.special import expit

        lat = kwant.lattice.chain(norbs=1)
        builder = kwant.Builder()
        builder[lat(0)] = 0.0
        builder[lat(10)] = 0.04
        lead = kwant.Builder(kwant.TranslationalSymmetry([-1]))
        lead[lat(0)] = 0.0
        lead[lat(0), lat(1)] = -1.0
        builder.attach_lead(lead)
        builder.attach_lead(lead.reversed(), origin=lat(0))
        system = builder.finalized()
        isolated = list(system.sites).index(lat(10))
        shift = 0.37
        original = BiasChargeDevice(system, reference_mu_ev=0.02).solve(
            np.zeros(len(system.sites)), [0.05, -0.05], 300, tolerance=1e-7
        )
        shifted = BiasChargeDevice(
            system, reference_mu_ev=0.02 + shift, lead_shifts_ev=[shift, shift]
        ).solve(
            np.full(len(system.sites), shift), [0.05 + shift, -0.05 + shift], 300, tolerance=1e-7
        )
        control = BiasChargeDevice(
            system, reference_mu_ev=0.02, lead_shifts_ev=[shift, shift]
        ).solve(
            np.full(len(system.sites), shift), [0.05 + shift, -0.05 + shift], 300, tolerance=1e-7
        )
        np.testing.assert_allclose(
            original.electrons_per_site, shifted.electrons_per_site, rtol=0, atol=2e-6
        )
        np.testing.assert_allclose(original.currents_a, shifted.currents_a, rtol=0, atol=1e-11)
        kt = Boltzmann * 300 / elementary_charge
        expected_control = 2 * expit((0.02 - 0.04 - shift) / kt)
        self.assertAlmostEqual(control.electrons_per_site[isolated], expected_control, places=6)
        self.assertGreater(
            abs(control.electrons_per_site[isolated] - original.electrons_per_site[isolated]), 0.5
        )
        np.testing.assert_allclose(original.currents_a, control.currents_a, rtol=0, atol=1e-11)

    def test_spin_degeneracy_scales_charge_and_current(self):
        system = chain()
        single = BiasChargeDevice(system, reference_mu_ev=0.03, spin=1).solve(
            [0.07], [0.08, -0.02], 300, tolerance=1e-7
        )
        double = BiasChargeDevice(system, reference_mu_ev=0.03, spin=2).solve(
            [0.07], [0.08, -0.02], 300, tolerance=1e-7
        )
        self.assertGreater(abs(single.currents_a[0]), 1e-7)
        np.testing.assert_allclose(
            double.electrons_per_site, 2 * np.array(single.electrons_per_site), rtol=0, atol=2e-6
        )
        np.testing.assert_allclose(
            double.currents_a, 2 * np.array(single.currents_a), rtol=0, atol=1e-11
        )

    def test_invalid_numerical_controls(self):
        for cap in [0, 127, 128.0, True]:
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                BiasChargeDevice(chain(), reference_mu_ev=0.03, max_poles=cap)
        provider = BiasChargeDevice(chain(), reference_mu_ev=0.03)
        for tolerance in [0, -1e-7, float("nan"), float("inf")]:
            with self.subTest(tolerance=tolerance), self.assertRaises(ValueError):
                provider.solve([0], [0.08, -0.02], 300, tolerance=tolerance)
        for temperature in [0, -1, float("nan"), float("inf")]:
            with self.subTest(temperature=temperature), self.assertRaises(ValueError):
                provider.solve([0], [0.08, -0.02], temperature)

    def test_explicit_pole_budget_preserves_converged_charge(self):
        system = chain()
        a = BiasChargeDevice(system, reference_mu_ev=0.03)
        b = BiasChargeDevice(system, reference_mu_ev=0.03, max_poles=65536)
        self.assertEqual(b.equilibrium.max_poles, 65536)
        first = a.solve([0.07], [0.08, -0.02], 300, tolerance=1e-7)
        second = b.solve([0.07], [0.08, -0.02], 300, tolerance=1e-7)
        np.testing.assert_allclose(
            first.electrons_per_site, second.electrons_per_site, atol=1e-9, rtol=0
        )
        np.testing.assert_allclose(first.currents_a, second.currents_a, atol=1e-14, rtol=0)
