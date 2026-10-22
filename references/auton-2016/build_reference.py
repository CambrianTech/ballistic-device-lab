"""Reproduce a manual AFM contour estimate; no fitted transport parameters."""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
IMAGE = ROOT / "docs/assets/literature/auton-2016-figure-1.jpg"
# Pixel coordinates in the untouched publisher JPEG, x right/y down.
# Four dark etched regions, traced independently (no imposed mirror symmetry).
polygons = [
    [
        [22, 235],
        [37, 235],
        [49, 254],
        [64, 275],
        [75, 292],
        [77, 299],
        [73, 302],
        [65, 300],
        [48, 289],
        [22, 271],
    ],
    [
        [145, 235],
        [158, 235],
        [158, 273],
        [140, 286],
        [123, 299],
        [116, 303],
        [112, 301],
        [114, 293],
        [125, 274],
    ],
    [[22, 321], [40, 317], [52, 316], [57, 319], [55, 324], [44, 337], [29, 355], [22, 368]],
    [
        [158, 320],
        [143, 315],
        [135, 314],
        [131, 316],
        [133, 321],
        [143, 334],
        [153, 348],
        [158, 359],
    ],
]
# AFM horizontal axis spans approximately 1.0 micrometre across 136 pixels.
center = np.array([90.0, 302.0])
normalized = [(np.array(p) - center) * [1 / 68, -1 / 68] for p in polygons]
record = dict(
    key="auton-2016-afm-manual-v1",
    source_doi="10.1038/ncomms11670",
    source_figure="1a AFM inset",
    source_sha256=hashlib.sha256(IMAGE.read_bytes()).hexdigest(),
    method="Manual visual polyline estimate of dark etched regions; no optimization",
    image_pixel_polygons=polygons,
    image_center_px=center.tolist(),
    horizontal_scale_um_per_pixel=1 / 136,
    normalized_half_width_um=0.5,
    boundary_sensitivity_px=3,
    uncertainty_note="Three pixels is a proposed sensitivity envelope, not a measured confidence interval. AFM tip convolution and image resolution limit edge recovery.",
    obstacles=[p.tolist() for p in normalized],
    status="Geometry reference only; contacts beyond the AFM window, atomistic edges and device electrostatics are not reconstructed",
)
(OUT / "geometry.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.65, 1]})
axes[0].imshow(plt.imread(IMAGE))
axes[0].set_axis_off()
axes[0].set_title("Published Figure 1 (unchanged)")
for p in normalized:
    axes[1].add_patch(Polygon(p * 0.5, facecolor="#263746"))
axes[1].set(
    xlim=(-0.5, 0.5),
    ylim=(-0.5, 0.5),
    xlabel="x (µm)",
    ylabel="y (µm)",
    title="Manual AFM geometry estimate\nDark = etched / excluded region",
    aspect="equal",
)
axes[1].set_facecolor("#e9bd72")
fig.suptitle("Auton et al. (2016): fabricated reference, not our triangle control")
fig.text(
    0.5,
    0.01,
    "Source: doi:10.1038/ncomms11670, Figure 1, CC BY 4.0. Right: approximate manual tracing; no electrical reproduction claimed.",
    ha="center",
    fontsize=9,
)
fig.tight_layout(rect=(0, 0.04, 1, 0.95))
fig.savefig(OUT / "geometry-reference.png", dpi=160)
