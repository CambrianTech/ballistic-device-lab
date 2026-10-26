"""Rectifier adapter for the reusable distinct-parent archive."""
from device_harness import Evaluation, distinct_champions
from ballistic_lab.search.broad_champion import shape_mask, difference
import numpy as np
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


def normalized_shape_mask(obstacles):
    """Compare outline independently of translation and axis-wise stretching.

    Orientation and relative placement of multiple obstacles remain meaningful.
    This is an archive diversity heuristic, never a transport equivalence.
    """
    polygons = [np.asarray(p, dtype=float) for p in obstacles]
    if not polygons:
        return shape_mask([])
    vertices = np.concatenate(polygons)
    low = vertices.min(axis=0)
    span = vertices.max(axis=0) - low
    if not np.isfinite(vertices).all() or np.any(span <= 0):
        raise ValueError('Invalid archive geometry')
    return shape_mask([(p-low)/span*1.8-.9 for p in polygons])


SHAPE_DISTANCE = .5


def select_parents(rows, capacity=5, minimum_distance=.2):
    """Caller supplies only records from the same verified physics/objective.

    Distance is changed etched area / etched union on the fixed 128Â² grid.
    Empty niches stay empty; qualification is never relaxed to fill the archive.
    """
    if not 0 < minimum_distance <= 1:
        raise ValueError('Minimum distance must be in (0, 1]')
    qualified = [r for r in rows if r.get('energy_converged') and
                 r.get('phase_converged') and r.get('phase64')]
    by_id = {}
    for row in qualified:
        key = row['candidate']['key']
        if key in by_id and by_id[key] != row:
            raise ValueError('Conflicting candidate records in parent history')
        by_id[key] = row
    masks = {key: shape_mask(row['candidate']['obstacles']) for key, row in by_id.items()}
    normalized = {key: normalized_shape_mask(row['candidate']['obstacles']) for key, row in by_id.items()}
    contract = 'fixed-dc-verified-inputs:normalized-outline-128-v2'
    records = [Evaluation(key, contract, row['phase64']['dc_power_w'], True, key)
               for key, row in by_id.items()]
    selected = distinct_champions(records, contract,
        lambda a, b: min(1.0, difference(masks[a], masks[b])[1] / minimum_distance,
                         difference(normalized[a], normalized[b])[1] / SHAPE_DISTANCE),
        capacity, 1.0)
    return [by_id[r.candidate_id] for r in selected]
