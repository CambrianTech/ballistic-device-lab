"""Independent NumPy reference trajectory solver."""

import numpy as np

from ballistic_lab.geometry.basic import cross, segments


def trace(
    polys,
    port,
    n=8192,
    spread=1.0,
    specularity=1.0,
    seed=123,
    return_dest=False,
    mfp=None,
):
    """Uniform contact position, flux cosine angular law; spread<1 is imposed collimation.
    Square side=2 units; centered absorbing contacts width=.6 on all four sides.
    Directions are unit speed. Diffuse reflections obey the cosine flux law.
    """
    rng = np.random.default_rng(seed)
    u = rng.uniform(-0.3, 0.3, n)
    theta = np.arcsin(rng.uniform(-spread, spread, n))
    normals = np.array([[1, 0], [-1, 0], [0, -1], [0, 1]])
    normal = normals[port]
    tangent = np.array([-normal[1], normal[0]])
    p = -normal[None, :] * (1 - 1e-9) + u[:, None] * tangent
    d = np.cos(theta)[:, None] * normal + np.sin(theta)[:, None] * tangent
    a, b = segments(polys)
    s = b - a
    sn = s / np.linalg.norm(s, axis=1)[:, None]
    norm = np.stack([-sn[:, 1], sn[:, 0]], axis=1)
    dest = np.full(n, -1)
    length = np.zeros(n)
    alive = np.arange(n)
    previous_hit = np.full(n, -1)
    paths = {i: [p[i].tolist()] for i in range(min(n, 16))}
    for bounce in range(100000):
        if not len(alive):
            break
        pp = p[alive]
        dd = d[alive]
        den = cross(dd[:, None, :], s[None, :, :])
        delta = a[None, :, :] - pp[:, None, :]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = cross(delta, s[None, :, :]) / den
            z = cross(delta, dd[:, None, :]) / den
        t = np.where((t > 1e-12) & (z >= -1e-12) & (z <= 1 + 1e-12), t, np.inf)
        # A straight reflected leg cannot intersect the same flat segment again.
        # Exclude numerical self-intersections; bulk scattering resets this rule.
        t = np.where(np.arange(len(a))[None, :] == previous_hit[alive, None], np.inf, t)
        hit = np.argmin(t, axis=1)
        distance = t[np.arange(len(alive)), hit]
        if not np.isfinite(distance).all():
            raise RuntimeError("Escaped boundary")
        bulk = np.zeros(len(alive), dtype=bool)
        if mfp is not None:
            flight = rng.exponential(mfp, len(alive))
            bulk = flight < distance
            distance = np.minimum(distance, flight)
        p[alive] += distance[:, None] * dd
        length[alive] += distance
        previous_hit[alive] = np.where(bulk, -1, hit)
        for idx in alive[alive < 16]:
            paths[int(idx)].append(p[idx].tolist())
        q = p[alive]
        contact = (
            (~bulk)
            & (hit < 4)
            & np.where((hit == 0) | (hit == 2), abs(q[:, 0]) < 0.3, abs(q[:, 1]) < 0.3)
        )
        # Outer segments bottom,right,top,left -> terminal ids.
        mapping = np.array([3, 1, 2, 0])
        dest[alive[contact]] = mapping[hit[contact]]
        keep = ~contact
        active = alive[keep]
        nn = norm[hit[keep]]
        old = dd[keep]
        reflected = old - 2 * np.sum(old * nn, axis=1)[:, None] * nn
        diffuse = (rng.random(len(active)) > specularity) & (~bulk[keep])
        if diffuse.any():
            inward = (
                nn[diffuse]
                * np.where(np.sum(old[diffuse] * nn[diffuse], axis=1) > 0, -1, 1)[:, None]
            )
            tang = np.stack([-inward[:, 1], inward[:, 0]], axis=1)
            angle = np.arcsin(rng.uniform(-1, 1, len(inward)))
            reflected[diffuse] = np.cos(angle)[:, None] * inward + np.sin(angle)[:, None] * tang
        if bulk.any():
            angle = rng.uniform(0, 2 * np.pi, int(bulk.sum()))
            reflected[bulk[keep]] = np.stack([np.cos(angle), np.sin(angle)], axis=1)
        d[active] = reflected
        alive = active
    if len(alive):
        raise RuntimeError(f"{len(alive)} rays unresolved; increase bounce cap")
    probabilities = np.bincount(dest, minlength=4) / n
    if return_dest:
        return probabilities, length, paths, dest
    return probabilities, length, paths
