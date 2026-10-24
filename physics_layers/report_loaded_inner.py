"""Compact audit of completed inner solves; never certifies an outer load solve."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def audit(run, limit):
    rows = []
    for path in sorted(run.glob('evaluation-*.json'))[:limit]:
        raw = path.read_bytes()
        item = json.loads(raw)
        voltage = item['voltage_v']
        feedback = item['feedback']
        current = feedback['transport']['currents_a']
        residual = feedback['history'][-1]
        if len(voltage) != 4 or len(current) != 4:
            raise ValueError('Expected L/R/T/B vectors')
        values = voltage + current + list(residual.values())
        if not all(isinstance(x, (float, int)) and math.isfinite(x) for x in values):
            raise ValueError('Incomplete or nonfinite completed evaluation')
        # This reporter is specific to the pilot configured for a 10 kohm load.
        load_current = (voltage[2] - voltage[3]) / 1e4
        input_power = sum(v*i for v, i in zip(voltage[:2], current[:2]))
        device_power = sum(v*i for v, i in zip(voltage, current))
        load_power = (voltage[2] - voltage[3])**2 / 1e4
        rows.append(dict(input_power_w=input_power, device_power_w=device_power,
                         load_power_w=load_power,
                         power_balance_residual_w=input_power-device_power-load_power,
                         file=path.name, sha256=hashlib.sha256(raw).hexdigest(),
                         voltage_v=voltage, currents_a=current,
                         feedback_residual=residual,
                         current_sum_a=sum(current),
                         output_kcl_residual_a=[current[2]+load_current,
                                                current[3]-load_current]))
    return dict(scope='Completed inner evaluations only; outer load convergence, power checks and rectified DC unresolved. Uncalibrated numerical fixture.',
                load_ohm=1e4, lead_order=['L','R','T','B'],
                source_sha256=json.loads((run/'status.json').read_text())['source_sha256'],
                evaluations=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--limit', type=int, required=True)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('limit must be positive')
    result = audit(args.run, args.limit)
    if len(result['evaluations']) != args.limit:
        raise ValueError('Requested completed evaluations not available')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
