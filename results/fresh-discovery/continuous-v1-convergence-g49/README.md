# Refinement coverage at generation 49

Of **1,020 screened candidates**, **100 have converged** in both energy and phase resolution. **920 remain screened-only**. No candidate in this completed snapshot has attempted higher-resolution refinement while remaining unresolved.

Thus unresolved refinement is not consuming the completed snapshot's finalist population. The larger limitation is coverage: only 9.8% of screened candidates have received refinement. The other 90.2% must not be described as convergence failures or physically rejected devices. This inventory cannot show whether screening missed a winner.

Source inspection also confirms that worker exceptions propagate to a failed worker status; the fresh campaign does not convert those exceptions to a zero-power score. This is a control-flow observation, not an injected-failure test or proof that every numerical failure raises an exception.

The reusable inventory distinguishes converged, refined-unresolved and screened-only records using saved resolution counts and convergence flags. The JSON retains candidate identities and the immutable snapshot hash. No worker source, checkpoint or scoring policy was changed. All results refer to the existing fixed-potential model, not physical validation.

Reproduce with a fresh output directory:

```powershell
python -m ballistic_lab.reporting.convergence_inventory runs/fresh-discovery-continuous-v1/round-000049.json results/fresh-discovery/continuous-v1-convergence-g49
```
