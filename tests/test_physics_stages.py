import unittest
from dataclasses import replace
from unittest.mock import patch

import numpy as np

from physics_layers.dc_stage import DCRequest, dc_stage
from physics_layers.stages import Check, RunIdentity, Stage, StageFailure, run_stages
from tests.test_circuit import BridgeModel

IDENTITY = RunIdentity("fixture-device", "resistor-network", "10mV-10kohm")


def fixture(name, dependencies=(), evaluate=lambda identity, inputs: 1):
    return Stage(
        name,
        "fixture-v1",
        ("Manufactured fixture only",),
        dependencies,
        evaluate,
        (Check("valid", lambda value: True),),
    )


class LinearNetwork:
    def currents(self, voltage):
        return 1e-5 * (4 * voltage - np.sum(voltage))


class StageTests(unittest.TestCase):
    def test_rectifier_matches_analytic_mean_and_power_balance(self):
        provider = fixture("transport", evaluate=lambda identity, inputs: BridgeModel())
        stage = dc_stage(
            DCRequest(0.001, 2000, phases=128),
            current_stage="transport",
            source_identity="bridge-fixture-v1",
        )
        result = run_stages(IDENTITY, (provider, stage))
        cycle = result.outputs["quasistatic_dc"].refined
        expected = 2 / np.pi * 0.001 * 0.99 / (1.01 + 2 / (0.001 * 2000))
        self.assertAlmostEqual(cycle.dc_output_v / expected, 1, delta=0.0001)
        self.assertGreater(cycle.ripple_load_power_w, 0)
        self.assertAlmostEqual(
            cycle.mean_input_power_w,
            cycle.mean_device_power_w + cycle.total_load_power_w,
            delta=1e-20,
        )

    def test_configuration_changes_provenance(self):
        first = fixture("first")
        changed = replace(first, configuration_json='{"temperature_k": 300}')
        self.assertNotEqual(
            run_stages(IDENTITY, (first,)).provenance_fingerprint,
            run_stages(IDENTITY, (changed,)).provenance_fingerprint,
        )

    def test_orders_dependencies_and_passes_only_declared_inputs(self):
        first = fixture("first")
        second = fixture("second", ("first",), lambda identity, inputs: inputs["first"] + 2)
        result = run_stages(IDENTITY, (second, first))
        self.assertEqual(result.outputs["second"], 3)
        self.assertEqual([r.stage for r in result.receipts], ["first", "second"])
        with self.assertRaises(TypeError):
            result.outputs["first"] = 0
        changed = run_stages(replace(IDENTITY, materials="other"), (second, first))
        self.assertNotEqual(result.provenance_fingerprint, changed.provenance_fingerprint)

    def test_missing_and_cyclic_dependencies_fail_before_any_solver(self):
        calls = []
        first = fixture("first", evaluate=lambda identity, inputs: calls.append(1))
        for stages in (
            (first, fixture("second", ("missing",))),
            (first, fixture("second", ("third",)), fixture("third", ("second",))),
        ):
            with self.assertRaises(ValueError):
                run_stages(IDENTITY, stages)
        self.assertEqual(calls, [])

    def test_failed_validation_never_runs_downstream(self):
        calls = []
        bad = replace(fixture("bad"), checks=(Check("conservation", lambda value: False),))
        later = fixture("later", ("bad",), lambda identity, inputs: calls.append(1))
        with self.assertRaises(StageFailure) as error:
            run_stages(IDENTITY, (fixture("before"), bad, later))
        self.assertEqual([r.stage for r in error.exception.completed], ["before"])
        self.assertIn("conservation", str(error.exception.__cause__))
        self.assertEqual(calls, [])

    def test_inner_solver_failure_propagates(self):
        def fail(identity, inputs):
            raise RuntimeError("charge failed to converge")

        with self.assertRaises(StageFailure) as error:
            run_stages(IDENTITY, (fixture("charge", evaluate=fail),))
        self.assertIn("charge failed", str(error.exception.__cause__))

    def test_actual_circuit_linear_network_has_no_dc(self):
        provider = fixture("transport", evaluate=lambda identity, inputs: LinearNetwork())
        stage = dc_stage(
            DCRequest(0.01, 10000, phases=8),
            current_stage="transport",
            source_identity="circuit-fixture-v1",
        )
        result = run_stages(IDENTITY, (stage, provider))
        cycle = result.outputs["quasistatic_dc"].refined
        self.assertAlmostEqual(cycle.dc_output_v, 0, delta=1e-14)
        self.assertGreater(cycle.mean_input_power_w, 0)
        self.assertEqual(len(cycle.samples), 16)

    def test_dc_refinement_failure_blocks_acceptance(self):
        provider = fixture("transport", evaluate=lambda identity, inputs: LinearNetwork())
        stage = dc_stage(
            DCRequest(0.01, 10000, phases=8),
            current_stage="transport",
            source_identity="circuit-fixture-v1",
        )
        valid = run_stages(IDENTITY, (provider, stage)).outputs["quasistatic_dc"]
        changed = replace(valid.refined, dc_output_v=0.001)
        with patch("physics_layers.dc_stage.sinusoidal_cycle", side_effect=[valid.coarse, changed]):
            with self.assertRaises(StageFailure) as error:
                run_stages(IDENTITY, (provider, stage))
        self.assertIn("Phase refinement failed", str(error.exception.__cause__))

    def test_unvalidated_stage_rejected(self):
        with self.assertRaises(ValueError):
            replace(fixture("empty"), checks=())


if __name__ == "__main__":
    unittest.main()
