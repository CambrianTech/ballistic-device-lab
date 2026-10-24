# Continuous discovery: first completed generation

The new seed evaluated **40 candidates**, eight each from triangle, beveled,
profile, islands and radial families. Two candidates passed both numerical
convergence gates. The strongest is `r0-beveled-g0-2`: **9.657396 µV DC magnitude**,
with power **9.32653e-15 W**. It does not beat the retained **28.330774 µV** champion.

The immutable round audit confirms unique candidate identities and that the
stored champion is exactly the highest-power eligible record including the
retained benchmark. The first family-refinement target is beveled, so both
initial refinements happened in that family; subsequent targets rotate. Screening
coverage across five families must not be mistaken for five-family convergence
validation. All other candidates remain unqualified, not physically disproven.

The worker has advanced to generation 1; this receipt describes completed
generation 0 only. Automatic publication follows the run every five minutes.
The audit includes the source snapshot SHA-256 and complete selected records.

Reproduce with a fresh output path:

```sh
python -m ballistic_lab.reporting.audit_fresh_campaign runs/fresh-discovery-continuous-v1 results/fresh-discovery/continuous-v1-initial/audit.json
```

This is fixed-potential simulated DC at the existing operating point, not
self-consistent charge feedback, physical validation, or a novelty claim.
