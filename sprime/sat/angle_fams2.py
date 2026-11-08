#!/usr/bin/env python3
"""Round-3 clause families (3 Nov 2026). Sources: Fable (sprime/r3_fable_nextrule.txt): K = bisector cut ('G' there),
N = circular segment, O = obtuse middle of an equidistant triple; Wonder (sprime/r3_wonder_nextrule.txt): G = generalized
'angle >= 60' intervals (wide source, isosceles base source, superinterval closure, 3-disjoint budget), X = strict
'> 60', triangle-sum and isosceles apex/base coupling. All sound for every strictly convex n-gon (n >= 4).
Angular order at p: L_p = p+1, ..., p-1 (positions 0..n-2). Auxiliaries are one-way (intended witness = true angle
predicate), so they are only ever used negatively in budget clauses.

  K: chord {a,b}, each boundary arc walked from a toward b, x before y:   LT(xa,xb) v LT(yb,ya)
  N: centre p, a=L[i], b=L[j], inner c (and d):  -E(pa,pb) v LT(pa,pc) v LT(ca,ab) ;  same with cb ;
     -E(pa,pb) v LT(pa,pc) v LT(pa,pd) v LT(cd,ab)
  G: g(p;a,b) ['angle apb >= 60']:  W: LT(ab,pa) v LT(ab,pb) v g ;  B_a: -E(pa,ab) v LT(pa,pb) v g ;
     B_b: -E(pb,ab) v LT(pb,pa) v g ;  closure: g(p;L_i,L_x) -> g(p;L_i,L_j), g(p;L_x,L_j) -> g(p;L_i,L_j) ;
     budget: positions i1<j1<=i2<j2<=i3<j3:  -g1 v -g2 v -g3
  X: t(p;a,b) ['> 60']: LT(pa,ab) & LT(pb,ab) -> t ; E(pa,ab) & LT(pb,pa) -> t ; E(pb,ab) & LT(pa,pb) -> t ; t -> g ;
     triangle {a,b,c}: -g(a) v -g(b) v -g(c) v E(ab,ac) ; same v E(ab,bc) ; -t(a) v -g(b) v -g(c) (each rotation) ;
     isosceles apex p, E(pq,pr):  -E v -g(p;q,r) v -t(q;p,r) ; -E v -g(p;q,r) v -t(r;p,q) ;
                                  -E v -t(p;q,r) v -g(q;p,r) ; -E v -t(p;q,r) v -g(r;p,q)
  O: o(y;x,z) ['angle xyz > 90']: centre c, x<y<z in L_c, E(cx,cy) & E(cy,cz) -> o(y;x,z) ; o -> g ;
     budget at y: two interior-disjoint o's ;  o + two g's pairwise interior-disjoint.
"""
import itertools


