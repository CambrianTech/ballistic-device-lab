import copy
import unittest
from dataclasses import asdict
from ballistic_lab.transport.circuit import solve_terminal_load, CircuitTolerance
from tests.test_circuit import ResistorModel
from physics_layers.compare_polarity import compare_completed


class MatchedPolarityTests(unittest.TestCase):
    def test_matched_reference_and_mismatch_refusals(self):
        status=dict(phase='complete',source_sha256={'model.py':'a'})
        def result(drive):
            return dict(solution=asdict(solve_terminal_load(ResistorModel(),drive,2000)),
                        drive_v=drive,load_ohm=2000,max_poles=128,cache_currents=True,
                        circuit_tolerance=asdict(CircuitTolerance()),source_sha256={'model.py':'a'})
        a,b=result(.001),result(-.001)
        self.assertAlmostEqual(compare_completed(status,a,status,b)['even_output_v'],0,places=15)
        bad=copy.deepcopy(b); bad['max_poles']=256
        with self.assertRaises(ValueError): compare_completed(status,a,status,bad)
        changed=copy.deepcopy(status); changed['source_sha256']['model.py']='b'
        bad=copy.deepcopy(b); bad['source_sha256']=changed['source_sha256']
        with self.assertRaises(ValueError): compare_completed(status,a,changed,bad)
        self.assertEqual(compare_completed(status,a,changed,bad,reviewed_source_changes=['model.py'])['reviewed_source_changes'],['model.py'])
