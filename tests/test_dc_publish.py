"""Reports cannot overwrite archives or publish unfinished refinements."""

import json
import tempfile
import unittest
from pathlib import Path

from ballistic_lab.pipeline.dc_publish import publish


class PublishChecks(unittest.TestCase):
    def test_complete_snapshot_is_immutable_and_rerenderable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "summary.json").write_text(
                json.dumps([dict(candidate=dict(key="x"), levels=[{}, {}, {}], phase64={})]),
                encoding="utf-8",
            )
            (source / "selection.json").write_text(
                json.dumps(dict(ranking=["x"], selected=["x"])), encoding="utf-8"
            )
            publish(source, root / "archive")
            publish(source, root / "archive")
            (source / "extra.txt").write_text("changed", encoding="utf-8")
            with self.assertRaises(ValueError):
                publish(source, root / "archive")
            (source / "summary.json").write_text(
                json.dumps([dict(candidate=dict(key="x"), levels=[{}])]), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                publish(source, root / "unfinished")
