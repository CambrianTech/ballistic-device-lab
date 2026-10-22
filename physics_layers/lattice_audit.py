"""Fresh graph and single-energy cache audit; no DC certification implied."""

import gzip
import json
from pathlib import Path

import numpy as np
from matplotlib.path import Path as PolygonPath
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system, solve_spectrum


def main():
    output = Path("results/physics-reference/lattice-audit")
    output.mkdir(parents=True, exist_ok=True)
    queue = json.loads(Path("runs/leader-validation/queue.json").read_text())["candidates"]
    selected = {"D00", "triangle-control", "diversity-r0-profile-g15-1"}
    reports = []
    for candidate in queue:
        if candidate["key"] not in selected:
            continue
        device = SquareDevice(candidate["obstacles"], 60 * 0.246e-9)
        request = LatticeRequest((0.9,))
        system = build_system(device, request)
        hamiltonian = system.hamiltonian_submatrix(sparse=True).tocsr()
        graph = hamiltonian.copy()
        graph.setdiag(0)
        graph.eliminate_zeros()
        components, labels = connected_components(graph, directed=False)
        sizes = np.bincount(labels)
        positions = np.array([site.pos for site in system.sites])
        inside = np.zeros(len(positions), dtype=bool)
        for poly in device.geometry():
            inside |= PolygonPath(poly).contains_points(positions / 30, radius=1e-10)
        interfaces = [set(map(int, contact)) for contact in system.lead_interfaces]
        overlaps = sum(len(a & b) for i, a in enumerate(interfaces) for b in interfaces[i + 1 :])
        fresh = solve_spectrum(system, request)[0]
        cache = Path("runs/dc-continuous/spectra") / f"{candidate['key']}.json.gz"
        if not cache.exists():
            cache = Path("results/2026-10-22-dc-wide") / cache.name
        with gzip.open(cache, "rt", encoding="utf-8") as stream:
            saved = json.load(stream)
        if saved["candidate"]["obstacles"] != candidate["obstacles"]:
            raise ValueError("Cached geometry mismatch")
        old = next(row for row in saved["spectrum"] if abs(row["energy_ev"] - 0.9) < 1e-12)
        delta = float(np.max(abs(np.array(fresh["transmission"]) - old["transmission"])))
        mirror = positions * [1, -1]
        distances = cKDTree(positions).query(mirror)[0]
        reports.append(
            dict(
                candidate=candidate,
                width_m=device.width_m,
                sites=len(positions),
                components=int(components),
                component_sizes=sizes.tolist(),
                isolated_sites=int(np.sum(np.diff(graph.indptr) == 0)),
                sites_inside_etched_polygons=int(inside.sum()),
                contact_site_counts=[len(i) for i in interfaces],
                contact_overlap_sites=overlaps,
                contact_components=[sorted(set(labels[list(i)].tolist())) for i in interfaces],
                fresh_spectrum=fresh,
                cached_transmission_max_difference=delta,
                unmatched_sites_under_y_reflection=int(np.sum(distances > 1e-8)),
            )
        )
        if components != 1 or inside.any() or overlaps or delta > 1e-9:
            raise ArithmeticError(f"Lattice audit failed for {candidate['key']}")
    (output / "results.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    empty = build_system(SquareDevice((), 60 * 0.246e-9), LatticeRequest((0.9,)))
    positions = np.array([site.pos for site in empty.sites])
    unmatched = int(np.sum(cKDTree(positions).query(positions * [1, -1])[0] > 1e-8))
    (output / "empty-reflection.json").write_text(
        json.dumps(dict(sites=len(positions), unmatched_y_reflection=unmatched), indent=2),
        encoding="utf-8",
    )
    for row in reports:
        print(
            row["candidate"]["key"],
            row["sites"],
            "sites;",
            row["components"],
            "component; cache delta",
            row["cached_transmission_max_difference"],
            "mirror unmatched",
            row["unmatched_sites_under_y_reflection"],
        )


if __name__ == "__main__":
    main()
