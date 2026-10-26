# Fresh discovery pipeline

The worker owns proposal generation, scoring, refinement, checkpointing and
champion retention. The publisher consumes its completed snapshots and redraws
the README. Neither step requires an AI or manual score selection.

## Run in your fork

With the Kwant environment active and BLAS limited to one thread:

```sh
python -m ballistic_lab.pipeline.fresh_discovery --root runs/my-campaign --seed 241026 --rounds 20 --workers 4
```

Set the `campaign_gallery` adapter's `root` in `publication.json` to that directory,
then run the existing publication service in another terminal:

```sh
python -m ballistic_lab.reporting.live_project --watch --push
```

Omit `--push` for local generation only. Publication uses the configured remote
and branch, normally your fork's `origin/main`. It checks actual worker liveness,
and refuses to absorb uncommitted README edits. The two processes communicate
through saved data: compute continues if publication fails, and publication never
changes scoring. This is a bounded 20-generation campaign, not a service that
survives a machine reboot.

## What runs automatically

A new seed produces 40 stratified initial designs spanning triangle, beveled,
profile, islands and radial families. Subsequent generations propose 20 designs:
fresh samples plus diversity-guided mutations. The strongest two screening
candidates receive the existing energy/phase refinement. A candidate may replace
the champion only when both convergence checks pass and DC power improves.
This single diversity campaign does not estimate superiority over other search
strategies. Equal candidate budgets are not equal CPU budgets.

The main gallery is control / retained benchmark / current campaign best, all at
14.76 nm width, 10 mV peak drive, 10 kohm load and 300 K with fixed internal
potential. The proposal strip shows one recorded proposal per family, clearly
unranked. Charge-feedback experiments stay in the physics section; their scores
cannot displace this campaign's champion.

## Checkpoints and model compatibility

The default ledger and synthetic control are the repository's published baseline.
Pass `--ledger`, `--controls` and `--reference-manifest` for compatible fork data.
The worker checks reference transport, geometry and scoring hashes before carrying
a champion forward. Different physics must be re-evaluated, not silently compared.
A full source manifest and seed/configuration are recorded in the new run.

Create `STOP` in the new run directory to stop after the active generation.
Resume with the same command and unchanged source/configuration after deliberately
removing that run's STOP. Never remove the old `runs/dc-continuous/STOP` to start
this campaign. Per-run OS locks prevent duplicate workers on the same directory;
operators must also avoid launching overlapping campaigns on limited hardware.
All completed rounds are immutable reporting inputs. Partial rows are checkpoints,
not published champions. The campaign keeps its best in `state.json` and snapshots;
the original champion ledger and historical studies remain intact.

## Mixed proposal strategy

`--strategy mixed` rotates elite, diversity and random parent strategies across
successive feedback generations; every generation still includes fresh global
samples. Each proposal records the strategy that produced it. Available explicit
modes are `elite`, `diversity`, `random`, and `mixed` (default remains diversity).
Refinement slots now go to the strongest unqualified records, so already-converged
leaders cannot consume them. Promotion still requires both convergence gates.

The bounded mixed campaign uses seed 241027 and a fresh run directory. It changes
both seed and strategy, so its outcome is not a controlled estimate of strategy
superiority. It broadens proposal behavior within the existing five geometry
families; it does not add new geometric topology families. Original campaigns,
controls, and champion are retained. The publisher's campaign root points at the
new run so its plots update automatically.

## Refinement exploration

New campaigns may select `--refinement-policy family`. One refinement slot goes to the highest coarse-power unqualified candidate; the second goes to the strongest remaining candidate in a rotating family (alphabetical family order, indexed by generation). If that family has no remaining candidate, the slot returns to the highest remaining score. Qualified rows never consume slots. Default `score` preserves the existing policy.

This changes allocation of the same two candidate slots, not the objective, numerical convergence gates, or champion promotion. It is not an equal-CPU guarantee. The option is saved in campaign configuration and cannot change on resume. Source hashes require a new campaign after this code change. Five focused discovery tests pass, including a low-scoring family's access to refinement. No comparative performance improvement has yet been measured with this policy.

## Sustained discovery

