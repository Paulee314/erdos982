import math, time
from geom import *
import realise
def eqs_from(P, tol=1e-9):
    cl = classes(P, tol); eqs=[]
    for c, cs in enumerate(cl):
        for k in cs:
            k = sorted(k)
            for v in k[1:]: eqs.append((c, k[0], v))
    return eqs
for n in (6,7,8):
    P = fan(n, math.pi/3/(2 if n<8 else 3))
    # reorder CCW: centre then arc points CCW
    eqs = eqs_from(P); t=time.time()
    r = realise.realise(n, eqs, tries=60, verbose=True)
    print(n, len(eqs), None if r is None else (r[1], r[2], r[3]), f'{time.time()-t:.1f}s')