def add_families2(enc, fams):
    n = enc.n; pr = enc.pr; LT = enc.LT; E = enc.E; pool = enc.pool
    m = lambda x: x % n
    L = {p: [m(p + i) for i in range(1, n)] for p in range(n)}
    pos = {p: {v: i for i, v in enumerate(L[p])} for p in range(n)}
    key = lambda p, a, b: (p,) + tuple(sorted((a, b), key=lambda v: pos[p][v]))
    g = lambda p, a, b: pool.id(('g',) + key(p, a, b))
    t = lambda p, a, b: pool.id(('t',) + key(p, a, b))
    o = lambda p, a, b: pool.id(('o',) + key(p, a, b))
    cl = []
    if 'K' in fams:
        for a, b in itertools.combinations(range(n), 2):
            for arc in ([m(a + i) for i in range(1, m(b - a))], [m(a - i) for i in range(1, m(a - b))]):
                for x, y in itertools.combinations(arc, 2):       # arc listed from a toward b
                    cl.append([LT(pr(x, a), pr(x, b)), LT(pr(y, b), pr(y, a))])
    if 'N' in fams:
        for p in range(n):
            Lp = L[p]
            for i, j in itertools.combinations(range(n - 1), 2):
                a, b = Lp[i], Lp[j]; eq = -E(pr(p, a), pr(p, b)); inner = Lp[i + 1:j]
                for c in inner:
                    cl.append([eq, LT(pr(p, a), pr(p, c)), LT(pr(c, a), pr(a, b))])
                    cl.append([eq, LT(pr(p, a), pr(p, c)), LT(pr(c, b), pr(a, b))])
                for c, d in itertools.combinations(inner, 2):
                    cl.append([eq, LT(pr(p, a), pr(p, c)), LT(pr(p, a), pr(p, d)), LT(pr(c, d), pr(a, b))])
    useG = bool({'G', 'X', 'O'} & set(fams))
    if useG:
        for p in range(n):
            Lp = L[p]
            for i, j in itertools.combinations(range(n - 1), 2):
                a, b = Lp[i], Lp[j]; G = g(p, a, b); ab, pa, pb = pr(a, b), pr(p, a), pr(p, b)
                cl.append([LT(ab, pa), LT(ab, pb), G])
                cl.append([-E(pa, ab), LT(pa, pb), G])
                cl.append([-E(pb, ab), LT(pb, pa), G])
                for x in range(i + 1, j):
                    cl.append([-g(p, a, Lp[x]), G]); cl.append([-g(p, Lp[x], b), G])
            for i1, j1, i2, j2, i3, j3 in itertools.combinations_with_replacement(range(n - 1), 6):
                if i1 < j1 <= i2 < j2 <= i3 < j3:
                    cl.append([-g(p, Lp[i1], Lp[j1]), -g(p, Lp[i2], Lp[j2]), -g(p, Lp[i3], Lp[j3])])
    if 'X' in fams:
        for p in range(n):
            for a, b in itertools.combinations(L[p], 2):
                T = t(p, a, b); ab, pa, pb = pr(a, b), pr(p, a), pr(p, b)
                cl.append([-LT(pa, ab), -LT(pb, ab), T])
                cl.append([-E(pa, ab), -LT(pb, pa), T])
                cl.append([-E(pb, ab), -LT(pa, pb), T])
                cl.append([-T, g(p, a, b)])
        for a, b, c in itertools.combinations(range(n), 3):
            ga, gb, gc = g(a, b, c), g(b, a, c), g(c, a, b)
            cl.append([-ga, -gb, -gc, E(pr(a, b), pr(a, c))])
            cl.append([-ga, -gb, -gc, E(pr(a, b), pr(b, c))])
            cl.append([-t(a, b, c), -gb, -gc]); cl.append([-ga, -t(b, a, c), -gc]); cl.append([-ga, -gb, -t(c, a, b)])
        for p in range(n):
            for q, r in itertools.combinations(L[p], 2):
                e = -E(pr(p, q), pr(p, r))
                cl += [[e, -g(p, q, r), -t(q, p, r)], [e, -g(p, q, r), -t(r, p, q)],
                       [e, -t(p, q, r), -g(q, p, r)], [e, -t(p, q, r), -g(r, p, q)]]
    if 'O' in fams:
        for c in range(n):
            for x, y, z in itertools.combinations(L[c], 3):
                cl.append([-E(pr(c, x), pr(c, y)), -E(pr(c, y), pr(c, z)), o(y, x, z)])
        for y in range(n):
            Ly = L[y]
            for a, b in itertools.combinations(Ly, 2): cl.append([-o(y, a, b), g(y, a, b)])
            iv = list(itertools.combinations(range(n - 1), 2))
            for (i1, j1), (i2, j2) in itertools.combinations(iv, 2):
                if j1 <= i2 or j2 <= i1:
                    cl.append([-o(y, Ly[i1], Ly[j1]), -o(y, Ly[i2], Ly[j2])])
            for i1, j1, i2, j2, i3, j3 in itertools.combinations_with_replacement(range(n - 1), 6):
                if i1 < j1 <= i2 < j2 <= i3 < j3:
                    I = [(Ly[i1], Ly[j1]), (Ly[i2], Ly[j2]), (Ly[i3], Ly[j3])]
                    for k in range(3):
                        cl.append([-o(y, *I[k])] + [-g(y, *I[l]) for l in range(3) if l != k])
    return cl, dict(g=g, t=t, o=o, L=L)
