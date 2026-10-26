"""Data-backed publication for a checkout or fork; never starts compute workers."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from datetime import datetime, timezone


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def replace_block(text, name, body):
    pattern = rf'<!-- {name}:start -->.*?<!-- {name}:end -->'
    if len(re.findall(pattern, text, re.S)) != 1:
        raise ValueError('Expected exactly one README block: '+name)
    return re.sub(pattern, lambda _: f'<!-- {name}:start -->\n{body}\n<!-- {name}:end -->', text, flags=re.S)


def processes():
    if os.name == 'nt':
        command = 'Get-CimInstance Win32_Process | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress'
        raw = subprocess.check_output(['powershell','-NoProfile','-Command',command], text=True, timeout=30)
        rows = json.loads(raw)
        return {int(r['ProcessId']): r.get('CommandLine') or '' for r in rows}
    result = {}
    for p in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            result[int(p.parent.name)] = p.read_bytes().replace(b'\0',b' ').decode(errors='replace')
        except OSError:
            pass
    return result


def activity(config, process_map):
    rows = []
    for job in config['workers']:
        for path in sorted(Path('.').glob(job['status_glob'])):
            try:
                status = read(path)
            except (OSError, ValueError):
                continue
            phase = status.get('phase', 'unknown')
            command = process_map.get(status.get('pid'), '')
            alive = bool(re.search(r'(?:^|\s)-m\s+'+re.escape(job['module'])+r'(?:\s|$)', command))
            rows.append(dict(run=path.parent.as_posix(), label=job['label'], phase=phase,
                             live=alive, stopped=(path.parent/'STOP').exists(),
                             status_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return rows


def loaded_points(config):
    from physics_layers.report_loaded_complete import validate
    rows, rejected = [], []
    for path in sorted(Path('.').glob(config['completed_glob'])):
        try:
            status = read(path)
            if status.get('phase') != 'complete':
                continue
            result = read(path.parent/'result.json')
            check = validate(status, result)
            rows.append(dict(run=path.parent.as_posix(), drive_v=result['drive_v'],
                             **check, source_sha256=result['source_sha256']))
        except (OSError, ValueError, KeyError) as exc:
            rejected.append(dict(run=path.parent.as_posix(), error=str(exc)))
    return rows, rejected


def publish(config, process_map=None):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    rows = activity(config, processes() if process_map is None else process_map)
    active = sorted({r['label'] for r in rows if r['live'] and r['phase'] not in ('complete','failed','waiting','stopped')})
    waiting = sorted({r['label'] for r in rows if r['live'] and r['phase']=='waiting'})
    state = 'Computing' if active else ('Workers waiting' if waiting else 'No active computation verified')
    detail = ', '.join(active or waiting) or 'See the evidence snapshot for completed and stopped runs.'
    body = f'**{state} · Updated {now}**\n\n{detail} · [Data snapshot](results/live/evidence.json) · Published every {config["interval_seconds"]//60} minutes while the publisher runs.'
    target = Path('README.md')
    text = replace_block(target.read_text(encoding='utf-8'), 'activity', body)
    points, rejected = loaded_points(config)
    # Each row is independently accepted; distinct source manifests remain visible.
    # This display never silently pairs different models or calculates cross-run parity.
    result_lines = ['| Drive (mV) | Output (µV) | Evidence |','| ---: | ---: | --- |']
    for row in sorted(points, key=lambda r:(r['drive_v'],r['run'])):
        result_lines.append(f'| {row["drive_v"]*1e3:g} | {row["output_v"]*1e6:.6f} | `{Path(row["run"]).name}` |')
    if not points:
        result_lines = ['No completed loaded-feedback points passed the publication checks in this checkout.']
    text = replace_block(text, 'loaded-points', '\n'.join(result_lines)+'\n\nIndividual operating points; source manifests and accounting are retained in the [data snapshot](results/live/evidence.json).')
    if points:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        figure, ax = plt.subplots(figsize=(7.5, 4.5), layout='constrained')
        ax.axhline(0, color='#9aa7b2', lw=1)
        ax.scatter([r['drive_v']*1e3 for r in points], [r['output_v']*1e6 for r in points], color='#087f8c', s=65)
        ax.set(xlabel='Input drive (mV)', ylabel='Output (µV)', title='Completed loaded-feedback operating points')
        ax.grid(alpha=.15)
        figure.supxlabel('Individual accepted solves · see source manifests · no fitted curve or cycle average', fontsize=9)
        Path('results/live').mkdir(parents=True,exist_ok=True)
        figure.savefig('results/live/loaded-points.png',dpi=160)
        plt.close(figure)
    extra = {}
    for spec in config.get('adapters', []):
        module, function = spec['callable'].split(':')
        output = getattr(importlib.import_module(module), function)(spec.get('options', {}))
        text = replace_block(text, spec['block'], output['markdown'])
        for name, body in output.get('blocks', {}).items():
            text = replace_block(text, name, body)
        extra[spec['block']] = output['evidence']
    out = Path('results/live'); out.mkdir(parents=True,exist_ok=True)
    evidence = dict(published_utc=now, workers=rows, loaded_points=points, rejected=rejected, adapters=extra)
    (out/'evidence.json').write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    target.write_text(text,encoding='utf-8')


def git_publish(config):
    paths = ['README.md','results/live']
    # Do not collect unrelated staged files or an editor's uncommitted README.
    subprocess.run(['git','-c','core.autocrlf=false','add','--',*paths],check=True)
    changed = subprocess.run(['git','diff','--cached','--quiet','--',*paths]).returncode
    if changed == 1:
        subprocess.run(['git','-c','core.safecrlf=false','commit','--only','-m','Refresh generated research evidence','--',*paths],check=True)
    elif changed != 0:
        raise RuntimeError('Cannot inspect generated changes')
    subprocess.run(['git','push',config['remote'],'HEAD:'+config['branch']],check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='publication.json')
    parser.add_argument('--watch',action='store_true')
    parser.add_argument('--push',action='store_true',help='Opt in to commits and push to configured fork remote')
    args = parser.parse_args()
    config = read(args.config)
    if config['interval_seconds'] < 60:
        raise ValueError('Publication interval must be at least 60 seconds')
    root = Path('runs/publication'); root.mkdir(parents=True,exist_ok=True)
    with (root/'publisher.lock').open('a+b') as lock:
        lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while not (root/'STOP').exists():
            try:
                if args.push:
                    dirty = subprocess.check_output(['git','status','--porcelain','--','README.md','results/live'],text=True)
                    if dirty.strip():
                        raise RuntimeError('Publication paths have uncommitted edits; preserve them and retry after commit')
                publish(config)
                if args.push:
                    git_publish(config)
                state = dict(pid=os.getpid(),phase='waiting',updated=datetime.now(timezone.utc).isoformat())
            except Exception as exc:
                state = dict(pid=os.getpid(),phase='failed',error=repr(exc))
                if not args.watch:
                    raise
            (root/'status.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
            if not args.watch:
                break
            for _ in range(config['interval_seconds']):
                if (root/'STOP').exists():
                    return
                time.sleep(1)


if __name__ == '__main__':
    main()
