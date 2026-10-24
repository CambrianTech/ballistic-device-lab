"""Parity diagnostics for matched opposite drives; not sinusoidal DC."""
import math


def polarity_components(positive_drive, negative_drive, positive_output, negative_output):
    values = (positive_drive, negative_drive, positive_output, negative_output)
    if not all(math.isfinite(x) for x in values):
        raise ValueError('Finite drives and outputs required')
    if positive_drive <= 0 or negative_drive != -positive_drive:
        raise ValueError('Equal-magnitude opposite drives required')
    return dict(even_output_v=(positive_output+negative_output)/2,
                odd_output_v=(positive_output-negative_output)/2,
                scope='Two-point parity diagnostic, not a sinusoidal-cycle average')
