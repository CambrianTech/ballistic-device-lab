import unittest
from types import SimpleNamespace

import numpy as np

from ballistic_lab.transport.circuit import solve_terminal_load
from physics_layers.feedback_current import FeedbackCurrentModel


class FeedbackCurrentTests(unittest.TestCase):
    def test_loaded_resistor_reference_with_permuted_provider(self):
        # Independent passive network: T couples to L by 2g, R by g;
        # B couples to L by g, R by 2g. Analytic loaded differential.
        g, resistance, drive = 1e-4, 1e4, 0.01
        calls = []

        def evaluate(v):
            calls.append(v.copy())
            current = np.zeros(4)
            for a, b, conductance in [(0, 2, 2 * g), (1, 2, g), (0, 3, g), (1, 3, 2 * g)]:
                flow = conductance * (v[a] - v[b])
                current[a] += flow
                current[b] -= flow
            return SimpleNamespace(transport=SimpleNamespace(currents_a=current[[2, 0, 3, 1]]))

        model = FeedbackCurrentModel(evaluate, lead_order=(1, 3, 0, 2))
        answer = solve_terminal_load(model, drive, resistance)
        expected = -g * drive / (3 * g + 2 / resistance)
        self.assertAlmostEqual(answer.output_v, expected, places=12)
        self.assertAlmostEqual(answer.load_power_w, expected**2 / resistance, places=18)
        self.assertGreater(len(calls), 1)

    def test_failure_propagates(self):
        def failed(v):
            raise ArithmeticError("feedback did not converge")

        with self.assertRaises(ArithmeticError):
            FeedbackCurrentModel(failed, lead_order=(0, 1, 2, 3)).currents(np.zeros(4))
        with self.assertRaises(ValueError):
            FeedbackCurrentModel(failed, lead_order=(0, 0, 2, 3))
        with self.assertRaises(ValueError):
            FeedbackCurrentModel(failed, lead_order=(0, 1, 2, 3)).currents([0, 0])


if __name__ == "__main__":
    unittest.main()

