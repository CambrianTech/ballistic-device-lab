import unittest
from physics_layers.even_scaling import even_scaling


class EvenScalingTests(unittest.TestCase):
    def test_constant_offset_does_not_masquerade_as_nonlinearity(self):
        a, b, offset = .005, .01, 2e-6
        low, high = offset + 3*a*a, offset + 3*b*b
        raw = even_scaling(a, b, low, high)
        self.assertFalse(raw['offset_corrected'])
        self.assertIsNone(raw['zero_bias_v'])
        self.assertAlmostEqual(raw['departure_from_quadratic_v'], .75*offset)
        corrected = even_scaling(a, b, low, high, zero_bias_v=offset)
        self.assertTrue(corrected['offset_corrected'])
        self.assertAlmostEqual(corrected['departure_from_quadratic_v'], 0)
        self.assertAlmostEqual(corrected['low_coefficient_per_v'], 3)
        self.assertTrue(even_scaling(a, b, 0, 0, zero_bias_v=0)['offset_corrected'])
        with self.assertRaises(ValueError):
            even_scaling(a, b, low, high, zero_bias_v=float('nan'))

    def test_quadratic_and_quartic_oracles(self):
        a,b=.005,.01
        r=even_scaling(a,b,3*a*a,3*b*b)
        self.assertAlmostEqual(r['departure_from_quadratic_v'],0)
        r=even_scaling(a,b,3*a*a+7*a**4,3*b*b+7*b**4)
        self.assertAlmostEqual(r['departure_from_quadratic_v'],7*a*a*(a*a-b*b))

    def test_zero_response_is_defined_and_bad_amplitudes_refused(self):
        self.assertEqual(even_scaling(.005,.01,0,0)['departure_from_quadratic_v'],0)
        for args in ((0,.01,0,0),(.01,.005,0,0),(.005,.01,float('nan'),0)):
            with self.assertRaises(ValueError): even_scaling(*args)
