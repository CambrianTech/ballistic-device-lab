"""Fresh seeded discovery: propose, score, refine, retain, snapshot. No AI required."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from ballistic_lab.pipeline.dc_continuous import save, single_worker, status, task, finalists
from ballistic_lab.search.dc_space import WideDCPlan, proposals
from ballistic_lab.search.champion_archive import select_parents, import_history


def qualified(row):
    return bool(row.get('energy_converged') and row.get('phase_converged') and row.get('phase64'))


def choose_champion(retained, rows):
    return max([retained]+[r for r in rows if qualified(r)],key=lambda r:r['phase64']['dc_power_w'])


def refinement_queue(rows, policy='score', generation=0):
    """Keep exploitation while optionally rotating a family exploration slot."""
    pending = [r for r in rows if not qualified(r)]
    if policy == 'score':
        return finalists(pending)
    if policy != 'family':
        raise ValueError('Unknown refinement policy')
    if not pending:
        return []
    ranked = sorted(pending, key=lambda r: (-r['levels'][0]['dc_power_w'], r['candidate']['key']))
    first = ranked[0]
    families = sorted({r['candidate']['family'] for r in rows})
    target = families[generation % len(families)]
    remaining = [r for r in ranked if r is not first]
    second = next((r for r in remaining if r['candidate']['family'] == target), None)
    return [first] + ([second or remaining[0]] if remaining else [])

def strategy_for(mode, generation):
    if mode == 'mixed':
        return ('elite', 'diversity', 'random')[(max(1, generation)-1) % 3]
    if mode not in ('elite', 'diversity', 'random'):
        raise ValueError('Unknown proposal strategy')
    return mode


def champion_offspring(items, champion, fraction, seed, generation):
    """Replace a bounded share of proposals, retaining global exploration."""
    import numpy as np
    from ballistic_lab.search.broad_champion import broad_child
    if not 0 <= fraction <= .5:
        raise ValueError('Champion fraction must be between zero and one half')
    parents = champion if isinstance(champion, list) else [champion]
    if not parents or not all(qualified(r) for r in parents):
        raise ValueError('Champion must pass energy and phase convergence')
    count = int(len(items)*fraction)
    result = list(items)
    if not count:
        return result
    rng = np.random.default_rng(np.random.SeedSequence([seed, generation, 725]))
    # Prefer mutation slots; rotate replacements so no family always loses them.
    slots = [i for i,c in enumerate(items) if c['origin'] != 'fresh global']
    if len(slots) < count:
        slots = list(range(1,len(items),2))
    slots = list(np.roll(slots, generation % len(slots)))[:count]
    accepted = []
    for j, slot in enumerate(slots):
        parent = parents[(generation*count+j) % len(parents)]['candidate']
        child = broad_child(parent, rng, accepted)
        if child is None:
            continue
        result[slot] = dict(key=f'champion-g{generation}-{j}',
            repeat=items[slot]['repeat'], round=generation,
            origin=f"mutation of {parent['key']}", parent_key=parent['key'],
            proposal_strategy='champion', **child)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--seed',type=int,default=241026)
    p.add_argument('--rounds',type=int,default=20)
    p.add_argument('--continuous',action='store_true',help='Continue generations until this run receives STOP')
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--strategy',choices=['elite','diversity','random','mixed'],default='diversity')
    p.add_argument('--ledger',type=Path,default=Path('results/live/champions.json'))
    p.add_argument('--reference-manifest',type=Path,default=Path('runs/dc-continuous/source.json'))
    p.add_argument('--controls',type=Path,default=Path('results/2026-10-22-dc-wide/summary.json'))
    p.add_argument('--refinement-policy', choices=['score','family'], default='score')
    p.add_argument('--champion-fraction', type=float, default=0.0)
    p.add_argument('--champion-capacity', type=int, default=5)
    p.add_argument('--champion-distance', type=float, default=.2)
    p.add_argument('--seed-archive', type=Path)
    args=p.parse_args()
    if args.rounds<1 or args.workers<1: raise ValueError('Positive rounds and workers required')
    if not 0 <= args.champion_fraction <= .5: raise ValueError('Champion fraction must be in [0, .5]')
    if args.champion_capacity < 1 or not 0 < args.champion_distance <= 1:
        raise ValueError('Positive champion capacity and distance in (0, 1] required')
    args.root.mkdir(parents=True,exist_ok=True)
    with single_worker(args.root):
        files=[x for x in Path('ballistic_lab').rglob('*.py') if 'reporting' not in x.parts]
        files += list(Path('device_harness').rglob('*.py'))
        hashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in files}
        manifest=args.root/'source.json'
        if manifest.exists() and json.loads(manifest.read_text())!=hashes: raise ValueError('Source changed; use a new campaign')
        save(manifest,hashes)
        config=dict(seed=args.seed,rounds=args.rounds,workers=args.workers,strategy=args.strategy)
        if args.continuous: config['continuous']=True
        if args.refinement_policy != 'score': config['refinement_policy']=args.refinement_policy
        if args.champion_fraction: config['champion_fraction']=args.champion_fraction
        config.update(champion_capacity=args.champion_capacity, champion_distance=args.champion_distance)
        if args.seed_archive:
            config['seed_archive']=str(args.seed_archive)
            config['seed_archive_sha256']=hashlib.sha256(args.seed_archive.read_bytes()).hexdigest()
        cfg=args.root/'config.json'
        if cfg.exists() and json.loads(cfg.read_text())!=config: raise ValueError('Resume configuration mismatch')
        save(cfg,config)
        statepath=args.root/'state.json'
        if statepath.exists(): state=json.loads(statepath.read_text())
        else:
            old=json.loads(args.reference_manifest.read_text())
            physics=[k for k in old if any(s in k.replace('\\','/') for s in ('/transport/','/geometry/','/experiments/dc_search.py','/experiments/coverage.py','/pipeline/contracts.py'))]
            if not physics or any(hashes.get(k)!=old[k] for k in physics): raise ValueError('Retained benchmark physics mismatch; re-evaluate before comparison')
            ledger=json.loads(args.ledger.read_text())
            records=[r for r in ledger.values() if qualified(r['candidate']) and (Path(r['source']).parent/'source.json').read_bytes()==args.reference_manifest.read_bytes()]
            if not records: raise ValueError('No compatible retained champion')
            champion=max((r['candidate'] for r in records),key=lambda r:r['phase64']['dc_power_w'])
            control=next(r for r in json.loads(args.controls.read_text()) if r['candidate']['key']=='D00')
            state=dict(round=0,rows=[],champion=champion,retained_champion=champion,control=control,objective='DC power at fixed 10 mV peak and 10 kohm',physics_verified=physics)
            state['parent_history'] = [champion]
            if args.seed_archive:
                state['parent_history'] += import_history(args.seed_archive, {k:hashes[k] for k in physics}, state['objective'])
            state['champion'] = choose_champion(champion, state['parent_history'])
            state['parent_archive'] = select_parents(state['parent_history'],args.champion_capacity,args.champion_distance)
            save(statepath,state)
        (args.root/'spectra').mkdir(exist_ok=True)
        plan=replace(WideDCPlan(),seeds=(args.seed,args.seed+100),parent_strategy='diversity',mutation_floor=.04)
        try:
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                while (args.continuous or state['round']<args.rounds) and not (args.root/'STOP').exists():
                    index=state['round']; path=args.root/f'proposals-{index:06d}.json'
                    if path.exists(): items=json.loads(path.read_text())
                    else:
                        round_plan=replace(plan,parent_strategy=strategy_for(args.strategy,index))
                        items=[dict(c,proposal_strategy=round_plan.parent_strategy) for repeat in range(2) for c in proposals(round_plan,repeat,index,state['rows'])]
                        items=champion_offspring(items,state['parent_archive'],args.champion_fraction,args.seed,index)
                        save(path,items)
                    known={r['candidate']['key']:r for r in state['rows']}
                    status(args.root,phase='screen',round=index)
                    futures={pool.submit(task,c,args.root/'spectra',False):c for c in items if c['key'] not in known}
                    for future in as_completed(futures):
                        r=future.result();known[r['candidate']['key']]=r;state['rows']=list(known.values());save(statepath,state)
                        status(args.root,phase='screen',round=index,last_completed=r['candidate']['key'])
                    status(args.root,phase='refine',round=index)
                    for r in refinement_queue(state['rows'], args.refinement_policy, index):
                        if not qualified(r):
                            refined=pool.submit(task,r['candidate'],args.root/'spectra',True).result()
                            known[refined['candidate']['key']]=refined
                    state['rows']=list(known.values());state['champion']=choose_champion(state['champion'],state['rows'])
                    state['parent_archive']=select_parents(state['parent_history']+state['rows'],args.champion_capacity,args.champion_distance)
                    save(args.root/f'round-{index:06d}.json',state)
                    state['round']+=1;save(statepath,state)
            status(args.root,phase='stopped' if (args.root/'STOP').exists() else 'complete',round=state['round'])
        except Exception as exc:
            status(args.root,phase='failed',round=state['round'],error=repr(exc));raise

if __name__=='__main__': main()
