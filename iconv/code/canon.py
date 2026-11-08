import json, sys, glob, itertools
from geom import classes
def eqset(P, tol=1e-12):
    cl = classes(P, tol); s=set()
    for c, cs in enumerate(cl):
        for k in cs:
            for u, v in itertools.combinations(sorted(k), 2): s.add((c,u,v))
    return s
def canon(n, s):
    best=None
    for r in range(n):
        for m in (1,-1):
            f=lambda x:(m*x+r)%n
            t=tuple(sorted((f(c),)+tuple(sorted((f(u),f(v)))) for c,u,v in s))
            best = t if best is None or t<best else best
    return best
def describe(P):
    n=len(P); cl=classes(P,1e-12)
    per=[sum(len(k)*(len(k)-1)//2 for k in c) for c in cl]
    sizes=[sorted((len(k) for k in c if len(k)>1), reverse=True) for c in cl]
    return per, sizes
if __name__=='__main__':
    seen={}
    for fn in sys.argv[1:]:
        for line in open(fn):
            d=json.loads(line); P=[tuple(p) for p in d['P']]; n=len(P)
            k=canon(n, eqset(P)); seen.setdefault(k, []).append(d)
    print(len(seen), 'distinct equality structures up to dihedral relabelling')
    for k, ds in seen.items():
        d=ds[0]; P=[tuple(p) for p in d['P']]
        per,sizes=describe(P); print(' Z',d['Z'],'Tsets',d['T_sets'],'eqlat',d['equilateral'],'per-vertex',per,'class sizes',sizes, 'x',len(ds))
