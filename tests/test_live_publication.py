import json
import os
from pathlib import Path
import tempfile
import unittest
from ballistic_lab.reporting.live_project import activity, replace_block
from ballistic_lab.reporting.evolution_story import select, eligible

class PublicationTests(unittest.TestCase):
    def test_markers_fail_closed_and_preserve_story(self):
        s='Intro\n<!-- x:start -->old<!-- x:end -->\nStory'
        self.assertEqual(replace_block(s,'x','new'),'Intro\n<!-- x:start -->\nnew\n<!-- x:end -->\nStory')
        for bad in ('no marker',s+s):
            with self.assertRaises(ValueError): replace_block(bad,'x','new')

    def test_dead_and_recycled_pid_do_not_claim_liveness(self):
        with tempfile.TemporaryDirectory() as temp:
            old=os.getcwd();os.chdir(temp)
            try:
                Path('status.json').write_text(json.dumps(dict(pid=123,phase='load')))
                config={'workers':[dict(status_glob='status.json',module='lab.worker',label='Lab')]}
                self.assertFalse(activity(config,{})[0]['live'])
                self.assertFalse(activity(config,{123:'python -m other.worker'})[0]['live'])
                self.assertTrue(activity(config,{123:'python -m lab.worker --run x'})[0]['live'])
            finally: os.chdir(old)

    def test_new_attempt_does_not_displace_converged_champion(self):
        def row(key,generation,power,converged):
            return dict(candidate=dict(key=key,round=generation,family='profile'),levels=[dict(dc_power_w=power)],energy_converged=converged,phase_converged=converged,phase64=dict(dc_power_w=power))
        champion=row('champ',1,5,True); pending=row('pending',2,99,False)
        attempts,best=select(dict(round=2,histories={'elite':[champion,pending]}))
        self.assertEqual(attempts,[pending]); self.assertEqual(best,champion)
        self.assertFalse(eligible(pending))

if __name__=='__main__': unittest.main()
