import unittest
import json
from pathlib import Path
import numpy as np
from ballistic_lab.search.polygon_mutation import valid_polygon,mutate_polygon

class PolygonTests(unittest.TestCase):
    def test_reject_crossing_touching_boundary_and_degenerate(self):
        self.assertTrue(valid_polygon([[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]]))
        for p in [ [[-.5,-.5],[.5,.5],[-.5,.5],[.5,-.5]], [[-1,-.5],[.5,-.5],[.5,.5]], [[0,0],[.1,0],[.2,0]], [[0,0],[0,0],[.5,.5]] ]:
            self.assertFalse(valid_polygon(p))

    def test_full_boundary_mutation_and_polygon_parent_reuse(self):
        parent=json.loads(Path('results/fresh-discovery/champion-probe-261026/selection.json').read_text())['parent']['candidate']
        rng=np.random.default_rng(261029)
        children=[c for _ in range(100) if (c:=mutate_polygon(parent,rng)) is not None]
        self.assertGreater(len(children),10)
        self.assertGreater(len({len(c['obstacles'][0]) for c in children}),1)
        self.assertTrue(all(valid_polygon(c['obstacles'][0]) for c in children))
        self.assertTrue(all(c['rotation_rad']==0 for c in children))
        self.assertTrue(all('rotation' not in c['mutation_operator'] for c in children))
        self.assertTrue(any(mutate_polygon(children[0],rng) is not None for _ in range(100)))
