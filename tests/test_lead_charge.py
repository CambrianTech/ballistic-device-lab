import importlib.util
import unittest

import numpy as np
from scipy.constants import elementary_charge, h

from physics_layers.lead_charge import LeadChargeDevice


def chain():
    import kwant

    lat = kwant.lattice.chain(norbs=1)
    builder = kwant.Builder()
    builder[lat(0)] = 0
    lead = kwant.Builder(kwant.TranslationalSymmetry([-1]))
    lead[lat(0)] = 0
    lead[lat(0), lat(1)] = -1
    builder.attach_lead(lead)
    builder.attach_lead(lead.reversed())
    return builder.finalized()


@unittest.skipUnless(importlib.util.find_spec("kwant"), "Kwant runtime required")
class LeadChargeTests(unittest.TestCase):
    def test_full_band_charge_current_and_gauge(self):
        system = chain()
        device = LeadChargeDevice(system, (-2, 2))
        result = device.solve([0], [0.05, -0.05], 300, tolerance=1e-7)
        np.testing.assert_allclose(result.electrons_per_site, [1], atol=1e-6)
        expected = 2 * elementary_charge**2 / h * 0.1
        np.testing.assert_allclose(result.currents_a, [expected, -expected], rtol=1e-6)
        shifted = LeadChargeDevice(system, (-1.63, 2.37), lead_shifts_ev=[0.37, 0.37])
        other = shifted.solve([0.37], [0.42, 0.32], 300, tolerance=1e-7)
        np.testing.assert_allclose(other.electrons_per_site, result.electrons_per_site, atol=1e-6)
        np.testing.assert_allclose(other.currents_a, result.currents_a, atol=1e-12)

    def test_missing_band_and_bound_state_rejected(self):
        for bounds, shift in [((-1, 1), 0), ((-2, 2), 1)]:
            with self.assertRaisesRegex(ArithmeticError, "spectral weight"):
                LeadChargeDevice(chain(), bounds).solve([shift], [0, 0], 300, tolerance=1e-6)

    def test_graphene_injectivity_matches_kwant(self):
        import kwant

        from ballistic_lab.pipeline.contracts import SquareDevice
        from ballistic_lab.transport.quantum import LatticeRequest, build_system

        system = build_system(SquareDevice((), 4 * 0.246e-9), LatticeRequest((0.7,)))
        device = LeadChargeDevice(system, (-8.1, 8.1))
        density, transmission = device.spectral(0.7, np.zeros(len(system.sites)))
        wave = kwant.wave_function(system, 0.7)
        for port in range(len(system.leads)):
            expected = np.sum(abs(wave(port)) ** 2, axis=0) / (2 * np.pi)
            np.testing.assert_allclose(density[port], expected, atol=1e-10)
        smatrix = kwant.smatrix(system, 0.7)
        for out in range(len(system.leads)):
            for inc in range(len(system.leads)):
                if out != inc:
                    self.assertAlmostEqual(transmission[out, inc], smatrix.transmission(out, inc))

    def test_neutral_poisson_pipeline(self):
        from physics_layers.site_feedback import solve_site_feedback
        from tests.test_site_feedback import fixture

        mesh, mapping, _ = fixture(0)
        result = solve_site_feedback(
            mesh, mapping, LeadChargeDevice(chain(), (-2, 2)), [1], [0, 0], 300
        )
        np.testing.assert_allclose(result.site_potential_v, [0], atol=1e-8)
        np.testing.assert_allclose(result.transport.currents_a, [0, 0], atol=1e-14)
