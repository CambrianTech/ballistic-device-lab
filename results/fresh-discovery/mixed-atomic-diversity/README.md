# Do different outlines produce different atomic devices?

For completed generation 9 of the mixed campaign, all **20 proposals produced distinct atomic lattices**. No exact duplicates were found after constructing the actual Kwant systems.

The audit hashes each system's site families and lattice coordinates, graph edges, and lead interfaces. It uses the fixed search lattice builder and performs no transport solve. This checks a specific failure mode: different polygon outlines discretizing into the same device.

This result applies only within this generation. It does not establish electrical diversity, improvement over the retained champion, or physical novelty. Rotated or otherwise symmetry-related devices may also have different hashes.

The snapshot fingerprint and per-candidate fingerprints are in [audit.json](audit.json). Reproduce using the Kwant environment:

```powershell
python -m ballistic_lab.reporting.atomic_diversity_audit runs/fresh-discovery-mixed-v2/round-000009.json audit-replay.json
```

The output path must be new so an existing audit cannot be silently overwritten.
