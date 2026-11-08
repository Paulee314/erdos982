import itertools, math
from collections import Counter
def mk_subset(N,S,centre):
    # returns list of vertex ids and a dist-class function
    V=[('v',s) for s in S]+([('O',)] if centre else [])
    def cls(x,y):
        if x[0]=='O' or y[0]=='O': return ('R',)
        d=(x[1]-y[1])%N; d=min(d,N-d)
        return ('R',) if 6*d==N else ('c',d)
    return V,cls
def stats(V,cls):
    n=len(V); idx=range(n)
    w={}
    for i,j in itertools.combinations(idx,2):
        w[(i,j)]=sum(1 for k in idx if k!=i and k!=j and cls(V[k],V[i])==cls(V[k],V[j]))
    Z=sum(w.values()); w2=sum(1 for x in w.values() if x==2); w3=sum(1 for x in w.values() if x>2)
    kdeg=[sum(1 for j in idx if j!=i and w[tuple(sorted((i,j)))]>=2) for i in idx]
    Zp=[]
    for c in idx:
        cnt=Counter(cls(V[c],V[v]) for v in idx if v!=c); Zp.append(sum(m*(m-1)//2 for m in cnt.values()))
    return dict(n=n,Z=Z,w2=w2,w3=w3,w0=sum(1 for x in w.values() if x==0),kdeg=kdeg,Zp=Zp)
