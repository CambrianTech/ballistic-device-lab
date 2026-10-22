import unittest

import numpy as np

from physics_layers.poisson3d import Poisson3DRequest, Poisson3DStage
from physics_layers.site_mesh import SiteMeshMap


class SiteMeshTests(unittest.TestCase):
    def setUp(self):
        self.shape = (7, 8, 9)
        self.spacing = np.array([0.7, 1.1, 0.9]) * 1e-9
        self.origin = np.array([-2.0, -3.0, -4.0]) * 1e-9
        rng = np.random.default_rng(2410)
        positions = self.origin + rng.uniform(1.1, 4.8, (31, 3)) * self.spacing
        self.mapping = SiteMeshMap(self.shape, tuple(self.spacing), tuple(self.origin), positions)
        self.fixed = np.full(self.shape, np.nan)
        for axis in range(3):
            sl = [slice(None)] * 3
            for end in (0, -1):
                sl[axis] = end
                self.fixed[tuple(sl)] = 0

    def test_conservation_adjoint_and_linear_field(self):
        """Catches axis swaps, missing cell volume and mismatched interpolation."""
        charge = np.random.default_rng(4).normal(size=31) * 1.602176634e-19
        z, y, x = np.indices(self.shape)
        phi = 0.17 + 0.03 * z - 0.07 * y + 0.11 * x
        rho = self.mapping.deposit_charge(charge, self.fixed)
        sampled = self.mapping.sample_potential(phi)
        coord = (self.mapping.positions_m - self.origin) / self.spacing
        np.testing.assert_allclose(
            sampled, 0.17 + coord @ np.array([0.03, -0.07, 0.11]), atol=1e-14
        )
        self.assertAlmostEqual(rho.sum() * np.prod(self.spacing) / charge.sum(), 1.0, places=13)
        np.testing.assert_allclose(
            charge @ sampled, np.sum(rho * phi) * np.prod(self.spacing), rtol=1e-13
        )
        np.testing.assert_allclose(
            self.mapping.sample_potential(phi + 2.5), sampled + 2.5, atol=1e-14
        )

    def test_electrode_overlap_cannot_cancel(self):
        positions = np.repeat([self.origin + 0.5 * self.spacing], 2, axis=0)
        mapping = SiteMeshMap(self.shape, tuple(self.spacing), tuple(self.origin), positions)
        with self.assertRaises(ValueError):
            mapping.deposit_charge([1e-19, -1e-19], self.fixed)

    def test_poisson_coupling_reciprocity_and_positive_energy(self):
        """Two different charge distributions must share a reciprocal Green operator."""
        faces = []
        for axis in range(3):
            shape = list(self.shape)
            shape[axis] -= 1
            faces.append(np.full(shape, 4.0))
        rng = np.random.default_rng(29)
        q1, q2 = rng.normal(size=(2, 31)) * 1e-20

        def solve(q):
            rho = self.mapping.deposit_charge(q, self.fixed)
            result = Poisson3DStage().evaluate(
                Poisson3DRequest(tuple(self.spacing), tuple(faces), rho, self.fixed)
            )
            return self.mapping.sample_potential(result.potential_v)

        p1, p2 = solve(q1), solve(q2)
        np.testing.assert_allclose(q1 @ p2, q2 @ p1, rtol=1e-12, atol=1e-35)
        self.assertGreater(q1 @ p1, 0.0)

    def test_mesh_plane_and_immutable_coordinates(self):
        positions = np.array([self.origin + np.array([3, 2, 4]) * self.spacing])
        mapping = SiteMeshMap(self.shape, tuple(self.spacing), tuple(self.origin), positions)
        positions[:] = 0
        rho = mapping.deposit_charge([2e-19], self.fixed)
        self.assertAlmostEqual(rho[3, 2, 4] * np.prod(self.spacing) / 2e-19, 1.0, places=13)
        with self.assertRaises(ValueError):
            mapping.positions_m.setflags(write=True)
        with self.assertRaises(ValueError):
            SiteMeshMap(self.shape, tuple(self.spacing), tuple(self.origin), [[-1.0, 0.0, 0.0]])


if __name__ == "__main__":
    unittest.main()
