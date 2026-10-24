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
