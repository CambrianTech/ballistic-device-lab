"""Preflight regression: invalid clouds never reach occupation solves."""
import tempfile
import unittest
from unittest.mock import patch
from physics_layers import finite_width_feedback as experiment
from physics_layers.equilibrium_charge import EquilibriumChargeDevice


class WidthPreflightTests(unittest.TestCase):
    def test_boundary_overlap_precedes_charge_solve(self):
        with tempfile.TemporaryDirectory() as output:
            with patch('sys.argv', ['fixture', '--sigma-nm', '0.12', '--factors', '2', '--output', output]), patch.object(EquilibriumChargeDevice, 'solve') as charge, patch.object(experiment, 'solve_accelerated') as feedback:
                with self.assertRaisesRegex(ValueError, 'overlaps a fixed-potential node'):
                    experiment.main()
                charge.assert_not_called()
                feedback.assert_not_called()

    def test_original_width_reaches_charge_solve(self):
        with tempfile.TemporaryDirectory() as output:
            with patch('sys.argv', ['fixture', '--sigma-nm', '0.10', '--factors', '2', '4', '--output', output]), patch.object(EquilibriumChargeDevice, 'solve', side_effect=RuntimeError('preflight passed')) as charge:
                with self.assertRaisesRegex(RuntimeError, 'preflight passed'):
                    experiment.main()
                charge.assert_called_once()


if __name__ == '__main__':
    unittest.main()
