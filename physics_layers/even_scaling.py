"""Two-amplitude even-response diagnostic; no fitted DC model is implied."""
import math


def even_scaling(low_amplitude_v, high_amplitude_v, low_even_v, high_even_v,
                 *, zero_bias_v=None):
    """Compare even responses, optionally subtracting a measured zero-drive output.

    None preserves the raw comparison and explicitly leaves the offset unresolved.
    A supplied zero is distinct from an unmeasured offset.
    """
    values = (low_amplitude_v, high_amplitude_v, low_even_v, high_even_v)
    if zero_bias_v is not None:
        values += (zero_bias_v,)
    if not all(math.isfinite(x) for x in values):
        raise ValueError('Finite inputs required')
    if not 0 < low_amplitude_v < high_amplitude_v:
        raise ValueError('Ordered positive amplitudes required')
    offset = 0.0 if zero_bias_v is None else zero_bias_v
    low_response = low_even_v - offset
    high_response = high_even_v - offset
    predicted = high_response*(low_amplitude_v/high_amplitude_v)**2
    return dict(low_even_v=low_even_v,quadratic_prediction_v=predicted,
                zero_bias_v=zero_bias_v, offset_corrected=zero_bias_v is not None,
                compared_low_response_v=low_response,
                compared_high_response_v=high_response,
                departure_from_quadratic_v=low_response-predicted,
                low_coefficient_per_v=low_response/low_amplitude_v**2,
                high_coefficient_per_v=high_response/high_amplitude_v**2,
                scope='Two-amplitude diagnostic; prediction refers to the compared response, with supplied zero-bias output subtracted. An absent offset remains unresolved; numerical uncertainty and model sensitivity require separate checks.')
