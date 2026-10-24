import unittest
from physics_layers.polarity import polarity_components


class PolarityTests(unittest.TestCase):
    def test_linear_response_has_no_even_component(self):
        r=polarity_components(.01,-.01,.002,-.002)
        self.assertEqual(r['even_output_v'],0)
        self.assertEqual(r['odd_output_v'],.002)

    def test_even_and_odd_response_reconstruction(self):
        # f(V)=a*V+b*V**2: exact analytic parity oracle.
        v=.01
        plus=2*v+3*v*v
        minus=-2*v+3*v*v
        r=polarity_components(v,-v,plus,minus)
        self.assertAlmostEqual(r['even_output_v'],3*v*v)
        self.assertAlmostEqual(r['odd_output_v'],2*v)
        self.assertAlmostEqual(r['even_output_v']+r['odd_output_v'],plus)
        self.assertAlmostEqual(r['even_output_v']-r['odd_output_v'],minus)
        # A sinusoid averages V**2 to amplitude**2/2, not amplitude**2.
        self.assertAlmostEqual(r['even_output_v']/2,3*v*v/2)

    def test_unmatched_or_nonfinite_rejected(self):
        for args in ((.01,-.02,1,2),(0,0,1,2),(.01,-.01,float('nan'),2)):
            with self.assertRaises(ValueError): polarity_components(*args)
