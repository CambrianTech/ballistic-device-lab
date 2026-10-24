"""Replay a saved pilot evaluation through the geometry adapter, with strict bounds."""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time
import numpy as np
from ballistic_lab.pipeline.contracts import SquareDevice
from .geometry_feedback_model import GeometryFeedbackModel


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference',type=Path)
    parser.add_argument('--output',type=Path,default=Path('runs/geometry-feedback-replay'))
    args=parser.parse_args()
    expected=json.loads(args.reference.read_text(encoding='utf-8'))
    args.output.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    manifest={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('physics_layers').glob('*.py')}
    status=dict(pid=os.getpid(),phase='running',reference=str(args.reference),reference_sha256=hashlib.sha256(args.reference.read_bytes()).hexdigest(),source_sha256=manifest)
    def save():
        status['elapsed_s']=time.monotonic()-started
        (args.output/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    save()
    try:
        device=SquareDevice((),4*.246e-9,contact_width_fraction=.6)
        model=GeometryFeedbackModel(device,max_evaluations=1,max_charge_calls=40,max_seconds=1200)
        result=model.evaluate(expected['voltage_v'])
        actual=asdict(result)
        (args.output/'evaluation.json').write_text(json.dumps(dict(voltage_v=expected['voltage_v'],feedback=actual),default=lambda x:x.tolist(),indent=2),encoding='utf-8')
        checks={}
        for name,a,b,tolerance in [
            ('site_potential_v',result.site_potential_v,expected['feedback']['site_potential_v'],1e-9),
            ('currents_a',result.transport.currents_a,expected['feedback']['transport']['currents_a'],1e-17),
            ('electrons_per_site',result.transport.electrons_per_site,expected['feedback']['transport']['electrons_per_site'],1e-8)]:
            difference=float(np.max(np.abs(np.asarray(a)-np.asarray(b))))
            checks[name]=dict(max_difference=difference,tolerance=tolerance,passed=bool(np.isfinite(difference) and difference<=tolerance))
        status.update(phase='complete' if all(c['passed'] for c in checks.values()) else 'mismatch',checks=checks,charge_calls=model.charge_calls)
    except Exception as exc:
        status.update(phase='failed',error=repr(exc));raise
    finally: save()

if __name__=='__main__': main()
