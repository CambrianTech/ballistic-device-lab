import unittest
import numpy as np
from simulate import trace, shapes


class TransportChecks(unittest.TestCase):
    def test_straight_rays_reach_opposite_contact(self):
        for port, opposite in enumerate([1, 0, 3, 2]):
            probabilities, lengths, _ = trace([], port, n=256, spread=0)
            self.assertEqual(probabilities[opposite], 1.)
            np.testing.assert_allclose(lengths, 2., atol=1e-7)

    def test_scattering_conserves_particles(self):
        for mfp in [None, .5, 2.]:
            probabilities, lengths, _, destinations = trace(
                shapes('triangle'), 0, n=2048, specularity=.8,
                mfp=mfp, seed=42, return_dest=True)
            self.assertAlmostEqual(float(probabilities.sum()), 1.)
            self.assertTrue(np.all((destinations >= 0) & (destinations < 4)))
            self.assertTrue(np.all(np.isfinite(lengths) & (lengths > 0)))

    def test_empty_cavity_up_down_symmetry(self):
        probabilities, _, _ = trace([], 0, n=32768, seed=71)
        self.assertLess(abs(probabilities[2] - probabilities[3]), .015)


if __name__ == '__main__':
    unittest.main()
