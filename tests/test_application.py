import json
import unittest
from dataclasses import replace

from physics_layers.application import (
    Application,
    Metric,
    Metrics,
    Requirement,
    compare,
    evaluate,
)
from physics_layers.stages import Check, RunIdentity, Stage, StageFailure

APP = Application(
    "fixture-detector",
    "1",
    ("transport", "metrics"),
    "metrics",
    (
        Requirement("noise", "W/sqrt(Hz)", "minimize", 2.0),
        Requirement("bandwidth", "Hz", "maximize", 10.0),
    ),
    "noise",
)


def stages(noise=1.0, bandwidth=20.0, unit="W/sqrt(Hz)", valid=True):
    return (
        Stage(
            "transport",
            "source-v1",
            ("Manufactured fixture",),
            (),
            lambda identity, inputs: 0,
            (Check("converged", lambda value: valid),),
        ),
        Stage(
            "metrics",
            "source-v1",
            ("Manufactured fixture",),
            ("transport",),
            lambda identity, inputs: Metrics(
                {"noise": Metric(noise, unit), "bandwidth": Metric(bandwidth, "Hz")}
            ),
            (Check("typed", lambda value: isinstance(value, Metrics)),),
        ),
    )


def run(device="candidate", **kwargs):
    return evaluate(RunIdentity(device, "fixture-material", "fixture-drive"), stages(**kwargs), APP)


class ApplicationTests(unittest.TestCase):
    def test_matched_improvement_and_serializable_receipt(self):
        result = compare(run(), run("control", noise=3), APP)
        self.assertTrue(result.eligible)
        self.assertTrue(result.beats_reference)
        self.assertEqual(json.loads(json.dumps(result.manifest()))["application"]["version"], "1")
        self.assertFalse(compare(run(), run("control"), APP).beats_reference)

    def test_missing_physics_fails_before_execution(self):
        called = []
        first = replace(stages()[0], evaluate=lambda *args: called.append(True))
        with self.assertRaises(ValueError):
            evaluate(RunIdentity("a", "b", "c"), (first,), APP)
        self.assertEqual(called, [])
        with self.assertRaises(StageFailure):
            run(valid=False)

    def test_improved_objective_cannot_hide_failed_constraint(self):
        result = compare(run(noise=0.1, bandwidth=9), run("control"), APP)
        self.assertFalse(result.eligible)
        self.assertFalse(result.beats_reference)
        self.assertIn("Target missed: bandwidth", result.reasons)

    def test_model_and_condition_mismatch_rejected(self):
        candidate, control = run(), run("control", noise=3)
        changed = replace(candidate, identity=replace(candidate.identity, materials="other"))
        self.assertFalse(compare(changed, control, APP).eligible)
        changed = replace(
            candidate,
            receipts=(
                replace(candidate.receipts[0], source_identity="v2"),
                *candidate.receipts[1:],
            ),
        )
        self.assertFalse(compare(changed, control, APP).eligible)
        self.assertFalse(compare(run(unit="pW/sqrt(Hz)"), control, APP).eligible)

    def test_missing_output_and_nonfinite_metrics_rejected(self):
        candidate = run()
        self.assertFalse(compare(replace(candidate, outputs={}), run("control"), APP).eligible)
        for value in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                Metric(value, "W")

    def test_other_application_uses_same_pipeline(self):
        # Architectural fixture only: no neuron physics is implied by these names.
        app = replace(APP, name="fixture-neuron", objective="bandwidth")
        result = compare(run(bandwidth=30), run("control", bandwidth=20), app)
        self.assertTrue(result.beats_reference)
        with self.assertRaises(TypeError):
            run().outputs["metrics"].values["noise"] = Metric(0, "W")


if __name__ == "__main__":
    unittest.main()
