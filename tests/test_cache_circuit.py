"""Cache compatibility with independent passive circuit oracles."""
import unittest
from dataclasses import asdict
import numpy as np
from ballistic_lab.transport.circuit import solve_terminal_load
from physics_layers.current_cache import ExactCurrentCache
from tests.test_circuit import ResistorModel, BridgeModel


class CacheCircuitTests(unittest.TestCase):
    def test_cache_preserves_load_solution_and_conditioning(self):
        for factory in (ResistorModel, BridgeModel):
            for drive in (-0.001, 0.001):
                with self.subTest(model=factory.__name__, drive=drive):
                    class Counted:
                        def __init__(self):
                            self.model = factory()
                            self.calls = []
                        def currents(self, voltage):
                            self.calls.append(tuple(voltage))
                            return self.model.currents(voltage)
                    plain, cached = Counted(), Counted()
                    expected = solve_terminal_load(plain, drive, 2000)
                    actual = solve_terminal_load(ExactCurrentCache(cached), drive, 2000)
                    self.assertEqual(asdict(actual), asdict(expected))
                    self.assertLess(len(cached.calls), len(plain.calls))
                    self.assertEqual(set(cached.calls), set(plain.calls))
                    self.assertTrue(np.isfinite(actual.output_jacobian_condition))
                    print(factory.__name__, drive, len(plain.calls), len(cached.calls))


if __name__ == '__main__':
    unittest.main()
