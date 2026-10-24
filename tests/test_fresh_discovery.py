import unittest
from dataclasses import replace
from ballistic_lab.pipeline.fresh_discovery import choose_champion
from ballistic_lab.search.dc_space import WideDCPlan, proposals
class FreshTests(unittest.TestCase):
 def test_only_converged_improvements_promote(self):
  def row(power,ok):return dict(energy_converged=ok,phase_converged=ok,phase64=dict(dc_power_w=power))
  old=row(5,True)
  self.assertIs(choose_champion(old,[row(99,False),row(4,True)]),old)
  better=row(6,True);self.assertIs(choose_champion(old,[better]),better)
 def test_new_seed_changes_population_reproducibly(self):
  old=proposals(WideDCPlan(),0,0,[])
  plan=replace(WideDCPlan(),seeds=(241026,241126))
  fresh=proposals(plan,0,0,[])
  self.assertEqual(fresh,proposals(plan,0,0,[]))
  self.assertNotEqual([x['obstacles'] for x in old],[x['obstacles'] for x in fresh])
  self.assertEqual(len({x['family'] for x in fresh}),5)
