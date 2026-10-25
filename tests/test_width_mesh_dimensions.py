import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from ballistic_lab.reporting.compare_width_mesh import validate_dimensions


class DimensionsTests(unittest.TestCase):
    def setUp(self):
        self.record=dict(positions_m=[[0,0,0],[1,1,1]],
                         rows=[dict(shape=[3,3,3],spacing_m=[1,1,1],potential_v=[0,1])])

    def test_complete_record(self):
        validate_dimensions(self.record)

    def test_missing_values_cannot_silently_shorten_zip(self):
        for key in ('shape','spacing_m','potential_v'):
            with self.subTest(key=key):
                record=copy.deepcopy(self.record)
                record['rows'][0][key].pop()
                with self.assertRaises(ValueError):
                    validate_dimensions(record)

    def test_empty_sites_rejected(self):
        self.record['positions_m']=[]
        with self.assertRaises(ValueError):
            validate_dimensions(self.record)


class SavedComparisonTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]
    coarse = Path('results/physics-reference/width-sensitivity-011/result.json')
    fine = Path('results/physics-reference/width-sensitivity-011-fine/result.json')

    def compare(self, coarse, fine, output):
        return subprocess.run(
            [sys.executable, '-m', 'ballistic_lab.reporting.compare_width_mesh',
             str(coarse), str(fine), str(output)],
            cwd=self.root, capture_output=True, text=True)

    def test_saved_physics_comparison_reproduces_every_field(self):
        expected = json.loads((self.root / self.fine.parent / 'comparison.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'comparison.json'
            run = self.compare(self.coarse, self.fine, output)
            self.assertEqual(run.returncode, 0, run.stderr)
            actual = json.loads(output.read_text())
            # Path separators differ across operating systems; hashes and all
            # scientific fields must still reproduce the published evidence.
            for record in (actual, expected):
                record['input_sha256'] = {
                    key.replace('\\', '/'): value
                    for key, value in record['input_sha256'].items()}
            self.assertEqual(actual, expected)

    def test_truncated_saved_potential_produces_no_report(self):
        record = json.loads((self.root / self.fine).read_text())
        record['rows'][0]['potential_v'].pop()
        with tempfile.TemporaryDirectory() as directory:
            fine = Path(directory) / 'truncated.json'
            fine.write_text(json.dumps(record))
            output = Path(directory) / 'comparison.json'
            run = self.compare(self.coarse, fine, output)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('Every site must have a potential', run.stderr)
            self.assertFalse(output.exists())
