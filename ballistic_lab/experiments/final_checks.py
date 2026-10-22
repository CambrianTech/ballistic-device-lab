"""Extra checks of optimized geometry, cap incident, and dimension reduction."""

import json

import numpy as np
from sklearn.metrics import r2_score

from ballistic_lab.experiments.learn_search import OUT, forest, score
from ballistic_lab.search.legacy_objective import polygon, sample
from ballistic_lab.transport.cpu import trace
from ballistic_lab.transport.gpu import trace_gpu


def main():
    result = json.loads((OUT / "learning-results.json").read_text())
    checks = []
    # Reproduce the formerly cap-limited seed on the frozen last-repeat winners.
    for design, x in enumerate(result["runs"][2]["winners"]):
        poly = polygon(x)
        for port in (0, 1):
            for spread in (1.0, 0.35):
                cpu = trace(
                    poly,
                    port,
                    n=65536,
                    spread=spread,
                    seed=71203 + port,
                    return_dest=True,
                )
                gpu = trace_gpu([poly], port, n=65536, spread=spread, seed=71203 + port, raw=True)
                mismatch = float(np.mean(cpu[3] != gpu[2][0]))
                assert mismatch < 0.001
                checks.append(
                    dict(
                        design=design,
                        port=port,
                        spread=spread,
                        mismatch=mismatch,
                        max_path=float(gpu[1].max()),
                    )
                )
    records = [json.loads(s) for s in (OUT / "learning-data.jsonl").read_text().splitlines()]
    train = next(r for r in records if r["tag"] == "pilot-training")
    x = np.array(train["x"])
    y = np.array(train["y"])
    # Independent second test set, since the first heldout set selected dimensions.
    xt = sample(np.random.default_rng(93140), 256)
    yt = score(xt, 93240, "independent-dimension-check", 8192)
    full = forest(17).fit(x, y)
    reduced = forest(17).fit(x[:, :2], y)
    dim = dict(
        full_r2=float(r2_score(yt, full.predict(xt))),
        width_height_r2=float(r2_score(yt, reduced.predict(xt[:, :2]))),
    )
    out = dict(optimized_cpu_gpu_checks=checks, independent_dimension_test=dim)
    (OUT / "final-checks.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
