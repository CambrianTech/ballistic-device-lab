"""Two-amplitude even-response diagnostic; no fitted DC model is implied."""
import math


def even_scaling(low_amplitude_v, high_amplitude_v, low_even_v, high_even_v):
    if not all(math.isfinite(x) for x in (low_amplitude_v,high_amplitude_v,low_even_v,high_even_v)):
        raise ValueError('Finite inputs required')
    if not 0 < low_amplitude_v < high_amplitude_v:
        raise ValueError('Ordered positive amplitudes required')
    predicted = high_even_v*(low_amplitude_v/high_amplitude_v)**2
    return dict(low_even_v=low_even_v,quadratic_prediction_v=predicted,
                departure_from_quadratic_v=low_even_v-predicted,
                low_coefficient_per_v=low_even_v/low_amplitude_v**2,
                high_coefficient_per_v=high_even_v/high_amplitude_v**2,
                scope='Two-amplitude diagnostic; zero-bias offset, numerical uncertainty and model sensitivity must be checked separately')
