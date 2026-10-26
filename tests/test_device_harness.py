import unittest
from device_harness import Evaluation, distinct_champions


class ArchiveTests(unittest.TestCase):
    def row(self, key, merit, qualified=True, comparison='model-v1'):
        return Evaluation(key, comparison, merit, qualified, 'fixture/'+key)

    def test_similar_weaker_does_not_displace_distinct_parent(self):
        rows=[self.row('a',10),self.row('b',9),self.row('c',8)]
        distance=lambda a,b: .05 if {a,b}=={'a','b'} else .7
        result=distinct_champions(rows,'model-v1',distance)
        self.assertEqual([r.candidate_id for r in result],['a','c'])
        self.assertEqual(result,distinct_champions(list(reversed(rows)),'model-v1',distance))

    def test_gates_and_comparison_identity(self):
        rows=[self.row('pending',100,False),self.row('other',200,comparison='model-v2'),self.row('ok',1)]
        self.assertEqual([r.candidate_id for r in distinct_champions(rows,'model-v1',lambda a,b:1)],['ok'])

    def test_invalid_distance_and_conflicting_receipts_fail(self):
        rows=[self.row('a',2),self.row('b',1)]
        with self.assertRaises(ValueError): distinct_champions(rows,'model-v1',lambda a,b:float('nan'))
        with self.assertRaises(ValueError): distinct_champions([self.row('a',1),self.row('a',2)],'model-v1',lambda a,b:1)
        with self.assertRaises(ValueError): self.row('a',float('inf'))

    def test_improved_neighbor_replaces_old_best_and_capacity_is_bounded(self):
        rows=[self.row('old',3),self.row('new',4),self.row('different',2)]
        result=distinct_champions(rows,'model-v1',lambda a,b:0 if {a,b}=={'old','new'} else 1,2)
        self.assertEqual([r.candidate_id for r in result],['new','different'])
