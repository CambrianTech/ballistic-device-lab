"""Explicit bridge from converged feedback evaluations to the DC circuit API."""

import numpy as np


class FeedbackCurrentModel:
    """Callback takes L,R,T,B voltages and returns a converged FeedbackResult.

    The callback owns voltage-to-chemical-potential conversion, contact/gate
    boundaries, bound-state policy and internal convergence. No frozen spectrum
    or previous successful result is used if a new evaluation fails.
    lead_order maps circuit L,R,T,B to provider current indices explicitly.
    """

    def __init__(self, evaluate_feedback, *, lead_order):
        order = tuple(lead_order)
        if len(order) != 4 or any(type(i) is not int for i in order) or set(order) != set(range(4)):
            raise ValueError("Explicit permutation of four provider leads required")
        self.evaluate_feedback = evaluate_feedback
        self.lead_order = order

    def currents(self, voltages_v):
        voltage = np.asarray(voltages_v, dtype=float)
        if voltage.shape != (4,) or not np.isfinite(voltage).all():
            raise ValueError("Four finite L,R,T,B voltages required")
        result = self.evaluate_feedback(voltage.copy())
        current = np.asarray(result.transport.currents_a, dtype=float)
        if current.shape != (4,) or not np.isfinite(current).all():
            raise ValueError("Feedback must return four finite currents into the device")
        return current[list(self.lead_order)].copy()
