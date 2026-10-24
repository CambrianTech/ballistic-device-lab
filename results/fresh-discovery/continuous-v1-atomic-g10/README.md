# Are new proposals actually different atomic devices?

All **20 candidates in completed generation 10** produce distinct atomic
lattices under the fixed search builder. None collapse to an exact duplicate
within this generation when compared by carbon site identities, graph edges,
and lead interfaces. This checks the discretized devices rather than polygon
names or parameter vectors.

The audit rebuilds geometry only; it does not recompute transport or affect
selection. The immutable snapshot hash and per-candidate atomic hashes are in
`result.json`. Reproduce with a fresh output path:

```sh
python -m ballistic_lab.reporting.atomic_diversity_audit runs/fresh-discovery-continuous-v1/round-000010.json results/fresh-discovery/continuous-v1-atomic-g10/result.json
```

This rules out exact within-generation lattice duplication for this sample.
It does not establish distinct electrical responses, diversity relative to
all earlier generations, physical validation, or literature novelty. The
continuous search and independent publisher remained live during the audit.
