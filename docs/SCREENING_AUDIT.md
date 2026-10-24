# Audit whether coarse screening overlooks useful designs

The fresh campaign used one diversity arm rather than the older matched elite,
diversity and random arms. Both use the same five parameterized shape families;
a new seed does not expand the geometry representation. A refinement allocation
bug also left many candidates unchecked; that is now fixed for future campaigns.

The nine converged records in the completed campaign changed by at most
0.161094 µV between coarse and refined voltage. This selected sample cannot
establish that screening is reliable for rejected candidates.

`ballistic_lab.pipeline.screening_audit` takes the strongest unqualified candidate
and the median unqualified candidate within each family, ten total in this run.
It copies cached spectra into a new directory and applies the same refinement
procedure using two workers. Original checkpoints and scores remain unchanged.
Selection is frozen before new evaluations. The sample is diagnostic, not an
unbiased estimate of false negatives or proof of algorithm superiority.

```sh
python -m ballistic_lab.pipeline.screening_audit runs/fresh-discovery-20261024/round-000019.json --output runs/my-screening-audit
```

Output must be new. Manifest, selection, source hashes, results and process status
are saved. This is a finite ten-case job; no automatic restart or champion promotion.
The audit is pending. Exploration breadth and final convergence are separate:
passing a coarse score is not physical validation, and a weak coarse score does
not establish that a device is uninteresting under every operating condition.
