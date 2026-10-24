import json
import os
from pathlib import Path
import tempfile
import unittest
from ballistic_lab.reporting.discovery_gallery import render

class GalleryTests(unittest.TestCase):
    def test_pending_is_not_promoted_and_completed_is_data_driven(self):
        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                run=Path('runs/small-feedback-test');run.mkdir(parents=True)
                row=dict(name='custom-shape',device=dict(obstacles=[],width_m=2e-9,contact_width_fraction=.4),evaluations=[{},{}])
                (run/'custom.json').write_text(json.dumps(row))
                state=dict(completed=[])
                (run/'status.json').write_text(json.dumps(state))
                self.assertEqual(render({})['evidence']['cards'][0]['result'],'Evaluation pending')
                state['completed']=[dict(name='custom-shape',phase='complete',even_transverse_current_difference_a=3e-12)]
                (run/'status.json').write_text(json.dumps(state))
                card=render({})['evidence']['cards'][0]
                self.assertEqual(card['result'],'+3.000 pA even ΔI')
                self.assertIn('2.000 nm',card['detail'])
            finally:
                os.chdir(previous)
