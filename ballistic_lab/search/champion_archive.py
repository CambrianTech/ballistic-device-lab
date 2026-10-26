"""Rectifier adapter for the reusable distinct-parent archive."""
from device_harness import Evaluation, distinct_champions
from ballistic_lab.search.broad_champion import shape_mask, difference
import copy
import hashlib
import json
from pathlib import Path


def import_history(path, physics_hashes, objective):
    """Import immutable qualified receipts only after physics/objective checks."""
    path = Path(path)
    source = json.loads((path.parent/'source.json').read_text())
    if any(source.get(k) != v for k, v in physics_hashes.items()):
        raise ValueError('Parent archive physics mismatch')
    payload = path.read_bytes()
    state = json.loads(payload)
    if state.get('objective') != objective:
        raise ValueError('Parent archive objective mismatch')
    digest = hashlib.sha256(payload).hexdigest()
    rows = []
    for row in state.get('rows', []) + state.get('parent_history', []) + [state['champion']]:
        if not (row.get('energy_converged') and row.get('phase_converged') and row.get('phase64')):
            continue
        item = copy.deepcopy(row)
        old_key = item['candidate']['key']
        item['candidate']['key'] = 'import-'+digest[:12]+'-'+old_key
        item['archive_provenance'] = dict(source=path.as_posix(), sha256=digest, candidate_key=old_key)
        if item not in rows:
            rows.append(item)
    return rows


def select_parents(rows, capacity=5, minimum_distance=.2):
    """Caller supplies only records from the same verified physics/objective.

    Distance is changed etched area / etched union on the fixed 128² grid.
    Empty niches stay empty; qualification is never relaxed to fill the archive.
    """
    qualified = [r for r in rows if r.get('energy_converged') and
                 r.get('phase_converged') and r.get('phase64')]
    by_id = {}
    for row in qualified:
        key = row['candidate']['key']
        if key in by_id and by_id[key] != row:
            raise ValueError('Conflicting candidate records in parent history')
        by_id[key] = row
    masks = {key: shape_mask(row['candidate']['obstacles']) for key, row in by_id.items()}
    contract = 'fixed-dc-verified-inputs:etched-union-128-v1'
    records = [Evaluation(key, contract, row['phase64']['dc_power_w'], True, key)
               for key, row in by_id.items()]
    selected = distinct_champions(records, contract,
        lambda a, b: difference(masks[a], masks[b])[1], capacity, minimum_distance)
    return [by_id[r.candidate_id] for r in selected]
