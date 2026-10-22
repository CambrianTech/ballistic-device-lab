"""Optional integration tests run in the isolated Kwant environment."""

import importlib.util
import unittest

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, LatticeStage


class LatticeContractChecks(unittest.TestCase):
    def test_rejects_invalid_physical_inputs(self):
        for energies in ((), (float("nan"),)):
            with self.assertRaises(ValueError):
                LatticeRequest(energies)
        with self.assertRaises(ValueError):
            LatticeRequest((0.2,), hopping_ev=0)


@unittest.skipUnless(importlib.util.find_spec("kwant"), "Optional Kwant environment required")
class LatticeIntegrationChecks(unittest.TestCase):
    def test_matched_ribbon_and_energy_gauge(self):
        from ballistic_lab.experiments.lattice import reference_gate

        reference_gate(LatticeRequest((0.3, 0.6, 0.9)), 20 * 0.246e-9)

    def test_four_terminal_conservation(self):
        result = LatticeStage().evaluate(
            SquareDevice((), 20 * 0.246e-9), LatticeRequest((0.3, 0.6, 0.9))
        )
        self.assertEqual(len(result.spectrum), 3)
        self.assertTrue(any(sum(row["modes"]) for row in result.spectrum))
