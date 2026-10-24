"""Render a saved refinement comparison without hand-entered scores."""
import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input');p.add_argument('output');a=p.parse_args()
    with open(a.input) as f: data=json.load(f)
    arms=data['arms']
    if len(arms)!=2:raise ValueError('Expected two comparison arms')
    labels=['Score-only','Rotating family']
    families=sorted(set().union(*(x['qualified_families'] for x in arms)))
    plt.style.use('dark_background')
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),layout='constrained')
    fig.patch.set_facecolor('#101b2c')
    colors=['#8d9db5','#45d6bd']
    x=np.arange(len(families))
    for i,(arm,label,color) in enumerate(zip(arms,labels,colors)):
        bars=axes[0].bar(x+(i-.5)*.36,[arm['qualified_families'].get(f,0) for f in families],width=.36,label=label,color=color)
        axes[0].bar_label(bars,padding=3)
    axes[0].set_xticks(x,families,rotation=20)
    axes[0].set(ylabel='Numerically qualified designs',title='Which shapes receive accurate evaluation?')
    axes[0].legend(loc='upper right')
    values=[abs(arms[0]['control']['phase64']['dc_v'])*1e6,*[abs(r['best']['phase64']['dc_v'])*1e6 for r in arms],abs(arms[0]['retained']['phase64']['dc_v'])*1e6]
    bars=axes[1].barh(['Control',*labels,'Retained champion'],values,color=['#65738a',*colors,'#f5c267'])
    axes[1].bar_label(bars,fmt='%.2f',padding=4)
    axes[1].set(xlabel='DC voltage magnitude (µV)',title='Best score and retained benchmark',xlim=(0,max(values)*1.2))
    fig.suptitle(f"{data['identical_candidate_records']} identical candidate records | completed generation {arms[0]['round']}",fontsize=15)
    fig.supxlabel('Fixed-potential simulation · one seed · numerical qualification is not physical validation',fontsize=9)
    fig.savefig(a.output,dpi=170)

if __name__=='__main__':main()
