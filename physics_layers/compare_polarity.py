"""Fail-closed checks for pairing completed opposite-drive experiments."""
from .polarity import polarity_components
from .report_loaded_complete import validate


def compare_completed(positive_status, positive, negative_status, negative, *, reviewed_source_changes=()):
    a=validate(positive_status,positive)
    b=validate(negative_status,negative)
    for key in ('load_ohm','max_poles','cache_currents','circuit_tolerance'):
        if positive[key] != negative[key]:
            raise ValueError('Unmatched '+key)
    def normalized(manifest):
        return {k.replace('\\','/'): v for k,v in manifest.items()}
    left=normalized(positive['source_sha256'])
    right=normalized(negative['source_sha256'])
    changed={k for k in left.keys() | right.keys() if left.get(k)!=right.get(k)}
    if changed != set(reviewed_source_changes):
        raise ValueError('Source differences require explicit exact review: '+repr(sorted(changed)))
    result=polarity_components(positive['drive_v'],negative['drive_v'],a['output_v'],b['output_v'])
    result['reviewed_source_changes']=sorted(changed)
    return result
