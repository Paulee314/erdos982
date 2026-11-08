#!/usr/bin/env python3
# compC: numeric #W2 / Z for two-ring (and sqrt7 octagon) configurations. Tolerance-based (evidence only).
import math, itertools, sys
def d2(p,q): return (p[0]-q[0])**2+(p[1]-q[1])**2
def stats(P,tol=1e-9):
    n=len(P); W2=0; Z=0; w0=0
    for i,j in itertools.combinations(range(n),2):
        w=sum(1 for k in range(n) if k!=i and k!=j and abs(d2(P[k],P[i])-d2(P[k],P[j]))<=tol*max(1,d2(P[k],P[i])))
        Z+=w; W2+=(w>=2); w0+=(w==0)
    return Z,W2,w0
def convex(P):
    n=len(P); s=[]
    for i in range(n):
        a,b,c=P[i],P[(i+1)%n],P[(i+2)%n]
        s.append((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))
    return all(x>1e-12 for x in s)
s7=math.sqrt(7)
oct7=[(0,0),(1,0),((3+s7)/4,(1+s7)/4),((3+s7)/4,(5+s7)/4),(0.5,(2+s7)/2),(-0.5,(2+s7)/2),(-(1+s7)/4,(3+s7)/4),(-(1+s7)/4,(s7-1)/4)]
print('sqrt7 octagon: convex',convex(oct7),'Z,W2,w0 =',stats(oct7))
best={}
for m in (4,6,8,10,12):
    n=2*m
    for ri in range(1,400):
        r=0.8+0.4*ri/400
        P=[]
        for t in range(m):
            P.append((math.cos(2*math.pi*t/m),math.sin(2*math.pi*t/m)))
            P.append((r*math.cos(2*math.pi*(t+.5)/m),r*math.sin(2*math.pi*(t+.5)/m)))
        if not convex(P): continue
        Z,W2,w0=stats(P,1e-10)
        b=best.get(n)
        if b is None or W2>b[0] or (W2==b[0] and Z>b[1]): best[n]=(W2,Z,r)
for n in sorted(best): print('two-ring n=%d: max W2=%d (n^2/4=%g) Z=%d at r=%.4f'%(n,best[n][0],n*n/4,best[n][1],best[n][2]))
