"""Plot saved mesh sensitivity without running transport or changing scores."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .compare_width_mesh import validate_dimensions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    records = [json.loads(p.read_text()) for p in args.records]
    for record in records:
        validate_dimensions(record)
        if len(record['rows']) != 1:
            raise ValueError('One mesh per record required')
        for key in ('sigma_m', 'cutoff_sigma', 'positions_m', 'source_sha256'):
            if record[key] != records[0][key]:
                raise ValueError(f'Mismatched {key}')
    rows = sorted((r['rows'][0] for r in records), key=lambda r: r['spacing_m'][0])
    for row in rows:
        for axis in range(3):
            extent = (row['shape'][axis]-1)*row['spacing_m'][axis]
            reference = (rows[0]['shape'][axis]-1)*rows[0]['spacing_m'][axis]
            if abs(extent-reference) > 1e-20:
                raise ValueError('Mismatched physical domain')
    h = [r['spacing_m'][0]*1e9 for r in rows]
    current = [1e12*(r['transport']['currents_a'][0]-rows[0]['transport']['currents_a'][0]) for r in rows]
    potential = [1e3*max(abs(a-b) for a,b in zip(r['potential_v'], rows[0]['potential_v'])) for r in rows]
    with plt.style.context('dark_background'):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
        for ax, values, label in zip(axes, (current, potential), ('Current difference (pA)', 'Maximum site-potential difference (mV)')):
            ax.plot(h, values, 'o-', color='#54d6c1')
            ax.set(xlabel='Mesh spacing (nm)', ylabel=label, xticks=h)
            ax.grid(alpha=.2)
        fig.suptitle('Charge feedback settles as the mesh is refined')
        fig.text(.5, .025, 'Differences from finest saved mesh; 15-site fixture, 0.11 nm cloud width. Not an error bound or physical validation.', ha='center', fontsize=8)
        fig.tight_layout(rect=(0, .07, 1, .94))
        with args.output.open('xb') as stream:
            fig.savefig(stream, format='png', dpi=160)
        plt.close(fig)


if __name__ == '__main__':
    main()
