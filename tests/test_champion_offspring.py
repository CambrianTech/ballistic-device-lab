import copy
import json
from pathlib import Path
import unittest
from ballistic_lab.pipeline.fresh_discovery import champion_offspring


class ChampionTests(unittest.TestCase):
    def test_multiple_parents_share_total_budget_and_rotate(self):
        from unittest.mock import patch
        parents=[dict(candidate=dict(key=f'p{i}'),energy_converged=True,phase_converged=True,phase64={'dc_power_w':1}) for i in range(7)]
        items=[dict(key=str(i),repeat=0,origin='mutation of other') for i in range(20)]
        with patch('ballistic_lab.search.broad_champion.broad_child',return_value={'family':'polygon','obstacles':[]}):
            first=champion_offspring(items,parents,.25,1,0)
            second=champion_offspring(items,parents,.25,1,1)
        a=[r['parent_key'] for r in first if r.get('proposal_strategy')=='champion']
        b=[r['parent_key'] for r in second if r.get('proposal_strategy')=='champion']
        self.assertEqual(a,['p0','p1','p2','p3','p4'])
        self.assertEqual(set(b),{'p5','p6','p0','p1','p2'})
        self.assertEqual(len(b),5)

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

    def test_broad_children_change_geometry_and_do_not_duplicate_siblings(self):
        import numpy as np
        from ballistic_lab.search.broad_champion import shape_mask, difference
        parent=json.loads(Path('results/fresh-discovery/champion-probe-261026/selection.json').read_text())['parent']
        items=[dict(key=str(i), repeat=i//10, origin='fresh global' if i%2==0 else 'mutation of other') for i in range(20)]
        for seed in range(12):
            children=[r for r in champion_offspring(items,parent,.25,seed,1) if r.get('proposal_strategy')=='champion']
            self.assertEqual(len(children),5)
            masks=[]
            for c in children:
                mask=shape_mask(c['obstacles'])
                area,relative=difference(mask,shape_mask(parent['candidate']['obstacles']))
                self.assertGreaterEqual(area,.035)
                self.assertGreaterEqual(relative,.20)
                for sibling in masks:
                    a,r=difference(mask,sibling)
                    self.assertGreaterEqual(a,.02)
                    self.assertGreaterEqual(r,.15)
                masks.append(mask)
        square=[[[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]]]
        mask=shape_mask(square)
        self.assertAlmostEqual(float(mask.mean()),.25)
        self.assertEqual(difference(mask,mask),(0,0))
