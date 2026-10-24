# Completed mixed exploration campaign

The campaign finished 20 generations (0–19), evaluating **420 candidates**. **40 passed both energy and phase convergence checks**. Independent replay of champion selection passed for every completed snapshot: the retained champion was never replaced by an unqualified or weaker candidate.

The strongest new design, `r0-beveled-g5-0`, came from **fresh global exploration**, not mutation. Its converged voltage magnitude is **19.699 µV**, with **0.03880 pW** delivered load power: about **3.09× the matched control**. The historical champion remains ahead at **28.331 µV / 0.08026 pW**.

The winning proposal was generated during a diversity-labelled generation, but its origin is fresh global. That label alone does not attribute the improvement to diversity selection. This run also changed the seed and corrected refinement allocation relative to the preceding campaign; it is not a controlled comparison of search strategies.

The result supports retaining fresh exploration alongside inherited candidates. It does not demonstrate physical novelty or calibrated device performance. All scores use the fixed-potential transport model; the separate charge/Poisson fixtures are not part of this scoring model.

## Reproduce the integrity audit

```sh
python -m ballistic_lab.reporting.audit_fresh_campaign runs/fresh-discovery-mixed-v2 new-audit.json
```

[audit.json](audit.json) contains the 20 immutable snapshot hashes, candidate counts, qualified winners, retained champion and matched control. The audit rejects duplicate candidate IDs or a champion that differs from the best qualified candidate plus retained incumbent.

The worker reached its configured limit and exited normally at 2026-10-24 18:09:00 UTC. Its checkpoints remain intact. The original continuous campaign's STOP remains in place, and the dynamic publisher continues independently.
