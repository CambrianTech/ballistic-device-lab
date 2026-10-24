# Publish your own experiment

The README is a visual narrative with named generated blocks. `publication.json`
selects local runs, worker modules, report adapters, interval and Git destination.
There are no developer-machine paths or hard-coded GitHub owners in the publisher.

```sh
# Preview from this repository's root; no commit or network write.
python -m ballistic_lab.reporting.live_project

# Keep refreshing locally every configured interval.
python -m ballistic_lab.reporting.live_project --watch

# Opt in to publishing to YOUR configured remote and branch.
python -m ballistic_lab.reporting.live_project --watch --push
```

In a fork, set `remote` and `branch` in `publication.json` and check `git remote -v`.
Use an environment with the project dependencies and Matplotlib. Run workers
separately following the architecture contracts; publication never starts or
restarts simulations. Retain the champion ledger when starting a fresh campaign.

Create `runs/publication/STOP` to stop publication; remove it for an explicit
restart. An OS lock prevents duplicate publishers and is released on process exit.
The watcher is a foreground command; a service manager can keep it alive across
machine restarts. It does not install a system service.

## What comes from data

- Activity: local status files plus PID **and module command-line** verification.
  A dead or recycled PID cannot make an experiment look active. Waiting is distinct
  from computing. The timestamp describes publication, not a live browser connection.
- Loaded operating points: completed status, matching source manifests and independent
  current/power/conditioning checks. Rejected inputs are retained in the JSON receipt.
- Latest generation: only completed round files, with best screening attempt per
  family, recorded mutation parent, and explicit convergence labels.
- Champions: retain the strongest converged row per source-manifest/objective key
  in `results/live/champions.json`. A restart cannot replace it with a weaker candidate.
  A different model creates a separate record. This deliberately conservative key
  is not a substitute for matching materials, drive, load and all numerical settings.
- Reference diagrams remain linked to their named immutable reports. They are not
  relabeled as new calculations when only the activity timestamp changes.

Generated files are in `results/live/`; README changes are confined to named
blocks. Unrelated staged files are not committed. Dirty publication paths stop
Git publication rather than absorbing an editor's changes; resolve/commit those
changes before retrying. Failures appear in `runs/publication/status.json`.
A rejected push never triggers a force push or automatic merge.

## Add an experiment

Add a worker's `status_glob`, Python module and label to `workers`. A reporting
adapter is a Python `module:function` entry in `adapters`, with an `options` object
and a matching `<!-- block:start -->` / `<!-- block:end -->` in README.
The function receives options and returns `markdown` plus serializable `evidence`.
It may create figures under `results/live/`. Keep numerical acceptance checks in
the adapter; no generic publisher can decide whether new physics is validated.
A missing/duplicate block or adapter exception fails publication.

The editorial order stays fixed. New results replace the appropriate experiment
panel rather than appending another status section. A control/champion/challenger
comparison requires matched evaluation evidence; no third panel is invented when
there is no distinct qualified challenger.
