import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
from ballistic_lab.pipeline.contracts import SquareDevice
from physics_layers.geometry_feedback_model import GeometryFeedbackModel

class GeometryModelTests(unittest.TestCase):
    def setUp(self):
        self.device=SquareDevice((),4*.246e-9,contact_width_fraction=.6)

    def test_invalid_input_and_expired_budget_do_not_launch_solver(self):
        m=GeometryFeedbackModel(self.device)
        with self.assertRaises(ValueError): m.currents([0,0,0,float('nan')])
        m.deadline=0
        with self.assertRaisesRegex(RuntimeError,'time budget'): m.currents([0]*4)
        self.assertEqual(m.evaluations,0)

    def test_failed_feedback_propagates_and_budget_bounds_retry(self):
        m=GeometryFeedbackModel(self.device,max_evaluations=1)
        m.neutral=np.zeros(2)
        with patch('physics_layers.geometry_feedback_model.geometry_fixture',return_value=(SimpleNamespace(sites=[1,2]),None,None)), patch('physics_layers.geometry_feedback_model.BiasChargeDevice'), patch('physics_layers.geometry_feedback_model.solve_accelerated',side_effect=RuntimeError('nonconverged')):
            with self.assertRaisesRegex(RuntimeError,'nonconverged'): m.currents([0]*4)
            with self.assertRaisesRegex(RuntimeError,'evaluation budget'): m.currents([0]*4)

    def test_completed_callback_and_current_order(self):
        saved=[];m=GeometryFeedbackModel(self.device,record=lambda v,r:saved.append(v))
        m.neutral=np.zeros(2)
        result=SimpleNamespace(transport=SimpleNamespace(currents_a=[1,-1,2,-2]))
        with patch('physics_layers.geometry_feedback_model.geometry_fixture',return_value=(SimpleNamespace(sites=[1,2]),None,None)), patch('physics_layers.geometry_feedback_model.BiasChargeDevice'), patch('physics_layers.geometry_feedback_model.solve_accelerated',return_value=result):
            np.testing.assert_equal(m.currents([.01,-.01,0,0]),[1,-1,2,-2])
        self.assertEqual(len(saved),1)

if __name__=='__main__': unittest.main()
