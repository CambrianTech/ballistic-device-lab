"""Summarize completed small-feedback pairs with residuals and provenance."""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args(); status=json.loads((a.run/'status.json').read_text())
    rows=[]
    for entry in status['completed']:
        if entry['phase']!='complete':
            rows.append(entry);continue
        source=a.run/(entry['name']+'.json');data=json.loads(source.read_text())
        evaluations=data['evaluations']
        if len(evaluations)!=2 or evaluations[0]['voltage_v']!=[.005,-.005,0.,0.] or evaluations[1]['voltage_v']!=[-.005,.005,0.,0.]:
            raise ValueError('Expected matched opposite bias pair')
        currents=[r['feedback']['transport']['currents_a'] for r in evaluations]
        even=sum(c[2]-c[3] for c in currents)/2
        rows.append(dict(name=entry['name'],phase='complete',sites=data['sites'],device=data['device'],
            even_transverse_current_difference_a=even,
            max_current_sum_residual_a=max(abs(sum(c)) for c in currents),
            final_feedback_residuals=[r['feedback']['history'][-1] for r in evaluations],
            integration_errors=[r['feedback']['transport']['integration_error'] for r in evaluations],
            source=source.as_posix(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    control=next(r for r in rows if r['name']=='empty-control')
    for r in rows:
        if r['phase']=='complete':r['magnitude_ratio_to_control']=abs(r['even_transverse_current_difference_a']/control['even_transverse_current_difference_a'])
    with a.output.open('x',encoding='utf-8') as f:
        json.dump(dict(scope='Grounded transverse terminals; two-bias even current, not loaded power or cycle average. Uncalibrated; refinement unresolved.',rows=rows),f,indent=2,allow_nan=False)
if __name__=='__main__':main()
