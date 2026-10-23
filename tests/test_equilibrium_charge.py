import importlib.util
import unittest

import numpy as np

from physics_layers.equilibrium_charge import EquilibriumChargeDevice, surface_selfenergy


@unittest.skipUnless(importlib.util.find_spec("kwant"), "Kwant runtime required")
class EquilibriumChargeTests(unittest.TestCase):
    def test_graphene_poisson_feedback_and_refinement(self):
        from physics_layers.graphene_feedback_demo import fixture
        from physics_layers.site_acceleration import solve_accelerated

        mesh, mapping, provider = fixture()
        reference = np.ones(len(mapping.positions_m))
        a = solve_accelerated(mesh, mapping, provider, reference, [0, 0], 300, tolerance=1e-5)
        b = solve_accelerated(mesh, mapping, provider, reference, [0, 0], 300, tolerance=1e-6)
        np.testing.assert_allclose(a.site_potential_v, b.site_potential_v, atol=1e-6)
        np.testing.assert_allclose(
            a.transport.electrons_per_site, b.transport.electrons_per_site, atol=1e-6
        )
        self.assertLess(max(abs(np.array(b.site_potential_v))), 0.03)
        self.assertLess(b.history[-1].occupation_residual, 1e-6)

    def test_chain_including_bound_charge_and_gauge(self):
        from physics_layers.lead_charge import LeadChargeDevice
        from tests.test_lead_charge import chain

        system = chain()
        device = EquilibriumChargeDevice(system)
        a = device.solve([0], [0.2, 0.2], 300, tolerance=1e-7)
        reference = LeadChargeDevice(system, (-2, 2)).solve([0], [0.2, 0.2], 300, tolerance=1e-7)
        np.testing.assert_allclose(a.electrons_per_site, reference.electrons_per_site, atol=1e-6)
        shifted = EquilibriumChargeDevice(system, lead_shifts_ev=[0.37, 0.37])
        b = shifted.solve([0.37], [0.57, 0.57], 300, tolerance=1e-7)
        np.testing.assert_allclose(a.electrons_per_site, b.electrons_per_site, atol=1e-7)
        positive = device.solve([1], [0, 0], 300, tolerance=1e-7)
        negative = device.solve([-1], [0, 0], 300, tolerance=1e-7)
        np.testing.assert_allclose(
            np.array(positive.electrons_per_site) + negative.electrons_per_site, [2], atol=1e-6
        )
        self.assertLess(positive.electrons_per_site[0], 1)
        # Independent finite-reservoir diagonalization includes the impurity
        # bound state as an ordinary eigenstate, with no continuum quadrature.
        from scipy.constants import Boltzmann, elementary_charge
        from scipy.linalg import eigh_tridiagonal
        from scipy.special import expit

        diagonal = np.zeros(801)
        diagonal[400] = 1
        energies, vectors = eigh_tridiagonal(diagonal, -np.ones(800))
        expected = 2 * np.sum(
            abs(vectors[400]) ** 2 * expit(-energies / (Boltzmann * 300 / elementary_charge))
        )
        self.assertAlmostEqual(positive.electrons_per_site[0], expected, places=6)
        with self.assertRaisesRegex(ValueError, "equal"):
            device.solve([0], [0, 0.01], 300)

    def test_surface_matches_kwant_and_finite_chain(self):
        from physics_layers.graphene_feedback_demo import fixture

        _, _, provider = fixture()
        for lead in provider.leads:
            np.testing.assert_allclose(
                surface_selfenergy(lead, 0.7 + 1e-7j), lead.selfenergy(0.7), atol=2e-6
            )
            cell = lead.cell_hamiltonian()
            hopping = lead.inter_cell_hopping()
            n, m = hopping.shape
            t = np.zeros((n, n), complex)
            t[:, :m] = hopping
            ham = (
                np.kron(np.eye(80), cell)
                + np.kron(np.diag(np.ones(79), 1), t.conj().T)
                + np.kron(np.diag(np.ones(79), -1), t)
            )
            g = np.linalg.inv((0.4 + 0.8j) * np.eye(len(ham)) - ham)[:n, :n]
            np.testing.assert_allclose(
                surface_selfenergy(lead, 0.4 + 0.8j), hopping.conj().T @ g @ hopping, atol=1e-10
            )

    def test_graphene_neutral_and_gated_refinement(self):
        from physics_layers.graphene_feedback_demo import fixture

        _, mapping, provider = fixture()
        n = len(mapping.positions_m)
        neutral = provider.solve(np.zeros(n), [0, 0], 300, tolerance=1e-7)
        np.testing.assert_allclose(neutral.electrons_per_site, 1, atol=1e-7)
        a = provider.solve(np.full(n, -0.03), [0, 0], 300, tolerance=1e-6)
        b = provider.solve(np.full(n, -0.03), [0, 0], 300, tolerance=1e-8)
        np.testing.assert_allclose(a.electrons_per_site, b.electrons_per_site, atol=1e-6)
        self.assertGreater(min(b.electrons_per_site), 1)
