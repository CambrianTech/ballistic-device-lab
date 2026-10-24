"""Independent ordered examples for the published rank audit CLI."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


def row(key, coarse, fine, qualified=True):
    return dict(candidate=dict(key=key, family='synthetic'),
                levels=[dict(count=257, dc_power_w=coarse)],
                phase64=dict(dc_power_w=fine), energy_converged=qualified,
                phase_converged=qualified)


class RankAuditTests(unittest.TestCase):
    def run_case(self, rows, root):
        source = root/'snapshot.json'
        source.write_text(json.dumps(dict(round=0, rows=rows)))
        return subprocess.run([sys.executable, '-m', 'ballistic_lab.reporting.rank_stability',
                               str(source), str(root/'report')], capture_output=True, text=True)

    def test_reversal_and_unqualified_exclusion(self):
        # A>B>C becomes C>B>A: all three pairs reverse, both extremes move two.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            result = self.run_case([row('a', 3, 1), row('b', 2, 2), row('c', 1, 3),
                                    row('unresolved', 100, 100, False)], root)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((root/'report/result.json').read_text())
            self.assertEqual((data['population'], data['qualified']), (4, 3))
            self.assertEqual((data['pair_count'], data['reversed_pairs'], data['max_rank_shift']), (3, 3, 2))
            self.assertEqual((data['coarse_best'], data['refined_best']), ('a', 'c'))
            self.assertIn('unrefined candidates remain unresolved', (root/'report/README.md').read_text())

    def test_tie_is_not_a_reversal_and_existing_report_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rows = [row('a', 2, 1), row('b', 2, 3)]
            self.assertEqual(self.run_case(rows, root).returncode, 0)
            path = root/'report/result.json'
            before = path.read_bytes()
            data = json.loads(before)
            self.assertEqual((data['tied_pairs'], data['reversed_pairs']), (1, 0))
            self.assertNotEqual(self.run_case(rows, root).returncode, 0)
            self.assertEqual(path.read_bytes(), before)

    def test_duplicate_identity_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            result = self.run_case([row('a', 2, 1), row('a', 1, 2)], root)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root/'report').exists())


if __name__ == '__main__':
    unittest.main()
