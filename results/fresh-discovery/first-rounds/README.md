# Fresh campaign: first completed generations

Through generation 3 (zero-indexed), 100 new candidates have been evaluated; 5 passed energy and phase convergence.

| Benchmark | DC magnitude (µV) |
| --- | ---: |
| Synthetic control | 11.205 |
| Retained champion | 28.331 |
| Fresh campaign best | 10.677 |

The fresh population has not beaten the control or retained champion. All saved
champion decisions in this audit match the strongest convergence-qualified
candidate or retained benchmark. Candidate identities are unique within each
snapshot. This audits bookkeeping, not independent physics.

Conditions remain fixed-potential graphene transport at 14.76 nm, 10 mV peak,
10 kohm and 300 K. Results do not establish physical validation or novelty.
The ongoing pipeline updates the main gallery from completed snapshots; this
report freezes the first observations. Source hashes and selected rows are in
`audit.json`.

Reproduce with a new output path:

```sh
python -m ballistic_lab.reporting.audit_fresh_campaign runs/fresh-discovery-20261024 audit-new.json
```
