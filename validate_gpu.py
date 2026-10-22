import json,time
from pathlib import Path
import numpy as np
import cupy as cp
from simulate import trace,shapes
from gpu_trace import trace_gpu,polygon,evaluate,sample

from paths import OUT as out
reports=[]
for poly in [shapes('straight'),shapes('triangle'),shapes('constriction'),polygon([1.3,.7,.1,.4])]:
    for port in range(4):
        cpu=trace(poly,port,n=4096,seed=901,return_dest=True)
        gpu=trace_gpu([poly],port,n=4096,seed=901,raw=True)
        mismatch=float(np.mean(cpu[3]!=gpu[2][0]))
        path_error=float(np.max(abs(cpu[1]-gpu[1][0])))
        assert mismatch<.001,(mismatch,path_error)
        reports.append(dict(port=port,mismatch=mismatch,max_path_error=path_error))
# Deterministic straight rays must all reach opposite port in an empty box.
for port in range(4):
    p=trace_gpu([[]],port,n=4096,spread=0)[0]
    assert p[[1,0,3,2][port]]==1
# Validate stochastic implementation statistically, independently of random stream.
for spec in [.8,0.]:
    poly=polygon([1.2,.6,0,0])
    cpu=trace(poly,0,n=65536,specularity=spec,seed=221)[0]
    gpu=trace_gpu([poly],0,n=65536,specularity=spec,seed=221)[0]
    assert np.max(abs(cpu-gpu))<.015,(cpu,gpu)
    reports.append(dict(specularity=spec,max_probability_error=float(np.max(abs(cpu-gpu)))))
# Time representative specular batch, including data transfers, after warmup.
polys=[polygon(z) for z in sample(np.random.default_rng(73),32)]
t=time.perf_counter()
for p in polys: trace(p,0,n=8192,seed=92)
cpu_seconds=time.perf_counter()-t
trace_gpu(polys,0,n=8192,seed=92);cp.cuda.Stream.null.synchronize()
times=[]
for _ in range(3):
    t=time.perf_counter();trace_gpu(polys,0,n=8192,seed=92);cp.cuda.Stream.null.synchronize()
    times.append(time.perf_counter()-t)
gpu_seconds=float(np.median(times))
result=dict(device=cp.cuda.runtime.getDeviceProperties(0)['name'].decode(),tests=reports,
            cpu_seconds=cpu_seconds,gpu_seconds=gpu_seconds,speedup=cpu_seconds/gpu_seconds,
            cupy_pool_bytes=cp.get_default_memory_pool().total_bytes())
(out/'gpu-validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
