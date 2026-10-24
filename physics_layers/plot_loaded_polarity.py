"""Plot only completed loaded points; no interpolated I-V curve."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .report_loaded_complete import validate

base=Path('results/physics-reference')
points=[]
for name in ('loaded-feedback-reverse','loaded-feedback-complete'):
    p=base/name
    result=json.loads((p/'result.json').read_text(encoding='utf-8'))
    status=json.loads((p/'completion.json').read_text(encoding='utf-8'))
    checked=validate(status,result)
    points.append((result['drive_v']*1e3,checked['output_v']*1e6))
fig,ax=plt.subplots(figsize=(7.5,4.5),layout='constrained')
ax.axhline(0,color='gray',linewidth=1)
ax.scatter(*zip(*points),s=85,color='#2267a8',zorder=3)
for x,y in points:
    ax.annotate(f'{y:.3f} µV',(x,y),xytext=(0,12),textcoords='offset points',ha='center')
ax.set(xlim=(-13,13),ylim=(-4,0.6),xticks=[-10,0,10],xlabel='Balanced input drive (mV)',ylabel='Loaded output VB − VT (µV)',title='Same output polarity at opposite drives')
ax.grid(alpha=.2)
fig.supxlabel('51-site uncalibrated fixture • 10 kΩ • two points, not sinusoidal DC',fontsize=10)
fig.savefig(base/'loaded-feedback-reverse/polarity.png',dpi=160)
plt.close(fig)
