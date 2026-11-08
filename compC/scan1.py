# exhaustive scan: subsets of regular N-gon (+centre if within open semicircle) ; record max kdeg and max w2, Z
import sys, itertools
from harness import *
best={}
for N in range(5,31):
  for n in range(5,12):
    for centre in (False,True):
      m=n-1 if centre else n
      if m>N: continue
      # S contains 0 wlog
      maxspan = (N-1)//2 if centre else N-1  # centre needs points in open semicircle: span < N/2
      if centre and m-1>maxspan: continue
      import math
      if math.comb(maxspan,m-1)>40000: continue
      for rest in itertools.combinations(range(1,maxspan+1),m-1):
        S=(0,)+rest
        if centre and 2*S[-1]>=N: continue
        V,cls=mk_subset(N,S,centre); st=stats(V,cls)
        kd=max(st['kdeg']); key=n
        b=best.setdefault(n,{'kd':(-1,),'w2':(-1,),'Z':(-1,)})
        if kd>b['kd'][0]: b['kd']=(kd,N,S,centre)
        if st['w2']>b['w2'][0]: b['w2']=(st['w2'],N,S,centre,st['Z'])
        if st['Z']>b['Z'][0]: b['Z']=(st['Z'],N,S,centre,st['w2'])
        if st['w3']: print('w3!',N,S,centre)
for n in sorted(best):
  b=best[n]; print(n,'kdmax',b['kd'],'(n-1)//2=',(n-1)//2,'| w2max',b['w2'][0],'n^2/4=',n*n/4,b['w2'][1:],'| Zmax',b['Z'][0],b['Z'][1:])
