# Charge-cloud width meets the gate boundary

Increasing the Gaussian width from **0.10 to 0.12 nm** in the existing 15-site graphene fixture is **rejected**, before a self-consistent solution is computed. The five-sigma cloud overlaps a fixed-potential mesh node. No current or potential comparison is available.

The grid spacing remains 0.10 nm (factor 2), with the original gate box, dielectric, atoms, neutral background, 30 mV boundary potential and 10 mV lead bias. This is a model-domain constraint, not evidence that a wider cloud changes device performance. A width sensitivity study requires a larger box and separate box-size convergence checks; changing the box also changes the electrostatic model.

Reproduce from the repository root with the Kwant runtime:

```powershell
python -m physics_layers.finite_width_feedback --sigma-nm 0.12 --factors 2 --output results/physics-reference/width-sensitivity-012
```

Observed rejection: `ValueError: Charge deposition overlaps a fixed-potential node`, raised in `SiteMeshMap.deposit_charge` while constructing the electrostatic response kernel. The safeguard was retained. The original two-grid results remain unchanged. This fixture uses an uncalibrated charge width and is not physical validation.

The experiment CLI now accepts width, grid factors and a separate output directory, refuses existing result files before computation, and records null grid differences for single-grid runs.
