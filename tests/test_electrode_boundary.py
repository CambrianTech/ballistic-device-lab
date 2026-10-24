import unittest

import numpy as np

from physics_layers.electrode_boundary import ElectrodeBoundary
from physics_layers.poisson3d import Poisson3DRequest, Poisson3DStage


class ElectrodeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.shape = (7, 7, 7)
        outside = np.zeros(self.shape, bool)
        outside[[0, -1], :, :] = True
        outside[:, [0, -1], :] = True
        outside[:, :, [0, -1]] = True
        left = np.zeros(self.shape, bool)
        left[:, :, 0] = True
        self.masks = (left, outside & ~left)

    def test_laplace_gauge_and_superposition(self):
        boundary = ElectrodeBoundary(self.masks)
        faces = tuple(
            np.ones(tuple(n - (i == axis) for i, n in enumerate(self.shape))) * 4
            for axis in range(3)
        )

        def solve(v):
            return (
                Poisson3DStage()
                .evaluate(
                    Poisson3DRequest(
                        (1e-9,) * 3, faces, np.zeros(self.shape), boundary.potentials(v)
                    )
                )
                .potential_v
            )

        a, b = solve([0.1, 0]), solve([0, 0.2])
        np.testing.assert_allclose(solve([0.1, 0.2]), a + b, atol=1e-14)
        np.testing.assert_allclose(solve([0.47, 0.37]), a + 0.37, atol=1e-14)
        self.assertGreaterEqual(a.min(), -1e-14)
        self.assertLessEqual(a.max(), 0.1 + 1e-14)

    def test_geometry_is_an_immutable_snapshot(self):
        from dataclasses import FrozenInstanceError

        boundary = ElectrodeBoundary(self.masks)
        expected = boundary.potentials([0.1, 0.2]).copy()
        self.masks[0][:] = False
        np.testing.assert_equal(boundary.potentials([0.1, 0.2]), expected)
        with self.assertRaises(ValueError):
            boundary.masks[0].setflags(write=True)
        with self.assertRaises(FrozenInstanceError):
            boundary.masks = ()
        with self.assertRaises(FrozenInstanceError):
            boundary.shape = (3, 3, 3)

    def test_reject_overlap_missing_face_and_bad_voltage(self):
        with self.assertRaises(ValueError):
            ElectrodeBoundary((self.masks[0], self.masks[0] | self.masks[1]))
        with self.assertRaises(ValueError):
            ElectrodeBoundary((self.masks[0],))
        with self.assertRaises(ValueError):
            ElectrodeBoundary(self.masks).potentials([0, float("nan")])


if __name__ == "__main__":
    unittest.main()
