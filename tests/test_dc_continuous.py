import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ballistic_lab.pipeline import dc_continuous as worker
from ballistic_lab.search.dc_space import WideDCPlan, proposals


class ContinuousChecks(unittest.TestCase):
    def test_arms_match_budget_and_global_proposals(self):
        initial = proposals(WideDCPlan(), 0, 0, []) + proposals(WideDCPlan(), 1, 0, [])
        history = [dict(candidate=c, levels=[dict(dc_power_w=i)]) for i, c in enumerate(initial)]
        batches = [worker.batch(arm, 1, history) for arm in worker.ARMS]
        self.assertEqual([len(b) for b in batches], [20, 20, 20])
        for batch in batches[1:]:
            self.assertEqual(
                [c["parameters"] for c in batch[::2]], [c["parameters"] for c in batches[0][::2]]
            )
        self.assertTrue(all(c["origin"] == "fresh random" for c in batches[2][1::2]))

    def test_single_owner_lock(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with worker.single_worker(root):
                with self.assertRaises(OSError):
                    with worker.single_worker(root):
                        pass
            with worker.single_worker(root):
                pass

    def test_stop_resume_does_not_repeat_completed_arm(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []

            def initialize(root):
                return dict(round=1, histories={arm: [] for arm in worker.ARMS}, completed=[])

            def batch(arm, index, history):
                return [dict(key=f"{arm}-{index}")]

            def task(item, output, refine):
                calls.append((item["key"], refine))
                if refine:
                    (root / "STOP").touch()
                return dict(candidate=item, levels=[dict(dc_power_w=1)])

            with (
                patch.object(worker, "initialize", initialize),
                patch.object(worker, "batch", batch),
                patch.object(worker, "task", task),
                patch.object(worker, "ProcessPoolExecutor", ThreadPoolExecutor),
            ):
                worker.run(root, workers=1)
                (root / "STOP").unlink()
                worker.run(root, workers=1)
            self.assertEqual(
                calls,
                [
                    ("elite-1", False),
                    ("elite-1", True),
                    ("diversity-1", False),
                    ("diversity-1", True),
                ],
            )
            state = json.loads((root / "state.json").read_text())
            self.assertIn("1:elite:refine", state["completed"])
