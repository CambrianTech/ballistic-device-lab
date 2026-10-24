"""Refine overlooked top and median candidates per family to audit screening."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
from ballistic_lab.pipeline.dc_continuous import save, status, task
from ballistic_lab.pipeline.fresh_discovery import qualified


def select(rows):
    selected=[]
    for family in sorted({r['candidate']['family'] for r in rows}):
        pending=sorted([r for r in rows if r['candidate']['family']==family and not qualified(r)],key=lambda r:(-r['levels'][0]['dc_power_w'],r['candidate']['key']))
        if pending:
            for rank in sorted({0,len(pending)//2}):
                selected.append(dict(family=family,pending_rank=rank+1,pending_count=len(pending),row=pending[rank]))
    return selected


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('snapshot',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    s=json.loads(a.snapshot.read_text());selection=select(s['rows'])
    a.output.mkdir(parents=True,exist_ok=False);(a.output/'spectra').mkdir()
    save(a.output/'manifest.json',dict(snapshot=str(a.snapshot),snapshot_sha256=hashlib.sha256(a.snapshot.read_bytes()).hexdigest(),selection=selection,source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('ballistic_lab').rglob('*.py') if 'reporting' not in p.parts},purpose='Top and median unqualified per family; diagnostic sample, not unbiased false-negative estimate'))
    for item in selection:
        key=item['row']['candidate']['key'];shutil.copy2(a.snapshot.parent/'spectra'/(key+'.json.gz'),a.output/'spectra'/(key+'.json.gz'))
    rows=[];status(a.output,phase='refine',remaining=len(selection))
    try:
        with ProcessPoolExecutor(max_workers=2) as pool:
            futures={pool.submit(task,item['row']['candidate'],a.output/'spectra',True):item for item in selection}
            for future in as_completed(futures):
                item=futures[future];r=future.result();rows.append(dict(family=item['family'],pending_rank=item['pending_rank'],before=item['row'],after=r))
                save(a.output/'results.json',rows);status(a.output,phase='refine',completed=len(rows),remaining=len(selection)-len(rows))
        status(a.output,phase='complete',completed=len(rows))
    except Exception as exc:
        status(a.output,phase='failed',error=repr(exc),completed=len(rows));raise
if __name__=='__main__':main()
