import copy
import unittest
from ballistic_lab.search.champion_archive import select_parents
from ballistic_lab.search.champion_archive import import_history
import tempfile
import json
from pathlib import Path


def row(key, x, power, converged=True):
    return dict(candidate=dict(key=key, obstacles=([[[x,-.3],[x+.2,-.3],[x+.2,.3],[x,.3]]] if x < 0 else [[[x,-.3],[x+.1,.3],[x+.2,-.3]]])),
                energy_converged=converged, phase_converged=converged,
                phase64=dict(dc_power_w=power))


class ArchiveTests(unittest.TestCase):
    def test_import_checks_physics_objective_and_preserves_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'round-000001.json'
            original=row('winner',-.7,10)
            path.write_text(json.dumps(dict(objective='same',rows=[original],champion=original)))
            (path.parent/'source.json').write_text(json.dumps({'solver':'abc'}))
            imported=import_history(path,{'solver':'abc'},'same')
            self.assertEqual(len(imported),1)
            self.assertNotEqual(imported[0]['candidate']['key'],'winner')
            self.assertEqual(imported[0]['archive_provenance']['candidate_key'],'winner')
            self.assertEqual(imported,import_history(path,{'solver':'abc'},'same'))
            with self.assertRaises(ValueError): import_history(path,{'solver':'changed'},'same')
            with self.assertRaises(ValueError): import_history(path,{'solver':'abc'},'other')

    def test_best_per_distinct_shape_and_no_unqualified_parent(self):
        rows=[row('best',-.7,10),row('clone',-.7,9),row('other',.4,8),row('pending',0,100,False)]
        before=copy.deepcopy(rows)
        selected=select_parents(rows,5)
        self.assertEqual([r['candidate']['key'] for r in selected],['best','other'])
        self.assertEqual(selected,select_parents(list(reversed(rows)),5))
        self.assertEqual(rows,before)
        self.assertEqual(len(select_parents(rows,1)),1)

    def test_archive_rebuild_promotes_better_niche_without_losing_other(self):
        rows=[row('old',-.7,10),row('other',.4,8),row('new',-.7,11)]
        self.assertEqual([r['candidate']['key'] for r in select_parents(rows)],['new','other'])

    def test_actual_displayed_lookalikes_share_one_slot(self):
        data=json.loads((Path(__file__).parent/'fixtures/archive-lookalikes.json').read_text())
        rows=[dict(candidate=c,energy_converged=True,phase_converged=True,
                   phase64=dict(dc_power_w=10-i)) for i,c in enumerate(data['candidates'])]
        self.assertEqual(len(select_parents(rows)),1)
        self.assertEqual(select_parents(rows)[0],rows[0])

    def test_translation_and_stretch_do_not_create_niche(self):
        a=row('best',-.7,10)
        b=copy.deepcopy(a);b['candidate']['key']='stretched'
        b['candidate']['obstacles']=[[[x*.5+.6,y*1.3+.1] for x,y in p] for p in a['candidate']['obstacles']]
        b['phase64']['dc_power_w']=9
        self.assertEqual(select_parents([b,a]),[a])

    def test_well_separated_shapes_and_invalid_threshold(self):
        a=row('rectangle',-.7,10)
        b=row('triangle',.4,8)
        b['candidate']['obstacles']=[[[.4,-.3],[.5,.3],[.6,-.3]], [[-.5,.4],[-.4,.7],[-.3,.4]]]
        self.assertEqual(len(select_parents([a,b])),2)
        with self.assertRaises(ValueError): select_parents([a,b],minimum_distance=0)
