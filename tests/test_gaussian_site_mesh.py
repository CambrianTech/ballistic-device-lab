import unittest

import numpy as np

from physics_layers.gaussian_site_mesh import GaussianSiteMeshMap
from physics_layers.poisson3d import Poisson3DRequest, Poisson3DStage


class GaussianMapTests(unittest.TestCase):
    def setUp(self):
        self.shape = (19, 20, 21)
        self.spacing = (0.1e-9, 0.09e-9, 0.08e-9)
        self.positions = np.array([[0.87, 0.85, 0.81], [0.94, 0.91, 0.87]]) * 1e-9
        self.mapping = GaussianSiteMeshMap(
            self.shape, self.spacing, (0, 0, 0), self.positions, 0.12e-9
        )
        self.fixed = np.full(self.shape, np.nan)
        for axis in range(3):
            for end in (0, -1):
                sl = [slice(None)] * 3
                sl[axis] = end
                self.fixed[tuple(sl)] = 0

    def test_charge_work_and_gauge(self):
        q = np.array([1.0, -0.7]) * 1.602176634e-19
        phi = np.random.default_rng(4).normal(size=self.shape)
        rho = self.mapping.deposit_charge(q, self.fixed)
        sampled = self.mapping.sample_potential(phi)
        np.testing.assert_allclose(rho.sum() * np.prod(self.spacing), q.sum(), rtol=1e-13)
        np.testing.assert_allclose(
            np.sum(rho * phi) * np.prod(self.spacing), q @ sampled, rtol=1e-13
        )
        np.testing.assert_allclose(self.mapping.sample_potential(phi + 2), sampled + 2)

    def test_poisson_reciprocity_and_positive_energy(self):
        faces = [
            np.full(tuple(n - (i == axis) for i, n in enumerate(self.shape)), 4.0)
            for axis in range(3)
        ]
        columns = []
        for q in np.eye(2) * 1.602176634e-19:
            rho = self.mapping.deposit_charge(q, self.fixed)
            result = Poisson3DStage().evaluate(
                Poisson3DRequest(self.spacing, tuple(faces), rho, self.fixed)
            )
            columns.append(self.mapping.sample_potential(result.potential_v))
        kernel = np.array(columns).T
        np.testing.assert_allclose(kernel, kernel.T, rtol=1e-12)
        self.assertGreater(np.linalg.eigvalsh(kernel).min(), 0)

    def test_reject_clipping_underresolution_and_electrode_cancellation(self):
        for positions, width in [(self.positions, 0.01e-9), ([[0, 0, 0]], 0.12e-9)]:
            with self.assertRaises(ValueError):
                GaussianSiteMeshMap(self.shape, self.spacing, (0, 0, 0), positions, width)
        mapping = GaussianSiteMeshMap(
            self.shape, self.spacing, (0, 0, 0), np.repeat(self.positions[:1], 2, axis=0), 0.12e-9
        )
        self.fixed[9, 9, 10] = 0
        with self.assertRaises(ValueError):
            mapping.deposit_charge([1e-19, -1e-19], self.fixed)


if __name__ == "__main__":
    unittest.main()
