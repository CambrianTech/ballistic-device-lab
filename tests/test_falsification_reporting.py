import json
import tempfile
import unittest
from pathlib import Path

from ballistic_lab.reporting.falsification import render


class FalsificationReportingTests(unittest.TestCase):
    def test_missing_failed_and_stale_receipts_never_pass(self):
        row = {"candidate": {"key": "fixture", "obstacles": []}, "phase64": {"dc_v": 1e-6}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            target = root / "report"
            target.mkdir()
            self.assertIn("Pending", render([row], target, source))
            receipt = source / "id"
            receipt.mkdir(parents=True)
            (receipt / "input.json").write_text(json.dumps(row))
            (receipt / "result.json").write_text(
                json.dumps(
                    dict(
                        candidate=row["candidate"],
                        status="fail",
                        identity="id",
                        checks={"fresh_dc": False},
                    )
                )
            )
            text = render([row], target, source)
            self.assertIn("FAIL", text)
            self.assertNotIn("| Pass |", text)
            row["phase64"]["dc_v"] = 2e-6
            self.assertIn("Pending", render([row], target, source))

    def test_completed_receipt_is_archived(self):
        row = {"candidate": {"key": "fixture", "obstacles": []}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            receipt = source / "id"
            receipt.mkdir(parents=True)
            target = root / "report"
            target.mkdir()
            (receipt / "input.json").write_text(json.dumps(row))
            (receipt / "result.json").write_text(
                json.dumps(
                    dict(
                        candidate=row["candidate"],
                        identity="id",
                        status="pass",
                        checks={
                            name: True
                            for name in [
                                "connected_graph",
                                "fresh_transmission",
                                "fresh_dc",
                                "terminal_exchange",
                            ]
                        },
                    )
                )
            )
            self.assertIn("| Pass | Pass |", render([row], target, source))
            self.assertTrue((target / "falsification/id/result.json").exists())
