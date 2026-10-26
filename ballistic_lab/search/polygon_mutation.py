"""Free-boundary polygon mutation with conservative interior-clearance checks."""
import numpy as np


def cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def intersects(a,b,c,d):
    # Include touching and collinear overlap: both are rejected.
    if np.any(np.maximum(np.minimum(a,b),np.minimum(c,d)) > np.minimum(np.maximum(a,b),np.maximum(c,d))+1e-10):
        return False
    return cross(b-a,c-a)*cross(b-a,d-a)<=1e-12 and cross(d-c,a-c)*cross(d-c,b-c)<=1e-12


def valid_polygon(p):
    p=np.asarray(p,float)
    if p.ndim!=2 or p.shape[1]!=2 or not 3<=len(p)<=24 or not np.isfinite(p).all() or np.any(abs(p)>.9):
        return False
    edges=np.roll(p,-1,axis=0)-p
    if np.min(np.linalg.norm(edges,axis=1))<.04:
        return False
    if abs(sum(cross(a,b) for a,b in zip(p,np.roll(p,-1,axis=0))))/2<.025:
        return False
    for i in range(len(p)):
        for j in range(i+1,len(p)):
            if j==i+1 or (i==0 and j==len(p)-1): continue
            if intersects(p[i],p[(i+1)%len(p)],p[j],p[(j+1)%len(p)]): return False
    return True


def mutate_polygon(parent,rng):
    """Single-obstacle first adapter; multi-obstacle candidates use old branch."""
    if len(parent['obstacles'])!=1: return None
    p=np.array(parent['obstacles'][0],float)
    operation=int(rng.integers(3))
    if operation==1 and len(p)<24:
        i=int(rng.integers(len(p)))
        p=np.insert(p,i+1,(p[i]+p[(i+1)%len(p)])/2+rng.normal(0,.12,2),axis=0)
    elif operation==2 and len(p)>3:
        p=np.delete(p,int(rng.integers(len(p))),axis=0)
    p+=rng.normal(0,.07,p.shape)
    angle=float(rng.uniform(-np.pi,np.pi))
    center=p.mean(axis=0)
    rotation=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    p=(p-center)@rotation.T*float(rng.uniform(.8,1.15))+center+rng.uniform(-.16,.16,2)
    if not valid_polygon(p): return None
    return dict(family='polygon',parameters=[],obstacles=[p.tolist()],
                geometry_encoding='explicit-polygons-v1',rotation_rad=angle,
                mutation_operator=('boundary-jitter','insert-vertex','delete-vertex')[operation]+'+rotation+translation')
