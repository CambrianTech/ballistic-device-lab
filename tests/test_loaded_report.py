import unittest
from dataclasses import asdict
from ballistic_lab.transport.circuit import solve_terminal_load, CircuitTolerance
from tests.test_circuit import ResistorModel
from physics_layers.report_loaded_complete import validate


class CompletedReportTests(unittest.TestCase):
    def setUp(self):
        self.status = dict(phase='complete',source_sha256={'fixture':'test'})
        self.result = dict(solution=asdict(solve_terminal_load(ResistorModel(),0.001,2000)),
                           drive_v=0.001,load_ohm=2000,circuit_tolerance=asdict(CircuitTolerance()),
                           source_sha256={'fixture':'test'})

    def test_independent_passive_reference(self):
        check=validate(self.status,self.result)
        self.assertAlmostEqual(check['output_v'],0.0005,places=15)
        self.assertAlmostEqual(check['load_power_w'],0.0005**2/2000,places=22)

    def test_incomplete_and_corrupt_results_rejected(self):
        self.status['phase']='load'
        with self.assertRaises(ValueError): validate(self.status,self.result)
        self.status['phase']='complete'
        self.result['solution']['load_power_w'] *= 2
        with self.assertRaises(ValueError): validate(self.status,self.result)
        self.result['source_sha256']={}
        with self.assertRaises(ValueError): validate(self.status,self.result)

    def test_wrong_declared_drive_rejected(self):
        self.result['drive_v'] = -0.001
        with self.assertRaises(ValueError):
            validate(self.status,self.result)
