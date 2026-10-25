import unittest
from ballistic_lab.reporting.low_score_holdout import select_holdout


def row(key, family, power, refined=False):
    return dict(candidate=dict(key=key,family=family),levels=[dict(dc_power_w=power)],
                phase64={'dc_v':1} if refined else None)


class HoldoutSelectionTests(unittest.TestCase):
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
