# Atomic diversity after 43 generations

All **20 proposals in completed generation 43 produce distinct atomic lattices** under the fixed graphene builder. There are four proposals each from beveled, islands, profile, radial and triangle families, with no exact within-generation duplicate.

The audit rebuilds each device and hashes its site identities, graph edges and lead interfaces. It therefore checks discretized devices rather than relying on different floating-point shape parameters or different candidate names. The immutable snapshot hash and each candidate's atomic hash are retained in `result.json`.

This rules out exact within-generation atomic duplication as the explanation for this batch's unchanged leader. It does not rule out near-duplicate geometries, equivalent transport behavior, repetition across generations, restricted shape families or unsuitable scoring. Distinct lattices do not establish physical novelty or improved performance. No transport solve, live selection change or worker restart was performed.

Reproduce in the Kwant environment with a fresh output filename:

```powershell
python -m ballistic_lab.reporting.atomic_diversity_audit runs/fresh-discovery-continuous-v1/round-000043.json results/fresh-discovery/continuous-v1-atomic-g43/result.json
```
