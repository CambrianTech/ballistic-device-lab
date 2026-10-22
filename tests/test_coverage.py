"""Coverage boundaries prevent invalid comparison and false convergence."""

import unittest

from ballistic_lab.experiments.coverage import CoveragePlan, output_convergence
from ballistic_lab.models import RayConfig
from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.pipeline.ray import RayRequest, RayStage
from ballistic_lab.transport.quantum import LatticeRequest


class CoverageChecks(unittest.TestCase):
    def test_changed_contacts_are_part_of_device_identity(self):
        nominal = SquareDevice((), 1e-8)
        wide = SquareDevice((), 1e-8, 0.4)
        self.assertNotEqual(nominal.fingerprint, wide.fingerprint)
        with self.assertRaises(ValueError):
            RayStage(None).evaluate(wide, RayRequest(RayConfig(), (10, 20)))
        with self.assertRaises(ValueError):
            LatticeRequest((0.5,), lattice_offset=(float("nan"), 0))

    def test_output_specific_tolerance_and_condition_matching(self):
        old = [dict(fermi_ev=0.9, load_ohm=1e4, output_voltage_v=1e-6)]
        new = [dict(fermi_ev=0.9, load_ohm=1e4, output_voltage_v=1.1e-6)]
        self.assertFalse(output_convergence(old, new, CoveragePlan())[0]["passed"])
        new[0]["output_voltage_v"] = 1.001e-6
        self.assertTrue(output_convergence(old, new, CoveragePlan())[0]["passed"])
        new[0]["fermi_ev"] = 0.8
        with self.assertRaises(ValueError):
            output_convergence(old, new, CoveragePlan())
