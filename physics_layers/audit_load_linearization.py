"""Independent local linearization of archived loaded-feedback evidence."""
import json
from pathlib import Path
import numpy as np


def main():
    source = Path('results/physics-reference/loaded-inner-audit/first-seven.json')
    rows = json.loads(source.read_text(encoding='utf-8'))['evaluations']
    zero, top, bottom, point = [rows[i] for i in (0, 3, 4, 6)]
    r0 = np.array(zero['output_kcl_residual_a'])
    jacobian = np.column_stack([
        (np.array(row['output_kcl_residual_a'])-r0) / row['voltage_v'][axis]
        for row, axis in ((top, 2), (bottom, 3))
    ])
    prediction = np.linalg.solve(jacobian, -r0)
    observed = np.array(point['voltage_v'][2:])
    result = dict(scope='Initial-point forward-difference diagnostic, not final root conditioning or physical validation',
                  source=str(source), source_records=[r['sha256'] for r in (zero,top,bottom,point)],
                  jacobian_a_per_v=jacobian.tolist(), condition_number=float(np.linalg.cond(jacobian)),
                  predicted_output_terminals_v=prediction.tolist(),
                  observed_output_terminals_v=observed.tolist(),
                  max_prediction_error_v=float(np.max(abs(prediction-observed))),
                  observed_output_kcl_residual_a=point['output_kcl_residual_a'])
    assert result['condition_number'] < 100
    assert result['max_prediction_error_v'] < 1e-8
    Path('results/physics-reference/loaded-inner-audit/initial-linearization.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