Use `--continuous` to keep proposing and refining generations until the run's
`STOP` file is created. This overrides the generation limit, retains checkpoints
and converged champions, and does not require an AI to schedule more rounds.
It does not auto-start after a machine reboot. Storage grows with saved spectra
and immutable snapshots; monitor free space during long runs.

```sh
python -m ballistic_lab.pipeline.fresh_discovery --root runs/fresh-discovery-continuous-v1 --seed 241029 --continuous --workers 4 --strategy mixed --refinement-policy family
```

Configure the publisher adapter root to follow your selected campaign every five minutes. One refinement
slot exploits coarse power and one rotates across geometry families. Numerical
energy/phase convergence gates remain required for champion promotion. This is
fixed-potential discovery; the separate small charge-feedback checks are not its
fitness function or a claim of physical validation.


## Champion descendants and physics gates
Use `--champion-fraction 0.25` in a fresh run to allocate one quarter of proposals to the strongest qualified champion (initially the retained benchmark). This is five of twenty candidates per later generation, replacing mutation/random slots while preserving all ten global proposals. Replacement slots rotate across families. Initial allocation preserves a global seed population in every family/repeat. Single-obstacle descendants use the full-boundary polygon operator described below. Multi-obstacle descendants redraw half the normalized parameters uniformly, retaining the rest from the parent. A 128 by 128 etched-area mask rejects children changing less than 3.5% of device area or 20% of the parent/child union. Siblings must differ by at least 2% of device area and 15% of their union. These are exploration heuristics, not physical novelty tests. After 256 unsuccessful trials the original proposal keeps the slot. Parent keys, distances and operator are recorded; parents are never modified. Fractions are rounded down to whole candidates. Zero preserves the original proposal policy.
This allocation is fixed, not adaptively inferred from advantage. Four exploratory descendants all converged but none improved on the parent; that small probe does not establish an optimal allocation. `--strategy mixed` rotates elite/diversity/random selection for remaining slots. `--refinement-policy family` spends one refinement slot on coarse power and one on a rotating family. A coarse score is never enough to replace the champion.
The active score remains fixed-potential DC power at 14.76 nm width, 10 mV peak drive, 10 kohm load and 300 K. Small self-consistent charge/3D Poisson fixtures test numerical behavior separately. Boundary-distance tests move normal boundaries with lateral boundaries and mesh spacing fixed; they are not calibrated housing models. Full-device stack validation is required before using that model for champion ranking.
```sh
python -m ballistic_lab.pipeline.fresh_discovery --root runs/fresh-discovery-polygon-v4 --seed 261029 --continuous --workers 4 --strategy mixed --refinement-policy family --champion-fraction 0.25
```
Set the publication adapter root to the same run. Current gallery shapes, scores, generation and offspring allocation come from run records/configuration. Archived figures remain explicitly labeled historical. A policy/source change starts a new directory and preserves prior STOP sentinels and checkpoints.


## Full-boundary descendants

Single-obstacle champion descendants now store explicit polygon vertices rather than forcing them back into a profile template. Each proposal perturbs every vertex (standard deviation 0.07 normalized coordinate units), optionally inserts or deletes a vertex, rotates through a uniformly sampled full circle, scales by 0.8–1.15 and translates each axis by up to 0.16. The saved family is `polygon`, parameters are empty, and `geometry_encoding=explicit-polygons-v1` identifies authoritative vertices. Polygon champions can themselves produce polygon descendants. Existing family-based global proposals and local mutations remain available.

Reject self-intersection/touching nonadjacent edges, edges shorter than 0.04, polygon area below 0.025, and vertices outside [-0.9,0.9]. The interior margin protects boundary contacts; it is a conservative geometric constraint, not fabrication qualification. The prior etched-area difference thresholds also apply. Multi-obstacle parents retain the parameter-redraw operator until a separate overlap/topology contract is implemented. The initial scope changes one obstacle's boundary, not its number of holes or islands. Rejections are bounded at 256 attempts per slot, then the original proposal survives.

Five focused mutation tests cover distance gates, reproducibility, parent preservation, invalid polygons, vertex-count changes and descendant reuse. A one-energy Kwant smoke check constructs all four leads and checks scattering residuals; it is not a convergence or device-performance result. The live campaign performs the unchanged full screening and refinement pipeline before promotion.
