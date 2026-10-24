import unittest
from physics_layers.even_scaling import even_scaling


class EvenScalingTests(unittest.TestCase):
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
