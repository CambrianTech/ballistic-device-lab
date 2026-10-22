
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
 int previous_hit=-1;
 for(int bounce=0;bounce<100000;bounce++) {
  double nearest=1e100; int hit=-1;
  for(int j=0;j<ns;j++) {
   if(j==previous_hit) continue;
   const double* a=seg+(geo*ns+j)*4;
   double sx=a[2]-a[0], sy=a[3]-a[1], den=dx*sy-dy*sx;
   if(fabs(den)<1e-15) continue;
   double ax=a[0]-px, ay=a[1]-py;
   double t=(ax*sy-ay*sx)/den, z=(ax*dy-ay*dx)/den;
   if(t>1e-12 && z>=-1e-12 && z<=1+1e-12 && t<nearest) {nearest=t;hit=j;}
  }
  if(hit<0) {dest[id]=-2; break;}
  if(mfp>0.) {
   double flight=-mfp*log(rnd(state));
   if(flight<nearest) {
    px+=flight*dx;py+=flight*dy;length+=flight;nscatter++;
    previous_hit=-1;
    double phi=6.2831853071795864769*rnd(state);
    dx=cos(phi);dy=sin(phi);
    continue;
   }
  }
  px+=nearest*dx; py+=nearest*dy; length+=nearest;
  previous_hit=hit;
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
