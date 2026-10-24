"""Compare completed feedback evaluations at exactly matched terminal voltages."""
import hashlib
import json
from pathlib import Path
import numpy as np


def compare(reference, candidate):
    a = json.loads(reference.read_bytes())
    b = json.loads(candidate.read_bytes())
    if a['voltage_v'] != b['voltage_v']:
        raise ValueError('Comparison requires identical terminal voltages')
    differences = {}
    for name, left, right in (
        ('site_potential_v', a['feedback']['site_potential_v'], b['feedback']['site_potential_v']),
        ('currents_a', a['feedback']['transport']['currents_a'], b['feedback']['transport']['currents_a']),
        ('electrons_per_site', a['feedback']['transport']['electrons_per_site'], b['feedback']['transport']['electrons_per_site']),
    ):
        left, right = np.asarray(left), np.asarray(right)
        if left.shape != right.shape or not np.isfinite(left).all() or not np.isfinite(right).all():
            raise ValueError('Incompatible or nonfinite evidence')
        differences[name] = float(np.max(abs(left-right)))
    return dict(reference=str(reference), candidate=str(candidate),
                reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                voltage_v=a['voltage_v'], max_absolute_difference=differences)


if __name__ == '__main__':
    base = Path('runs/loaded-feedback-pilot-poles-131072')
    cached = base.with_name(base.name+'-cached')
    rows = [compare(base/'evaluation-001.json', cached/'evaluation-001.json'),
            compare(base/'evaluation-004.json', cached/'evaluation-002.json')]
    out = Path('results/physics-reference/loaded-inner-audit/cached-first-two.json')
    out.write_text(json.dumps(dict(scope='Matched completed points only; cached outer solve and runtime benefit pending', comparisons=rows), indent=2)+'\n', encoding='utf-8')
    print(json.dumps(rows, indent=2))
