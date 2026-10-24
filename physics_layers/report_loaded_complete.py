"""Publish a completed loaded pilot only after independent accounting checks."""
import argparse
import json
import math
from pathlib import Path


def validate(status, result):
    if status['phase'] != 'complete':
        raise ValueError('Outer solve is not complete')
    if status['source_sha256'] != result['source_sha256']:
        raise ValueError('Source manifests differ')
    s = result['solution']
    v, current = s['voltage_v'], s['current_a']
    if len(v) != 4 or len(current) != 4 or not all(math.isfinite(x) for x in v+current):
        raise ValueError('Invalid terminal vectors')
    drive = result['drive_v']
    if not math.isfinite(drive) or v[0] != drive/2 or v[1] != -drive/2:
        raise ValueError('Terminal bias disagrees with declared balanced drive')
    resistance = result['load_ohm']
    if not math.isfinite(resistance) or resistance <= 0:
        raise ValueError('Invalid load')
    t = result['circuit_tolerance']
    limit = t['current_atol_a'] + t['current_rtol']*max(map(abs,current))
    if not math.isfinite(limit) or limit <= 0:
        raise ValueError('Invalid tolerance')
    output = v[3]-v[2]
    kcl = max(abs(current[2]-output/resistance), abs(current[3]+output/resistance))
    pin = sum(a*b for a,b in zip(v[:2],current[:2]))
    device = sum(a*b for a,b in zip(v,current))
    load = output**2/resistance
    power_limit = limit*sum(map(abs,v))
    if abs(sum(current)) > limit or kcl > limit:
        raise ValueError('Current accounting failed')
    if abs(pin-device-load) > power_limit or device < -power_limit:
        raise ValueError('Power accounting failed')
    condition = s['output_jacobian_condition']
    if not math.isfinite(condition) or condition > 1e12:
        raise ValueError('Invalid final conditioning')
    for key, expected in [('output_v',output), ('input_power_w',pin), ('device_power_w',device), ('load_power_w',load)]:
        if not math.isclose(s[key],expected,rel_tol=1e-12,abs_tol=1e-30):
            raise ValueError('Reported '+key+' disagrees with terminal evidence')
    return dict(output_v=output,load_power_w=load,kcl_residual_a=kcl,
                power_residual_w=pin-device-load,output_jacobian_condition=condition)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    status=json.loads((args.run/'status.json').read_text(encoding='utf-8'))
    if status['phase'] != 'complete':
        raise ValueError('Outer solve is not complete; nothing published')
    result=json.loads((args.run/'result.json').read_text(encoding='utf-8'))
    checks=validate(status,result)
    args.output.mkdir(parents=True,exist_ok=False)
    for name,data in [('result.json',result),('completion.json',status),('accounting.json',checks)]:
        (args.output/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(checks,indent=2))


if __name__ == '__main__':
    main()
