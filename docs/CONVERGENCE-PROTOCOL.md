# Coverage convergence follow-up

Frozen before execution, 2026-10-22. Select all seven device cases with any unresolved output in the published coverage snapshot. Reuse their 1025-point spectra without changing the Hamiltonian, thermal model, dimensions, contacts, drive or loads. Append 2049 and 4097-point nested grids over the same 0.42–1.38 eV interval. This adds 21,504 energy/device solves.

The follow-up reports its own criterion: BOTH 1025→2049 and 2049→4097 output changes must be at most 1 nV + 1% of the finer magnitude. The original 145/180 result remains immutable. Publish each originally unresolved output's disposition and also any previously passing output that fails this stronger follow-up. No tolerance relaxation, sign selection or candidate retuning. The budget stops at 4097 even if some cases remain unresolved.

Input checkpoint hashes and physics source hashes are checked and frozen before execution. Two CPU processes, one BLAS/OpenMP thread each. Every finished refinement level is checkpointed; all failures remain in the summary. This test addresses sampling density, not energy-window truncation, physical realism or fabrication variation.
