"""Matched control, retained champion and fresh campaign best from run receipts."""
import json
import os
import subprocess
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from ballistic_lab.reporting.evolution_story import eligible


def draw(ax, candidate, color):
    ax.set(xlim=(-1.1,1.1),ylim=(-1.1,1.1),aspect='equal');ax.axis('off')
    ax.add_patch(Rectangle((-1,-1),2,2,facecolor='#20374c',edgecolor='#849aae'))
    for poly in candidate['obstacles']:ax.add_patch(Polygon(poly,facecolor='#0c1725',edgecolor=color,lw=1.5))
    for x,y in [([-.3,.3],[1,1]),([-.3,.3],[-1,-1]),([-1,-1],[-.3,.3]),([1,1],[-.3,.3])]:ax.plot(x,y,color=color,lw=4)


def render(options):
    root=Path(options['root']);snapshots=sorted(root.glob('round-*.json'))
    source=snapshots[-1] if snapshots else root/'state.json'
    if not source.exists(): return dict(markdown='Fresh campaign preparing its benchmark records.',evidence={})
    state=json.loads(source.read_text());rows=state['rows'] if snapshots else []
    qualified=[r for r in rows if eligible(r)]
    current=max(qualified,key=lambda r:r['phase64']['dc_power_w']) if qualified else None
    cards=[('SYNTHETIC CONTROL',state['control']),('RETAINED CHAMPION',state['retained_champion']),('CURRENT CAMPAIGN BEST',current)]
    fig,axes=plt.subplots(1,3,figsize=(12,4.7),facecolor='#0c1725')
    for ax,(title,row),color in zip(axes,cards,['#9bb5cd','#ffc76b','#55dfc5']):
        ax.axis('off');ax.set_title(title,color=color,fontsize=12,pad=15)
        if row:
            draw(ax,row['candidate'],color)
            ax.text(.5,-.09,f"{abs(row['phase64']['dc_v'])*1e6:.3f} µV DC",transform=ax.transAxes,color='white',ha='center',fontsize=15)
            ax.text(.5,-.21,row['candidate']['family'].title()+' • converged',transform=ax.transAxes,color='#a8bacf',ha='center',fontsize=10)
        else:ax.text(.5,.5,'Searching new shapes\nAwaiting converged result',transform=ax.transAxes,color='#a8bacf',ha='center',va='center',fontsize=13)
    fig.subplots_adjust(left=.025,right=.975,top=.83,bottom=.22,wspace=.2)
    out=Path('results/live');out.mkdir(parents=True,exist_ok=True)
    fig.savefig(out/'campaign.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)
    proposals=sorted(root.glob('proposals-*.json')); attempts=[]
    if proposals:
        candidates=json.loads(proposals[-1].read_text())
        attempts=[next(c for c in candidates if c['family']==f) for f in sorted({c['family'] for c in candidates})]
        fig,axes=plt.subplots(1,len(attempts),figsize=(3*len(attempts),3.7),facecolor='#0c1725',squeeze=False)
        for ax,c in zip(axes[0],attempts):
            draw(ax,c,'#55dfc5');ax.set_title(c['family'].title(),color='white');ax.text(.5,-.08,'Proposed • unranked',transform=ax.transAxes,ha='center',color='#a8bacf',fontsize=10)
        fig.subplots_adjust(left=.02,right=.98,top=.85,bottom=.16);fig.savefig(out/'campaign-attempts.png',dpi=150,facecolor=fig.get_facecolor());plt.close(fig)
    # Reuse the atomic renderer only for this fixed-potential campaign model.
    # Cache by complete input records; never leave an old image labeled as current.
    atomic_rows=[state['control'],state['champion']]
    atomic_input=out/'atomic-comparison-input.json'
    payload=json.dumps(atomic_rows,sort_keys=True)
    runtime=Path(os.environ.get('BALLISTIC_KWANT_PYTHON','../ballistic-quantum-runtime/env/python.exe')).resolve()
    atomic_body='Atomic rendering unavailable: configure `BALLISTIC_KWANT_PYTHON` for this checkout.'
    if runtime.exists():
        if not atomic_input.exists() or atomic_input.read_text(encoding='utf-8')!=payload or not (out/'atomic-comparison.png').exists():
            atomic_input.write_text(payload,encoding='utf-8')
            env=os.environ.copy()
            env['PATH']=str(runtime.parent)+os.pathsep+str(runtime.parent/'Library/bin')+os.pathsep+env.get('PATH','')
            env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
            try:
                subprocess.run([str(runtime),'-m','ballistic_lab.reporting.atomic_view',str(out),'comparison'],env=env,check=True,timeout=120)
            except Exception:
                atomic_input.unlink(missing_ok=True)
                raise
        atomic_body='![Atomic lattices of the synthetic control and strongest qualified champion](results/live/atomic-comparison.png)\n\n**Same material. Same drive. Evolving geometry.** This image follows the strongest qualified champion in the configured campaign, including its retained benchmark. Bright dots are simulated carbon sites; black openings are etched voids. Scores and lattice geometry come from saved records.'
    # Return the hero as a second generated block alongside the campaign gallery.
    config=json.loads((root/'config.json').read_text())
    fraction=config.get('champion_fraction',0)
    body=f'**One benchmark. A fresh population. A champion to beat.**\n\n![Synthetic control, retained champion, and best converged design from this campaign](results/live/campaign.png)\n\nChampion descendants: **{fraction:.0%} of proposals**. Completed generation: **{state["round"] if snapshots else "pending"}**. Only energy- and phase-converged designs enter the comparison. The retained benchmark is preserved; improved qualified winners become parents for subsequent generations. [Model and search methodology](docs/FRESH_DISCOVERY.md).'
    if proposals:
        children=sum(c.get('proposal_strategy')=='champion' for c in candidates)
        body+=f'\n\nLatest proposal batch: **{len(candidates)} shapes**, including **{children} champion descendants**. Completed matched snapshots: **{len(snapshots)}** (generation labels start at zero).'
    if attempts:body+='\n\n**Shapes being explored now** — one recorded proposal per family, not selected for score.\n\n![Current diverse geometry proposals](results/live/campaign-attempts.png)'
    body+='\n\n[Machine-readable selection and run evidence](results/live/evidence.json) · [Run your own campaign](docs/FRESH_DISCOVERY.md).'
    return dict(markdown=body,blocks={'atomic-hero':atomic_body},evidence=dict(source=source.as_posix(),completed_snapshot=bool(snapshots),control=state['control'],retained=state['retained_champion'],current=current,champion=state['champion'],attempts=attempts))
