"""Double precision CUDA billiards. One independent ray per thread; small batches."""
import numpy as np
import cupy as cp
from simulate import segments

cp.get_default_memory_pool().set_limit(size=512*1024**2)
SOURCE=r'''
__device__ double rnd(unsigned long long &s) {
 s^=s<<13; s^=s>>7; s^=s<<17;
 return ((s>>11)+0.5)*1.1102230246251565e-16;
}
extern "C" __global__ void rays(const double* seg, int ns, int nd,
 const double* u, const double* angle, int n, int port, double spec,
 unsigned long long seed, double mfp, int* dest, double* lengths, int* scatters) {
 int id=blockDim.x*blockIdx.x+threadIdx.x;
 if(id>=n*nd) return;
 int k=id%n, geo=id/n;
 double nx=port==0?1:port==1?-1:0;
 double ny=port==2?-1:port==3?1:0;
 double px=-nx*(1-1e-9)-ny*u[k], py=-ny*(1-1e-9)+nx*u[k];
 double dx=cos(angle[k])*nx-sin(angle[k])*ny;
 double dy=cos(angle[k])*ny+sin(angle[k])*nx;
 double length=0.;
 unsigned long long state=(seed+1)*0x9e3779b97f4a7c15ULL+(k+1)*0xbf58476d1ce4e5b9ULL;
 if(!state) state=1;
 dest[id]=-1;
 int nscatter=0;
 for(int bounce=0;bounce<100000;bounce++) {
  double nearest=1e100; int hit=-1;
  for(int j=0;j<ns;j++) {
   const double* a=seg+(geo*ns+j)*4;
   double sx=a[2]-a[0], sy=a[3]-a[1], den=dx*sy-dy*sx;
   if(fabs(den)<1e-15) continue;
   double ax=a[0]-px, ay=a[1]-py;
   double t=(ax*sy-ay*sx)/den, z=(ax*dy-ay*dx)/den;
   if(t>1e-8 && z>=-1e-10 && z<=1+1e-10 && t<nearest) {nearest=t;hit=j;}
  }
  if(hit<0) {dest[id]=-2; break;}
  if(mfp>0.) {
   double flight=-mfp*log(rnd(state));
   if(flight<nearest) {
    px+=flight*dx;py+=flight*dy;length+=flight;nscatter++;
    double phi=6.2831853071795864769*rnd(state);
    dx=cos(phi);dy=sin(phi);
    continue;
   }
  }
  px+=nearest*dx; py+=nearest*dy; length+=nearest;
  if(hit<4 && ((hit==0 || hit==2)?fabs(px)<.3:fabs(py)<.3)) {
   dest[id]=hit==0?3:hit==1?1:hit==2?2:0; break;
  }
  const double* a=seg+(geo*ns+hit)*4;
  double sx=a[2]-a[0], sy=a[3]-a[1], norm=sqrt(sx*sx+sy*sy);
  double wx=-sy/norm, wy=sx/norm, dot=dx*wx+dy*wy;
  if(rnd(state)>spec) {
   if(dot>0) {wx=-wx;wy=-wy;}
   double sn=2*rnd(state)-1, cs=sqrt(1-sn*sn);
   dx=cs*wx-sn*wy;dy=cs*wy+sn*wx;
  } else {dx-=2*dot*wx;dy-=2*dot*wy;}
 }
 lengths[id]=length;
 scatters[id]=nscatter;
}
'''
KERNEL=cp.RawKernel(SOURCE,'rays',options=('--std=c++11','--fmad=false'))

def trace_gpu(polygons,port,n=8192,spread=1.,specularity=1.,seed=123,raw=False,mfp=None):
    seg=[]
    for poly in polygons:
        a,b=segments(poly);seg.append(np.concatenate([a,b],axis=1))
    seg=np.stack(seg).astype(np.float64)
    rng=np.random.default_rng(seed)
    u=rng.uniform(-.3,.3,n);theta=np.arcsin(rng.uniform(-spread,spread,n))
    count=n*len(polygons)
    dest=cp.empty(count,dtype=cp.int32);lengths=cp.empty(count,dtype=cp.float64)
    scatters=cp.empty(count,dtype=cp.int32)
    KERNEL(((count+127)//128,),(128,),
      (cp.asarray(seg),np.int32(seg.shape[1]),np.int32(len(polygons)),cp.asarray(u),cp.asarray(theta),
       np.int32(n),np.int32(port),np.float64(specularity),np.uint64(seed),np.float64(-1 if mfp is None else mfp),dest,lengths,scatters))
    d=dest.reshape(len(polygons),n)
    bad=int(cp.sum(d<0).get())
    if bad:
        codes,counts=np.unique(cp.asnumpy(d[d<0]),return_counts=True)
        raise RuntimeError(f'{bad} unresolved rays {dict(zip(codes.tolist(),counts.tolist()))}; no score accepted')
    probabilities=cp.asnumpy(cp.stack([(d==k).mean(axis=1) for k in range(4)],axis=1))
    if raw:return probabilities,cp.asnumpy(lengths).reshape(len(polygons),n),cp.asnumpy(d),cp.asnumpy(scatters).reshape(len(polygons),n)
    return probabilities

BOUNDS=np.array([[.25,1.5],[.25,1.1],[-.35,.35],[-.6,.6]])
def polygon(x):
    width,height,offset,skew=x
    return [np.array([[-width/2,offset+height/2],[width/2,offset+height/2],[skew*width/2,offset-height/2]])]

def sample(rng,n):return rng.uniform(BOUNDS[:,0],BOUNDS[:,1],(n,4))

def evaluate(x,n=4096,seed=123):
    """Mean collimation response at specularity 1 and .8; same rays across geometries."""
    x=np.asarray(x);all_scores=[]
    for start in range(0,len(x),32):
        polys=[polygon(z) for z in x[start:start+32]]
        scores=[]
        for spec in [1.,.8]:
            conditions=[]
            for spread in [1.,.35]:
                p=np.mean([trace_gpu(polys,k,n,spread,spec,seed+k) for k in (0,1)],axis=0)
                conditions.append(p[:,3]-p[:,2])
            scores.append(conditions[1]-conditions[0])
        all_scores.extend(np.mean(scores,axis=0).tolist())
    return np.array(all_scores)
