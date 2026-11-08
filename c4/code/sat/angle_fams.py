#!/usr/bin/env python3
"""New clause families for the S'-violation search (designed by Fable, 3 Nov 2026, sprime/r2c_fable_clauses.txt;
L3 reviewed by Wonder + Fable). All are sound for every strictly convex n-gon, EXCEPT B1 and the B0 premise, which hold
for S'-VIOLATORS only (L3: a violator's MEC support has >= 3 vertices, no diametral pair, all consecutive gaps <= h-1).

  A : acute indicators A_v (int(v) < 90 deg).  A1: d(v-1,v+1) <= d(v-1,v) -> A_v ; d(v-1,v+1) <= d(v,v+1) -> A_v.
      A2: AtMost3(A).
  D : D_v (int(v) <= 60 deg) <- d(v-1,v+1) <= d(v-1,v) and <= d(v,v+1).  AtMost2(D).
  B : MEC support selectors s_v.  B0 AtLeast3(s) [violator]; B1 gap bound [violator]; with
      C(a,b) := -s_a v -s_b v s_{a+1} v ... v s_{b-1}  (a,b consecutive support, gap g = b-a in 1..h-1):
      B2 C v LT(ax, a(x+1)) for x = a+1..b-1;  B3 C v LT(bx, b(x-1)) for x = b-1..a+1 (x-1 down to a);
      B4 C v LT(xy, ab) for a <= x < y <= b, {x,y} != {a,b};  B5 C v -A_x for a < x < b;  A3 A_v -> s_v.
  F : at every p, for 1 <= i1<j1 <= i2<j2 <= i3<j3 <= n-1 (ccw order q_i = p+i): not all three triangles (p,q_i,q_j)
      'wide' (chord q_i q_j >= both radii):  OR_k [LT(q_ik q_jk, p q_ik) v LT(q_ik q_jk, p q_jk)].
"""
import itertools
from pysat.card import CardEnc, EncType


def add_families(enc, fams, violator=True):
    n = enc.n; h = n // 2; pr = enc.pr; LT = enc.LT; pool = enc.pool
    cl = []
    A = {v: pool.id(('A', v)) for v in range(n)}
    D = {v: pool.id(('D', v)) for v in range(n)}
    s = {v: pool.id(('s', v)) for v in range(n)}
    m = lambda x: x % n
    if 'A' in fams or 'B' in fams:
        for v in range(n):
            a, b = m(v - 1), m(v + 1)
            cl.append([LT(pr(a, v), pr(a, b)), A[v]])          # d(a,b) <= d(a,v)  -> A_v
            cl.append([LT(pr(v, b), pr(a, b)), A[v]])          # d(a,b) <= d(v,b)  -> A_v
    if 'A' in fams:
        cl += CardEnc.atmost(lits=[A[v] for v in range(n)], bound=3, vpool=pool, encoding=EncType.seqcounter).clauses
    if 'D' in fams:
        for v in range(n):
            a, b = m(v - 1), m(v + 1)
            cl.append([LT(pr(a, v), pr(a, b)), LT(pr(v, b), pr(a, b)), D[v]])
        cl += CardEnc.atmost(lits=[D[v] for v in range(n)], bound=2, vpool=pool, encoding=EncType.seqcounter).clauses
    if 'B' in fams:
        if violator:
            cl += CardEnc.atleast(lits=[s[v] for v in range(n)], bound=3, vpool=pool, encoding=EncType.seqcounter).clauses
            for a in range(n):
                cl.append([-s[a]] + [s[m(a + i)] for i in range(1, h)])          # B1
        for a in range(n):
            for g in range(1, h):
                b = m(a + g)
                C = [-s[a], -s[b]] + [s[m(a + i)] for i in range(1, g)]
                for i in range(1, g):                                           # B2: x = a+i, x+1 = a+i+1
                    x = m(a + i); cl.append(C + [LT(pr(a, x), pr(a, m(x + 1)))])
                for i in range(g - 1, 0, -1):                                   # B3: x = a+i (> a), x-1 >= a
                    x = m(a + i); cl.append(C + [LT(pr(b, x), pr(b, m(x - 1)))])
                seg = [m(a + i) for i in range(g + 1)]
                for x, y in itertools.combinations(seg, 2):                     # B4
                    if {x, y} != {a, b}: cl.append(C + [LT(pr(x, y), pr(a, b))])
                for i in range(1, g):                                           # B5
                    cl.append(C + [-A[m(a + i)]])
        for v in range(n):                                                      # A3
            cl.append([-A[v], s[v]])
    if 'F' in fams:
        for p in range(n):
            q = [m(p + i) for i in range(n)]       # q[i] = p+i, i = 1..n-1
            idx = range(1, n)
            for i1, j1, i2, j2, i3, j3 in itertools.combinations_with_replacement(idx, 6):
                if not (i1 < j1 <= i2 < j2 <= i3 < j3): continue
                c = []
                for i, j in ((i1, j1), (i2, j2), (i3, j3)):
                    ch = pr(q[i], q[j])
                    c += [LT(ch, pr(p, q[i])), LT(ch, pr(p, q[j]))]
                cl.append(c)
    return cl, dict(A=A, D=D, s=s)
