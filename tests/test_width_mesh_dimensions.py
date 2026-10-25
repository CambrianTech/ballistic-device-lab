import copy
import unittest
from ballistic_lab.reporting.compare_width_mesh import validate_dimensions


class DimensionsTests(unittest.TestCase):
    def setUp(self):
        self.record=dict(positions_m=[[0,0,0],[1,1,1]],
                         rows=[dict(shape=[3,3,3],spacing_m=[1,1,1],potential_v=[0,1])])

    def test_complete_record(self):
        validate_dimensions(self.record)

    def test_missing_values_cannot_silently_shorten_zip(self):
        for key in ('shape','spacing_m','potential_v'):
            with self.subTest(key=key):
                record=copy.deepcopy(self.record)
                record['rows'][0][key].pop()
                with self.assertRaises(ValueError):
                    validate_dimensions(record)

    def test_empty_sites_rejected(self):
        self.record['positions_m']=[]
        with self.assertRaises(ValueError):
            validate_dimensions(self.record)
