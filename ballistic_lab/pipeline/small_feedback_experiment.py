"""Bounded small-geometry feedback comparison, not a loaded-power search score."""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time
import numpy as np
from ballistic_lab.pipeline.contracts import SquareDevice
from physics_layers.geometry_feedback_fixture import geometry_fixture
from physics_layers.geometry_feedback_model import GeometryFeedbackModel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cases = [('empty-control', ()),
             ('triangle-up', (((-.3, -.3), (.3, -.3), (0., .3)),)),
             ('triangle-down', (((-.3, .3), (.3, .3), (0., -.3)),))]
    started = time.monotonic()
    status = dict(pid=os.getpid(), phase='running', completed=[],
                  scope='Uncalibrated 0.984 nm fixture; grounded transverse terminals. No load-power or full-size champion comparison.',
                  source_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [Path(__file__), *Path('physics_layers').glob('*.py')]})
    def save():
        status['elapsed_s'] = time.monotonic() - started
        temporary = args.output / 'status.tmp'
        temporary.write_text(json.dumps(status, indent=2), encoding='utf-8')
        temporary.replace(args.output / 'status.json')
    save()
    fingerprints = set()
    for name, obstacles in cases:
        if (args.output / 'STOP').exists():
            status['phase'] = 'stopped'; save(); return
        status['current'] = name; save()
        try:
            device = SquareDevice(obstacles, 4*.246e-9, .6)
            system, _, _ = geometry_fixture(device, [0]*4)
            lattice = repr([(str(s.family), tuple(s.tag)) for s in system.sites])
            fingerprint = hashlib.sha256(lattice.encode()).hexdigest()
            if fingerprint in fingerprints:
                raise ValueError('Duplicate atomic lattice: shape does not create a distinct experiment')
            fingerprints.add(fingerprint)
            model = GeometryFeedbackModel(device, max_evaluations=2, max_charge_calls=80, max_seconds=3600)
            row = dict(name=name, device=asdict(device), sites=len(system.sites), lattice_sha256=fingerprint, evaluations=[])
            for polarity in (1, -1):
                if (args.output / 'STOP').exists():
                    status['phase'] = 'stopped'; save(); return
                volts = [polarity*.005, -polarity*.005, 0., 0.]
                result = model.evaluate(volts)
                row['evaluations'].append(dict(voltage_v=volts, feedback=asdict(result)))
                (args.output / (name+'.json')).write_text(json.dumps(row, default=lambda x:x.tolist(), indent=2), encoding='utf-8')
            currents = np.array([r['feedback']['transport']['currents_a'] for r in row['evaluations']])
            status['completed'].append(dict(name=name, sites=len(system.sites), phase='complete',
                even_transverse_current_difference_a=float(((currents[0,2]-currents[0,3])+(currents[1,2]-currents[1,3]))/2)))
        except Exception as exc:
            status['completed'].append(dict(name=name, phase='failed', error=repr(exc)))
        save()
    status['phase'] = 'complete' if all(r['phase']=='complete' for r in status['completed']) else 'completed-with-failures'
    save()

if __name__ == '__main__':
    main()
