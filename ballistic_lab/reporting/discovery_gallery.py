"""A data-driven gallery joining retained achievements with active experiments."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def render(options):
    ledger_path = Path(options.get('ledger', 'results/live/champions.json'))
    ledger = read(ledger_path) if ledger_path.exists() else {}
    cards = []
    for model, record in sorted(ledger.items()):
        row = record['candidate']
        cards.append(dict(title='RETAINED CHAMPION', name=row['candidate']['family'].title(),
            obstacles=row['candidate']['obstacles'], contact=.3,
            result=f"{abs(row['phase64']['dc_v'])*1e6:.3f} µV DC",
            detail='Fixed-potential model • converged', model=model,
            source=record['source']))
    paths = sorted(Path('.').glob(options.get('experiments', 'runs/small-feedback-*/status.json')),
                   key=lambda p:p.stat().st_mtime)
    source = None
    if paths:
        source = paths[-1]; state = read(source)
        completed = {r['name']:r for r in state.get('completed', [])}
        for path in sorted(source.parent.glob('*.json')):
            if path.name == 'status.json':
                continue
            try:
                row = read(path)
            except json.JSONDecodeError:
                continue  # Writer may be publishing an evaluation at this instant.
            if 'device' not in row or 'evaluations' not in row:
                continue
            outcome = completed.get(row['name'], {})
            done = outcome.get('phase') == 'complete' and len(row['evaluations']) == 2
            result = (f"{outcome['even_transverse_current_difference_a']*1e12:+.3f} pA even ΔI"
                      if done else 'Evaluation pending' if not outcome else outcome['phase'])
            cards.append(dict(title='COMPLETED PHYSICS CHECK' if done else 'UNRESOLVED PHYSICS CHECK', name=row['name'].replace('-', ' ').title(),
                obstacles=row['device']['obstacles'], contact=row['device']['contact_width_fraction'],
                result=result, detail=f"{row['device']['width_m']*1e9:.3f} nm • charge feedback",
                source=path.as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    out = Path('results/live'); out.mkdir(parents=True, exist_ok=True)
    n = max(2, len(cards))
    fig, axes = plt.subplots(1, n, figsize=(4*n, 4.6), facecolor='#0c1725', squeeze=False)
    for i, ax in enumerate(axes[0]):
        ax.set_facecolor('#0c1725'); ax.set(xlim=(-1.15,1.15), ylim=(-1.15,1.15), aspect='equal'); ax.axis('off')
        if i >= len(cards):
            ax.text(.5,.55,'EXPERIMENT RUNNING' if source else 'READY FOR NEW DESIGNS',color='#55dfc5',ha='center',transform=ax.transAxes,fontsize=12)
            ax.text(.5,.4,'Saved geometries appear here\nas evaluations arrive.',color='#a8bacf',ha='center',transform=ax.transAxes,fontsize=11)
            continue
        card=cards[i]; color='#ffc76b' if card['title']=='RETAINED CHAMPION' else '#55dfc5'
        ax.add_patch(Rectangle((-1,-1),2,2,facecolor='#20374c',edgecolor='#7892a8',lw=1.5))
        for polygon in card['obstacles']:
            ax.add_patch(Polygon(polygon,facecolor='#0c1725',edgecolor=color,lw=1.8))
        c=card['contact']
        for xs,ys in [([-c,c],[1,1]),([-c,c],[-1,-1]),([-1,-1],[-c,c]),([1,1],[-c,c])]:
            ax.plot(xs,ys,color=color,lw=4)
        ax.set_title(card['title']+'\n'+card['name'],color=color,fontsize=12,pad=12)
        ax.text(.5,-.07,card['result'],color='white',ha='center',transform=ax.transAxes,fontsize=13)
        ax.text(.5,-.18,card['detail'],color='#a8bacf',ha='center',transform=ax.transAxes,fontsize=10)
    fig.subplots_adjust(left=.025,right=.975,top=.81,bottom=.22,wspace=.22)
    fig.savefig(out/'discovery.png',dpi=160,facecolor=fig.get_facecolor()); plt.close(fig)
    body='**Keep the best. Explore what changes it.** The retained champion stays in view as new experiment geometries and results arrive.\n\n![Retained champion alongside the latest saved experiment designs](results/live/discovery.png)\n\nShapes are normalized for display. Gold marks retained champions; teal marks new experiments. Different scales and physics have separate scores—this gallery is not a shared ranking. New feedback points measure grounded-terminal current, not loaded DC power. [Live evidence](results/live/evidence.json).'
    if not ledger:
        body='<details>\n<summary>Completed charge-feedback checks — saved reference results</summary>\n\nThese fixtures are completed checks, not the active evolutionary population. See the [current campaign and evolving designs](#current-discovery) above.\n\n![Small-device charge-feedback experiments](results/live/discovery.png)\n\nThese small fixtures test the physics implementation; their current scores are separate from the main loaded-power competition. This image changes only when new charge-feedback geometry results are saved. [Run evidence](results/live/evidence.json).\n\n</details>'
    return dict(markdown=body,evidence=dict(cards=cards,experiment_status=source.as_posix() if source else None))

