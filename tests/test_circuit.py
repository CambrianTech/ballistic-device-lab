"""Independent resistor and diode-bridge oracles for terminal/cycle accounting."""

import unittest

import numpy as np

from ballistic_lab.transport.circuit import sinusoidal_cycle, solve_terminal_load
from ballistic_lab.transport.reservoirs import solve_load


class ResistorModel:
    def __init__(self):
        self.g = np.zeros((4, 4))
        for i, j in ((0, 3), (1, 2)):
            self.g[i, i] += 0.001
            self.g[j, j] += 0.001
            self.g[i, j] -= 0.001
            self.g[j, i] -= 0.001

    def currents(self, voltage):
        return self.g @ voltage


class BridgeModel:
    """Passive piecewise-linear diode bridge; analytic output factor known."""

    def currents(self, voltage):
        result = np.zeros(4)
        for i, j in ((0, 3), (1, 3), (2, 0), (2, 1)):
            difference = voltage[i] - voltage[j]
            current = 0.001 * (difference if difference >= 0 else 0.01 * difference)
            result[i] += current
            result[j] -= current
        return result


class CircuitChecks(unittest.TestCase):
    def test_linear_limit_matches_independent_matrix_solver(self):
        model = ResistorModel()
        for drive in (-0.001, 0, 0.001):
            reference = solve_load(model.g, drive, 2000)
            result = solve_terminal_load(model, drive, 2000)
            np.testing.assert_allclose(result.voltage_v, reference.terminal_voltages_v, atol=1e-15)
            self.assertAlmostEqual(result.input_power_w, reference.input_power_w, delta=1e-22)
        cycle = sinusoidal_cycle(model, 0.001, 2000)
        self.assertLess(abs(cycle.dc_output_v), 1e-18)
        self.assertAlmostEqual(cycle.total_load_power_w, 0.0005**2 / 4000, delta=1e-22)
        self.assertAlmostEqual(cycle.ripple_load_power_w, cycle.total_load_power_w, delta=1e-22)

    def test_rectifying_bridge_and_phase_convergence(self):
        model = BridgeModel()
        factor = 0.99 / (1.01 + 2 / (0.001 * 2000))
        for drive in (-0.001, 0.001):
            solution = solve_terminal_load(model, drive, 2000)
            self.assertAlmostEqual(solution.output_v, abs(drive) * factor, delta=1e-15)
        coarse = sinusoidal_cycle(model, 0.001, 2000, 32)
        fine = sinusoidal_cycle(model, 0.001, 2000, 128)
        expected = 2 / np.pi * 0.001 * factor
        self.assertLess(abs(fine.dc_output_v - expected), abs(coarse.dc_output_v - expected))
        self.assertAlmostEqual(fine.dc_output_v / expected, 1, delta=0.0003)
        self.assertAlmostEqual(fine.dc_load_power_w, fine.dc_output_v**2 / 2000, delta=1e-22)
        self.assertGreater(fine.ripple_load_power_w, 0)
        self.assertGreater(fine.dc_efficiency, 0)
        self.assertLess(fine.dc_efficiency, 1)
        self.assertAlmostEqual(
            fine.mean_input_power_w,
            fine.mean_device_power_w + fine.total_load_power_w,
            delta=1e-22,
        )

    def test_invalid_current_provider_rejected(self):
        class Invalid:
            def currents(self, voltage):
                return np.ones(4)

        with self.assertRaises(ValueError):
            solve_terminal_load(Invalid(), 0.001, 1000)
        with self.assertRaises(ValueError):
            sinusoidal_cycle(ResistorModel(), 0.001, 1000, 7)

        class Disconnected:
            def currents(self, voltage):
                return np.zeros(4)

        with self.assertRaises(ValueError):
            solve_terminal_load(Disconnected(), 0.001, 1000)


if __name__ == "__main__":
    unittest.main()
