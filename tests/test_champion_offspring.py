import copy
import json
from pathlib import Path
import unittest
from ballistic_lab.pipeline.fresh_discovery import champion_offspring


class ChampionTests(unittest.TestCase):
    def test_initial_population_keeps_every_family_in_each_repeat(self):
        from ballistic_lab.search.dc_space import WideDCPlan, proposals
        parent=json.loads(Path('results/fresh-discovery/champion-probe-261026/selection.json').read_text())['parent']
        items=[c for repeat in range(2) for c in proposals(WideDCPlan(),repeat,0,[])]
        result=champion_offspring(items,parent,.25,123,0)
        self.assertEqual(sum(r.get('proposal_strategy')=='champion' for r in result),10)
        for repeat in range(2):
            for family in WideDCPlan().families:
                self.assertTrue(any(c['repeat']==repeat and c['family']==family and c['origin']=='fresh global' for c in result))

    def test_budget_lineage_reproducibility_and_parent_immutability(self):
        parent=json.loads(Path('results/fresh-discovery/champion-probe-261026/selection.json').read_text())['parent']
        before=copy.deepcopy(parent)
        items=[dict(key=str(i), repeat=i//10, origin='fresh global' if i%2==0 else 'mutation of other') for i in range(20)]
        result=champion_offspring(items,parent,.25,123,3)
        self.assertEqual(result,champion_offspring(items,parent,.25,123,3))
        offspring=[r for r in result if r.get('proposal_strategy')=='champion']
        self.assertEqual(len(offspring),5)
        self.assertEqual(len({r['key'] for r in result}),20)
        self.assertEqual(sum(r['origin']=='fresh global' for r in result),10)
        self.assertTrue(all(r['parent_key']==parent['candidate']['key'] for r in offspring))
        self.assertEqual(parent,before)
        self.assertEqual(champion_offspring(items,parent,0,123,3),items)
        with self.assertRaises(ValueError): champion_offspring(items,parent,.6,123,3)
        parent['phase_converged']=False
        with self.assertRaises(ValueError): champion_offspring(items,parent,.25,123,3)
