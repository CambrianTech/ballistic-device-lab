import unittest

import numpy as np

from physics_layers.electrostatics import EPSILON_0
from physics_layers.poisson3d import Poisson3DRequest, Poisson3DStage, deposit_sheet


def boundaries(exact):
    fixed = exact.copy()
    fixed[1:-1, 1:-1, 1:-1] = np.nan
    return fixed


def faces(shape, value=1.0):
    return tuple(
        np.full(tuple(n - (a == axis) for a, n in enumerate(shape)), value) for axis in range(3)
    )


class Poisson3DTests(unittest.TestCase):
    def test_manufactured_second_order_unequal_spacing(self):
        errors = []
        for n in (9, 17):
            lengths = np.array([2e-8, 3e-8, 5e-8])
            z, y, x = np.meshgrid(*(np.linspace(0, 1, n) for _ in range(3)), indexing="ij")
            exact = np.sin(np.pi * z) * np.sin(np.pi * y) * np.sin(np.pi * x)
            rho = EPSILON_0 * np.pi**2 * np.sum(1 / lengths**2) * exact
            fixed = boundaries(exact)
            rho[np.isfinite(fixed)] = 0
            result = Poisson3DStage().evaluate(
                Poisson3DRequest(tuple(lengths / (n - 1)), faces(exact.shape), rho, fixed)
            )
            errors.append(np.max(abs(result.potential_v - exact)))
        self.assertGreater(errors[0] / errors[1], 3.9)
        self.assertLess(errors[0] / errors[1], 4.1)

    def test_sheet_charge_analytic_and_gauge(self):
        shape = (17, 7, 9)
        h = (1e-9, 2e-9, 3e-9)
        sigma = 1e-4
        z = np.arange(shape[0]) * h[0]
        exact = np.broadcast_to(
            (sigma / (2 * EPSILON_0) * np.minimum(z, z[-1] - z))[:, None, None], shape
        ).copy()
        fixed = boundaries(exact)
        sheet = np.zeros(shape[1:])
        sheet[1:-1, 1:-1] = sigma
        rho = deposit_sheet(sheet, 8, h, fixed)
        self.assertAlmostEqual(float(rho.sum() * np.prod(h) / (sheet.sum() * h[1] * h[2])), 1)
        for shift in (0, 0.7):
            result = Poisson3DStage().evaluate(
                Poisson3DRequest(h, faces(shape), rho, fixed + shift)
            )
            np.testing.assert_allclose(result.potential_v, exact + shift, atol=2e-14)
            dz = EPSILON_0 * result.electric_field_faces_v_m[0]
            np.testing.assert_allclose(dz[8, 1:-1, 1:-1] - dz[7, 1:-1, 1:-1], sigma, atol=1e-15)

    def test_layered_dielectric_displacement(self):
        shape = (9, 5, 5)
        h = (1e-9, 2e-9, 3e-9)
        eps = list(faces(shape))
        eps[0][4:] = 4
        profile = np.r_[0, np.cumsum(1 / eps[0][:, 0, 0])]
        profile /= profile[-1]
        exact = np.broadcast_to(profile[:, None, None], shape).copy()
        result = Poisson3DStage().evaluate(
            Poisson3DRequest(h, tuple(eps), np.zeros(shape), boundaries(exact))
        )
        np.testing.assert_allclose(result.potential_v, exact, atol=1e-14)
        displacement = eps[0] * result.electric_field_faces_v_m[0]
        np.testing.assert_allclose(
            displacement, np.full_like(displacement, displacement[0, 0, 0]), rtol=1e-13
        )

    def test_internal_electrode_and_input_contract(self):
        shape = (5, 5, 5)
        fixed = boundaries(np.zeros(shape))
        fixed[2, 2, 2] = 1
        request = Poisson3DRequest((1, 1, 1), faces(shape), np.zeros(shape), fixed)
        fixed[:] = 8
        result = Poisson3DStage().evaluate(request)
        self.assertEqual(result.potential_v[2, 2, 2], 1)
        self.assertGreater(result.potential_v[2, 2, 1], 0)
        with self.assertRaises(ValueError):
            result.potential_v.setflags(write=True)
        sheet = np.zeros((5, 5))
        sheet[2, 2] = 1
        with self.assertRaises(ValueError):
            deposit_sheet(sheet, 2, (1, 1, 1), request.fixed_potential_v)
        bad = np.zeros(shape)
        bad[0, 0, 0] = 1
        with self.assertRaises(ValueError):
            Poisson3DRequest((1, 1, 1), faces(shape), bad, request.fixed_potential_v)


if __name__ == "__main__":
    unittest.main()
