import sys, itertools, time
sys.path.insert(0,'../sat'); sys.path.insert(0,'.')
from patutil import eqset
from angle_lp import AngleLP
n=int(sys.argv[1]); fn=sys.argv[2]
lp=AngleLP(n); base=lp.base_rows()
L=[l for l in open(fn) if l.strip() and not l.startswith('#')]
dead=0; t0=time.time()
for l in L:
    S=eqset(l,n); rows=list(base)
    for (c,u,v) in S:
        d,r,k=lp.lit_row(c,u,v,'='); rows.append((d,r,k,('E',c,u,v)))
    tm,_=lp.solve(rows,want_dual=False)
    if tm<=1e-9: dead+=1
print(n, len(L), 'dead by eq-only angle LP:', dead, time.time()-t0)
