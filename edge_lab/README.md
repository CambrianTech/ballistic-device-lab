# Atomic-edge sensitivity

Run `python -m edge_lab.worker` in the isolated Kwant environment with single-thread BLAS.
This separate one-CPU consumer tests D00, triangle-control and each observed overall
leader from completed snapshots. Existing search scoring is unchanged.

The pilot has 21 cases: three devices, an intact baseline and three predetermined
seeds for each of one and three missing atoms. Eligible atoms have fewer than three
neighbors, lie within one lattice constant of an etched polygon, and remain at least
two lattice constants from the outer boundary. Lead interfaces cannot be deleted.
This probes discrete edge vacancies, not passivation, edge relaxation, a calibrated
fabrication distribution or phonon scattering. Equal vacancy counts do not mean equal
damaged-edge fractions. Three seeds cannot establish a reliable yield estimate.

The induced subgraph preserves all surviving onsite/hopping terms and lead models.
Disconnected graphs are retained as disconnected results, not resampled. Conservation,
unitarity, reciprocity and equilibrium gates apply at every energy. DC convergence
requires both 1025→2049 and 2049→4097 energy-grid changes plus 64→128 phase changes
to stay within 1 nV + 1% of final DC voltage. Failures remain unresolved. Conditions
are the existing fixed-potential 300 K, 0.9 eV, 10 mV peak, 10 kΩ campaign.

`runs/edge-sensitivity` stores source hashes, queue, status, exact removed sites,
spectral checkpoints and completed receipts. The OS lock prevents duplicates.
Create `STOP` there to stop between 32-energy batches; remove it and rerun to resume.
Do not edit loaded `edge_lab`, `verification_lab` or transport sources. A changed
source manifest requires a new validated campaign. Errors are recorded and require
diagnosis before retry; they never become passes. Reporting reads completed receipts.

Self-consistent graphene charge/electrostatics remains a separate required stage;
this experiment does not supply that missing model.
