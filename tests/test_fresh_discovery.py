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

class RefinementTests(unittest.TestCase):
 def test_converged_leaders_do_not_consume_pending_slots(self):
  from ballistic_lab.pipeline.fresh_discovery import refinement_queue
  def row(key,power,ok):
   return dict(candidate=dict(key=key),levels=[dict(dc_power_w=power)],energy_converged=ok,phase_converged=ok,phase64=dict(dc_power_w=power))
  rows=[row('leader',100,True),row('second',90,True),row('pending',80,False),row('other',70,False),row('lower',60,False)]
  self.assertEqual([r['candidate']['key'] for r in refinement_queue(rows)],['pending','other'])

class StrategyTests(unittest.TestCase):
 def test_mixed_visits_every_strategy_without_random_schedule(self):
  from ballistic_lab.pipeline.fresh_discovery import strategy_for
  self.assertEqual([strategy_for('mixed',i) for i in range(1,7)],['elite','diversity','random']*2)
  self.assertEqual(strategy_for('random',9),'random')
  with self.assertRaises(ValueError):strategy_for('unknown',1)

class FamilyRefinementTests(unittest.TestCase):
 def test_rotating_slot_reaches_low_scoring_family(self):
  from ballistic_lab.pipeline.fresh_discovery import refinement_queue
  def row(key,family,power):
   return dict(candidate=dict(key=key,family=family),levels=[dict(dc_power_w=power)])
  rows=[row('a','beveled',100),row('b','beveled',90),row('c','radial',1)]
  self.assertEqual([r['candidate']['key'] for r in refinement_queue(rows,'family',1)],['a','c'])
  self.assertEqual(len(refinement_queue(rows[:1],'family',1)),1)
  self.assertEqual(refinement_queue([],'family'),[])
  with self.assertRaises(ValueError): refinement_queue(rows,'invalid')
