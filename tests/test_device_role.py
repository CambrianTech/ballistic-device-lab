import unittest

from ballistic_lab.reporting.device_role import metrics


class DeviceRoleTests(unittest.TestCase):
    def test_signal_response_and_efficiency_are_distinct(self):
        result = metrics(dict(dc_v=-20e-6, dc_power_w=4e-14, input_power_w=2e-9))
        self.assertAlmostEqual(result["loaded_responsivity_v_per_w"], 10000)
        self.assertAlmostEqual(result["dc_efficiency"], 2e-5)

    def test_undefined_input_is_rejected(self):
        for power in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                metrics(dict(dc_v=1, dc_power_w=1, input_power_w=power))
