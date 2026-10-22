"""Reproducible classical geometry screen, NOT an electrical rectifier solver."""

import json

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ballistic_lab.geometry.basic import segments, shapes
from ballistic_lab.paths import OUT
from ballistic_lab.transport.cpu import trace

PORTS = ["Left", "Right", "Top", "Bottom"]


def steering(polys, n=8192, spread=0.35, specularity=1.0, seed=123):
    p = np.array([trace(polys, k, n, spread, specularity, seed + k)[0] for k in (0, 1)])
    return float(np.mean(p[:, 3] - p[:, 2])), p


def linear_output(p):
    # Symmetrize MC estimates to enforce exact reciprocity; diagonal ensures conservation.
    w = (p + p.T) / 2
    np.fill_diagonal(w, 0)
    lap = np.diag(w.sum(axis=1)) - w
    v = np.array([0.5, -0.5, 0.0, 0.0])
    v[2:] = np.linalg.solve(lap[2:, 2:], -lap[2:, :2] @ v[:2])
    reverse = -v
    return float(v[2] - v[3]), float((v[2] - v[3] + reverse[2] - reverse[3]) / 2)


def main():
    kinds = ["straight", "triangle", "constriction"]
    rows = []
    matrices = []
    fig, axs = plt.subplots(2, 3, figsize=(13, 8), layout="constrained")
    for col, kind in enumerate(kinds):
        poly = shapes(kind)
        p = np.array([trace(poly, k, n=32768, seed=500 + k)[0] for k in range(4)])
        matrices.append(p)
        eq, _ = steering(poly, n=32768, spread=1.0, seed=800)
        focus, prob = steering(poly, n=32768, spread=0.35, seed=800)
        lin, dc = linear_output(p)
        rows.append(
            dict(
                geometry=kind,
                equilibrium_angular_steering=eq,
                collimated_steering=focus,
                steering_change=focus - eq,
                raw_reciprocity_max=float(abs(p - p.T).max()),
                linear_transverse_ratio=lin,
                linear_DC_ratio=dc,
                probabilities=p.tolist(),
            )
        )
        ax = axs[0, col]
        a, b = segments(poly)
        for aa, bb in zip(a, b):
            ax.plot(*np.array([aa, bb]).T, color="black", lw=2)
        for k, xy in enumerate(
            [
                ([-1, -1], [-0.3, 0.3]),
                ([1, 1], [-0.3, 0.3]),
                ([-0.3, 0.3], [1, 1]),
                ([-0.3, 0.3], [-1, -1]),
            ]
        ):
            ax.plot(*xy, color="#45b66d", lw=5, zorder=5)
        for port, color in [(0, "#168aad"), (1, "#ef8354")]:
            _, _, paths = trace(poly, port, n=32, spread=0.35, seed=42 + port)
            for path in list(paths.values())[:6]:
                ax.plot(*np.array(path).T, color=color, alpha=0.4, lw=0.8)
        ax.set(
            xlim=(-1.08, 1.08),
            ylim=(-1.08, 1.08),
            aspect="equal",
            title=kind.capitalize(),
            xlabel="Normalized x",
            ylabel="Normalized y",
        )
        ax = axs[1, col]
        ax.imshow(p, vmin=0, vmax=1, cmap="Blues")
        for i in range(4):
            for j in range(4):
                ax.text(j, i, f"{p[i, j]:.3f}", ha="center", va="center")
        ax.set(
            xticks=range(4),
            xticklabels=PORTS,
            yticks=range(4),
            yticklabels=PORTS,
            xlabel="Exit terminal",
            ylabel="Injection terminal",
            title="Equilibrium angular transmission",
        )
    fig.suptitle(
        "Ballistic geometry screen: trajectories and reciprocal scattering\nClassical hard-wall rays; illustrative geometry, no calibrated voltage response"
    )
    fig.savefig(OUT / "geometries.png", dpi=170)
    fig.savefig(OUT / "geometries.pdf")
    plt.close(fig)
    # Coarse multi-parameter search. Common random numbers reduce comparison noise.
    sweep = []
    for width in [0.3, 0.6, 0.9, 1.2]:
        for height in [0.3, 0.6, 0.9]:
            for offset in [-0.25, 0, 0.25]:
                poly = shapes("triangle", width, height, offset)
                eq, _ = steering(poly, n=4096, spread=1.0)
                focused, _ = steering(poly, n=4096, spread=0.35)
                sweep.append(dict(width=width, height=height, offset=offset, change=focused - eq))
    best = max(sweep, key=lambda r: r["change"])
    poly = shapes("triangle", best["width"], best["height"], best["offset"])
    holdout = []
    for spec in [1.0, 0.8, 0.5, 0.0]:
        changes = []
        for seed in range(4):
            eq, _ = steering(poly, n=32768, spread=1.0, specularity=spec, seed=2000 + 10 * seed)
            focus, _ = steering(poly, n=32768, spread=0.35, specularity=spec, seed=2000 + 10 * seed)
            changes.append(focus - eq)
        holdout.append(
            dict(
                specularity=spec,
                mean=float(np.mean(changes)),
                seed_std=float(np.std(changes, ddof=1)),
                samples=changes,
            )
        )
    # Mirror reverses steering; empty junction is symmetry control.
    mirror = [p * np.array([1, -1]) for p in poly]
    original = steering(poly, n=65536, seed=7000)[0]
    mirrored = steering(mirror, n=65536, seed=7000)[0]
    checks = dict(
        max_reciprocity_error=max(r["raw_reciprocity_max"] for r in rows),
        mirror_sum=original + mirrored,
        straight_collimated_steering=rows[0]["collimated_steering"],
        linear_DC_max=max(abs(r["linear_DC_ratio"]) for r in rows),
    )
    assert checks["max_reciprocity_error"] < 0.02
    assert abs(checks["mirror_sum"]) < 0.02
    assert abs(checks["straight_collimated_steering"]) < 0.02
    assert checks["linear_DC_max"] < 1e-12
    result = dict(
        model="Classical geometric collimation sensitivity; not DC voltage or efficiency",
        baselines=rows,
        sweep=sweep,
        best=best,
        holdout=holdout,
        checks=checks,
    )
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    ax.errorbar(
        [r["specularity"] for r in holdout],
        [100 * r["mean"] for r in holdout],
        yerr=[100 * r["seed_std"] for r in holdout],
        fmt="o-",
        capsize=4,
    )
    ax.set(
        xlabel="Probability of specular wall reflection",
        ylabel="Change in bottom-minus-top probability (points)",
        title="Selected triangle: sensitivity to imposed angular collimation\nError bars: seed standard deviation, not fabrication uncertainty",
    )
    ax.grid(alpha=0.25)
    fig.savefig(OUT / "robustness.png", dpi=170)
    plt.close(fig)
    print(json.dumps(dict(baselines=rows, best=best, holdout=holdout, checks=checks), indent=2))


if __name__ == "__main__":
    main()
