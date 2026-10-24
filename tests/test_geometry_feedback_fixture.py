import unittest
import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from physics_layers.four_terminal_fixture import fixture
from physics_layers.geometry_feedback_fixture import geometry_fixture


class GeometryFeedbackFixtureTests(unittest.TestCase):
    def test_empty_control_reproduces_pilot(self):
        volts = [.005, -.005, .0001, -.0002]
        device = SquareDevice((), 4*.246e-9, contact_width_fraction=.6)
        a, mesh_a, map_a = fixture(volts)
        b, mesh_b, map_b = geometry_fixture(device, volts)
        self.assertEqual(list(a.sites), list(b.sites))
        np.testing.assert_array_equal(a.hamiltonian_submatrix(), b.hamiltonian_submatrix())
        np.testing.assert_array_equal(map_a.positions_m, map_b.positions_m)
        self.assertEqual(map_a.shape, map_b.shape)
        for name in mesh_a.__dataclass_fields__:
            left, right = getattr(mesh_a, name), getattr(mesh_b, name)
            if isinstance(left, tuple):
                for x, y in zip(left, right):
                    np.testing.assert_array_equal(x, y)
            else:
                np.testing.assert_array_equal(left, right)

    def test_obstacle_changes_actual_lattice(self):
        empty = SquareDevice((), 8*.246e-9, contact_width_fraction=.6)
        triangle = SquareDevice((((-.3,-.3),(.3,-.3),(0,.3)),),
                                empty.width_m, empty.contact_width_fraction)
        a, _, _ = geometry_fixture(empty, [0]*4)
        b, _, mapping = geometry_fixture(triangle, [0]*4)
        self.assertLess(len(b.sites), len(a.sites))
        self.assertEqual(len(b.leads), 4)
        self.assertEqual(len(mapping.positions_m), len(b.sites))
