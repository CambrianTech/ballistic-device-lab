"""Explicit electrode partition for a Dirichlet Poisson domain."""

import numpy as np

from .poisson3d import frozen_array


class ElectrodeBoundary:
    """Disjoint masks in caller-declared order, e.g. L,R,T,B,gate.

    Every outer node must belong to an electrode. Interior nodes may be free.
    Masks encode geometry only; voltage, lead-band and reservoir conventions
    remain explicit responsibilities of the device callback.
    """

    def __init__(self, masks):
        masks = tuple(np.asarray(mask) for mask in masks)
        if not masks or any(mask.dtype != bool for mask in masks):
            raise ValueError("Boolean electrode masks required")
        shape = masks[0].shape
        if len(shape) != 3 or min(shape) < 3 or any(mask.shape != shape for mask in masks):
            raise ValueError("Matching three-dimensional masks required")
        if any(not mask.any() for mask in masks):
            raise ValueError("Every declared electrode must have support")
        count = np.sum(masks, axis=0)
        if np.any(count > 1):
            raise ValueError("Electrode masks overlap; assign edges and corners explicitly")
        if any(not np.all(np.take(count, [0, -1], axis=axis) == 1) for axis in range(3)):
            raise ValueError("Every outer node needs a Dirichlet electrode assignment")
        self.masks = tuple(frozen_array(mask) != 0 for mask in masks)
        for mask in self.masks:
            mask.flags.writeable = False
        self.shape = shape

    def potentials(self, voltages_v):
        voltages = np.asarray(voltages_v, float)
        if voltages.shape != (len(self.masks),) or not np.isfinite(voltages).all():
            raise ValueError("One finite voltage per declared electrode required")
        fixed = np.full(self.shape, np.nan)
        for mask, voltage in zip(self.masks, voltages):
            fixed[mask] = voltage
        return frozen_array(fixed)
