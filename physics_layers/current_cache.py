"""Bounded exact-voltage memoization for one frozen deterministic current model."""

from collections import OrderedDict

import numpy as np


class ExactCurrentCache:
    """Create a new instance whenever geometry, model or tolerances change.

    No rounding, interpolation, failed-evaluation caching or persistent reuse.
    Intended only for deterministic quasistatic providers, not stateful dynamics.
    """

    def __init__(self, provider, *, capacity=32):
        if type(capacity) is not int or capacity < 1:
            raise ValueError("Positive integer capacity required")
        self.provider, self.capacity = provider, capacity
        self._cache = OrderedDict()

    def currents(self, voltage):
        voltage = np.asarray(voltage, dtype=float)
        if voltage.shape != (4,) or not np.isfinite(voltage).all():
            raise ValueError("Four finite voltages required")
        key = tuple(voltage)
        if key not in self._cache:
            current = np.asarray(self.provider.currents(voltage.copy()), dtype=float)
            if current.shape != (4,) or not np.isfinite(current).all():
                raise ValueError("Four finite currents required")
            self._cache[key] = current.copy()
            if len(self._cache) > self.capacity:
                self._cache.popitem(last=False)
        self._cache.move_to_end(key)
        return self._cache[key].copy()
