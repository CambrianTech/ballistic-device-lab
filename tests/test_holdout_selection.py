import unittest
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from ballistic_lab.reporting.low_score_holdout import select_holdout


def row(key, family, power, refined=False):
    return dict(candidate=dict(key=key,family=family),levels=[dict(dc_power_w=power)],
                phase64={'dc_v':1} if refined else None)


class HoldoutSelectionTests(unittest.TestCase):
    def test_partial_run_directory_is_never_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'snapshot.json'
            source.write_text(json.dumps(dict(rows=[row('a','islands',1),row('b','islands',2)])))
            output=root/'run'
            output.mkdir()
            marker=output/'result.json'
            marker.write_text('preserve partial evidence')
            result=subprocess.run([sys.executable,'-m','ballistic_lab.reporting.low_score_holdout',
                                   '--snapshot',str(source),'--output',str(output)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('FileExistsError',result.stderr)
            self.assertEqual(marker.read_text(),'preserve partial evidence')
            self.assertFalse((output/'selection.json').exists())

    def test_exclusion_keeps_original_lower_half_boundary(self):
        rows=[row(str(i),'islands',i) for i in range(4)]
        chosen,pool,population=select_holdout(rows,'islands',['0'])
        self.assertEqual((chosen['candidate']['key'],pool,population),('1',1,4))
        with self.assertRaises(ValueError):
            select_holdout(rows,'islands',['0','1'])

    def test_family_filter_precedes_lower_half(self):
        rows=[row('i','islands',0),row('a','radial',10),row('b','radial',20)]
        chosen,pool,population=select_holdout(rows,'radial')
        self.assertEqual((chosen['candidate']['key'],pool,population),('a',1,2))

    def test_refined_lower_half_does_not_promote_upper_half(self):
        with self.assertRaises(ValueError):
            select_holdout([row('a','radial',1,True),row('b','radial',2)],'radial')

    def test_order_independent_and_missing_family_rejected(self):
        rows=[row(str(i),'radial',i) for i in range(8)]
        self.assertEqual(select_holdout(rows),select_holdout(list(reversed(rows))))
        with self.assertRaises(ValueError):
            select_holdout(rows,'absent')
