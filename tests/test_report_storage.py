import tempfile
import unittest
from pathlib import Path

from ballistic_lab.reporting.storage import archive, drain


class ReportStorageTests(unittest.TestCase):
    def test_drain_preserves_bytes_and_mutable_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a, b = (root / name for name in ("round-000001", "round-000002"))
            a.mkdir()
            b.mkdir()
            for directory in (a, b):
                (directory / "round-000001.json").write_bytes(b'{"history":1}')
                (directory / "source.json").write_bytes(b"source")
            result = drain(root)
            self.assertEqual(result["reclaimed_bytes"], 13)
            self.assertTrue((a / "round-000001.json").samefile(b / "round-000001.json"))
            self.assertFalse((a / "source.json").samefile(b / "source.json"))
            self.assertEqual(drain(root)["reclaimed_bytes"], 0)

    def test_conflict_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for n in (1, 2):
                directory = root / f"round-{n:06d}"
                directory.mkdir()
                (directory / "round-000001.json").write_text(str(n))
            with self.assertRaises(ValueError):
                drain(root)
            self.assertEqual((root / "round-000002/round-000001.json").read_text(), "2")

    def test_new_publication_shares_archive_not_live_input(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "round-000001.json"
            source.write_bytes(b"history")
            targets = [root / f"round-{n:06d}" / source.name for n in (1, 2)]
            for target in targets:
                target.parent.mkdir()
                archive(source, target)
            self.assertTrue(targets[0].samefile(targets[1]))
            self.assertFalse(source.samefile(targets[0]))
