import unittest
from dataclasses import replace

import numpy as np
from scipy.constants import elementary_charge

from physics_layers.negf_reference import WideBandDevice, solve_hartree
from physics_layers.poisson3d import Poisson3DRequest, Poisson3DStage
from physics_layers.site_feedback import FeedbackFailure, FeedbackPlan, solve_site_feedback
from physics_layers.site_mesh import SiteMeshMap
from physics_layers.stages import Check, RunIdentity, Stage, StageFailure, run_stages


def fixture(voltage=0.1):
    shape = (5, 5, 5)
    fixed = np.full(shape, voltage, dtype=float)
    fixed[1:-1, 1:-1, 1:-1] = np.nan
    spacing = (1e-9,) * 3
    faces = tuple(np.full(tuple(n - (a == i) for i, n in enumerate(shape)), 4.0) for a in range(3))
    mesh = Poisson3DRequest(spacing, faces, np.zeros(shape), fixed)
    mapping = SiteMeshMap(shape, spacing, (0, 0, 0), [[2e-9, 2e-9, 2e-9]])
    device = WideBandDevice([[0]], [[[0.1]], [[0.1]]])
    return mesh, mapping, device


class SiteFeedbackTests(unittest.TestCase):
    def test_screening_matches_independent_hartree_kernel(self):
        mesh, mapping, device = fixture()
        result = solve_site_feedback(mesh, mapping, device, [1], [0.04, -0.02], 300)
        grounded = np.where(np.isfinite(mesh.fixed_potential_v), 0.0, np.nan)
        rho = mapping.deposit_charge([-elementary_charge], grounded)
        response = Poisson3DStage().evaluate(
            replace(mesh, fixed_potential_v=grounded, charge_density_c_m3=rho)
        )
        kernel = -mapping.sample_potential(response.potential_v)[0]
        reference = solve_hartree(
            device, [0.04, -0.02], 300, [1], [[kernel]], [-0.1], tolerance_ev=1e-10
        )
        self.assertTrue(0 < result.site_potential_v[0] < 0.1)
        self.assertLess(result.excess_charge_c[0], 0)
        np.testing.assert_allclose(
            -np.array(result.site_potential_v), reference.onsite_shift_ev, atol=1e-8
        )
        np.testing.assert_allclose(
            result.transport.currents_a, reference.transport.currents_a, atol=1e-12
        )
        self.assertLess(abs(sum(result.transport.currents_a)), 1e-18)

    def test_uniform_gauge_shift_preserves_charge_and_current(self):
        mesh, mapping, device = fixture()
        a = solve_site_feedback(mesh, mapping, device, [1], [0.04, -0.02], 300)
        shifted = replace(mesh, fixed_potential_v=mesh.fixed_potential_v + 0.37)
        b = solve_site_feedback(shifted, mapping, device, [1], [-0.33, -0.39], 300)
        np.testing.assert_allclose(b.field.potential_v - a.field.potential_v, 0.37, atol=1e-8)
        np.testing.assert_allclose(
            a.transport.electrons_per_site, b.transport.electrons_per_site, atol=1e-8
        )
        np.testing.assert_allclose(a.transport.currents_a, b.transport.currents_a, atol=1e-12)

    def test_neutral_equilibrium_and_refinement(self):
        mesh, mapping, device = fixture(0)
        result = solve_site_feedback(mesh, mapping, device, [1], [0, 0], 300)
        np.testing.assert_allclose(result.excess_charge_c, 0, atol=1e-28)
        mesh, mapping, device = fixture()
        a = solve_site_feedback(mesh, mapping, device, [1], [0, 0], 300)
        b = solve_site_feedback(
            mesh,
            mapping,
            device,
            [1],
            [0, 0],
            300,
            FeedbackPlan(
                potential_tolerance_v=1e-10, occupation_tolerance=1e-10, quadrature_tolerance=1e-12
            ),
        )
        np.testing.assert_allclose(a.site_potential_v, b.site_potential_v, atol=1e-8)

    def test_failure_blocks_pipeline_and_tiny_mixing_cannot_pass(self):
        mesh, mapping, device = fixture()
        called = []
        stage = Stage(
            "charge_transport",
            "fixture-source",
            ("Wide-band reference",),
            (),
            lambda identity, inputs: solve_site_feedback(
                mesh,
                mapping,
                device,
                [1],
                [0, 0],
                300,
                FeedbackPlan(mixing=1e-12, max_iterations=2),
            ),
            (Check("converged", lambda value: bool(value.history)),),
        )
        downstream = Stage(
            "metric",
            "fixture-source",
            ("Fixture",),
            (stage.name,),
            lambda identity, inputs: called.append(True),
            (Check("valid", lambda value: True),),
        )
        with self.assertRaises(StageFailure) as caught:
            run_stages(RunIdentity("one-site", "wide-band", "300K"), (stage, downstream))
        self.assertIsInstance(caught.exception.__cause__, FeedbackFailure)
        self.assertEqual(called, [])


if __name__ == "__main__":
    unittest.main()
