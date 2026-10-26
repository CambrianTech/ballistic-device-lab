"""Render the latest generation and retain a champion per exact model manifest."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle


def eligible(row):
    return bool(row.get('energy_converged') and row.get('phase_converged') and row.get('phase64'))


def select(snapshot):
    rows = [r for arm in snapshot['histories'].values() for r in arm]
    latest = [r for r in rows if r['candidate']['round'] == snapshot['round']]
    families = sorted({r['candidate']['family'] for r in latest})
    attempts = [max((r for r in latest if r['candidate']['family']==f), key=lambda r:r['levels'][0]['dc_power_w']) for f in families]
    champions = [r for r in rows if eligible(r)]
    return attempts, max(champions,key=lambda r:r['phase64']['dc_power_w']) if champions else None


def render(options):
    paths = sorted(Path('.').glob(options['snapshots']))
    if not paths:
        return dict(markdown='No completed generations in this checkout yet.',evidence={})
    path = paths[-1]; snapshot = json.loads(path.read_text(encoding='utf-8'))
    attempts, champion = select(snapshot)
    manifest = path.parent/'source.json'
    if not manifest.exists():
        raise ValueError('Campaign source manifest required')
    model = hashlib.sha256(manifest.read_bytes()+snapshot['objective'].encode()).hexdigest()
    out = Path('results/live');out.mkdir(parents=True,exist_ok=True)
    ledger_path=out/'champions.json'
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    old=ledger.get(model)
    if champion and (not old or champion['phase64']['dc_power_w']>old['candidate']['phase64']['dc_power_w']):
        ledger[model]=dict(candidate=champion,source=path.as_posix(),objective=snapshot['objective'])
    ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
    lookup={r['candidate']['key']:r for arm in snapshot['histories'].values() for r in arm}
    fig,axes=plt.subplots(2,max(1,len(attempts)),figsize=(3*max(1,len(attempts)),6.6),squeeze=False)
    for col,row in enumerate(attempts):
        c=row['candidate']; origin=c.get('origin','')
        parent=lookup.get(origin.removeprefix('mutation of ')) if origin.startswith('mutation of ') else None
        for y,item in enumerate((parent,row)):
            ax=axes[y,col];ax.set(xlim=(-1.05,1.05),ylim=(-1.05,1.05),aspect='equal');ax.axis('off')
            if item:
                ax.add_patch(Rectangle((-1,-1),2,2,fill=False,edgecolor='#334b62'))
                for polygon in item['candidate']['obstacles']:
                    ax.add_patch(Polygon(polygon,color='#087f8c' if y else '#a9bac7'))
                for x1,x2,y1,y2 in [(-.3,.3,1,1),(-.3,.3,-1,-1),(-1,-1,-.3,.3),(1,1,-.3,.3)]: ax.plot([x1,x2],[y1,y2],color='#e69b2d',lw=3)
                ax.set_title(('Parent' if not y else c['family'].title()),fontsize=12)
                score=item['levels'][0]['dc_v']*1e6
                ax.text(.5,-.04,f'{score:+.3f} µV screening',transform=ax.transAxes,ha='center',fontsize=10)
            else:
                ax.text(.5,.5,'Fresh sample\n(no mutation parent)',transform=ax.transAxes,ha='center',va='center',color='#667788')
        axes[1,col].text(.5,-.16,'Converged' if eligible(row) else 'Screening only',transform=axes[1,col].transAxes,ha='center',fontsize=9)
    fig.suptitle(f'Generation {snapshot["round"]} · parents → new attempts',fontsize=17)
    fig.text(.5,.015,'Best screening attempt per family in this generation · fixed-potential model · etched regions in color',ha='center',fontsize=10)
    fig.subplots_adjust(left=.025,right=.985,bottom=.13,top=.88,hspace=.55,wspace=.18);fig.savefig(out/'generation.png',dpi=150);plt.close(fig)
    record=ledger.get(model)
    title = (f'**Champion to beat: {abs(record["candidate"]["phase64"]["dc_v"])*1e6:.3f} µV DC.** ' if record else '**No converged champion yet.** ')
    body=title+f'Archived three-arm study -- completed generation: **{snapshot["round"]}**. The champion survives restarts; records from different source manifests remain separate.\n\n![Parents and latest diverse attempts](results/live/generation.png)\n\nThe strip selects new attempts by screening score within each family, not by visual preference. Parent links come from recorded mutation origins; fresh samples have no parent. [Selection evidence](results/live/evidence.json) · [Champion ledger](results/live/champions.json).'
    return dict(markdown=body,evidence=dict(snapshot=path.as_posix(),snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),model=model,selected=attempts,champion=record))
