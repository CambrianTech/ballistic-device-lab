import copy
import unittest
from ballistic_lab.reporting.compare_refinement import validate_pair

class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.base=dict(round=4,objective='fixed',control={'power':1},retained_champion={'power':2},rows=[{'candidate':{'key':'a'}}])
    def test_matched_and_mismatched_benchmarks(self):
        validate_pair(self.base,copy.deepcopy(self.base))
        for key in ('round','objective','control','retained_champion'):
            other=copy.deepcopy(self.base)
            other[key]='different'
            with self.subTest(key=key),self.assertRaises(ValueError):validate_pair(self.base,other)
            del other[key]
            with self.assertRaises(ValueError):validate_pair(self.base,other)
    def test_duplicate_candidates_rejected(self):
        other=copy.deepcopy(self.base)
        other['rows']*=2
        with self.assertRaises(ValueError):validate_pair(self.base,other)
