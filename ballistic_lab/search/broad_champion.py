"""Broad parameter recombination gated by actual etched-area differences."""
import numpy as np
from ballistic_lab.geometry.families import FAMILIES, geometry
from ballistic_lab.search.polygon_mutation import mutate_polygon


def shape_mask(obstacles, resolution=128):
    axis = -1 + (np.arange(resolution) + .5) * 2 / resolution
    x, y = np.meshgrid(axis, axis)
    mask = np.zeros(x.shape, dtype=bool)
    for polygon in obstacles:
        vertices = np.asarray(polygon)
        inside = np.zeros(x.shape, dtype=bool)
        for a, b in zip(vertices, np.roll(vertices, -1, axis=0)):
            if b[1] != a[1]:
                inside ^= ((a[1] > y) != (b[1] > y)) & (x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])
        mask |= inside
    return mask


def difference(a, b):
    changed = np.count_nonzero(a ^ b)
    return changed / a.size, changed / max(1, np.count_nonzero(a | b))


def broad_child(parent, rng, accepted):
    """Mutate the full boundary, or redraw multi-obstacle genes; reject lookalikes.

    Fixed 128x128 geometry diagnostic, not a physics or novelty claim.
    A bounded failure leaves the original search proposal in its slot.
    """
    original = shape_mask(parent['obstacles'])
    for attempt in range(256):
        if len(parent['obstacles']) == 1:
            proposal = mutate_polygon(parent, rng)
            if proposal is None:
                continue
        else:
            bounds = np.asarray(FAMILIES[parent['family']].bounds)
            low, width = bounds[:, 0], bounds[:, 1]-bounds[:, 0]
            unit = (np.asarray(parent['parameters'])-low)/width
            indices = rng.choice(len(unit), max(2, (len(unit)+1)//2), replace=False)
            unit[indices] = rng.random(len(indices))
            parameters = low + unit * width
            proposal = dict(family=parent['family'], parameters=parameters.tolist(),
                            obstacles=[p.tolist() for p in geometry(parent['family'],parameters)],
                            mutation_operator='half-gene redraw')
        obstacles = proposal['obstacles']
        mask = shape_mask(obstacles)
        area, relative = difference(original, mask)
        if area < .035 or relative < .20:
            continue
        if any(difference(mask, other)[0] < .02 or difference(mask, other)[1] < .15 for other in accepted):
            continue
        accepted.append(mask)
        return dict(**proposal,
                    changed_device_fraction=area, changed_union_fraction=relative,
                    shape_grid=128, proposal_trials=attempt+1)
    return None
