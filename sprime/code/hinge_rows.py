#!/usr/bin/env python3
"""Family Lambda-hinge (valid in EVERY strictly convex polygon; Euclid I.8 (SSS), I.24/I.25 (hinge)).
For two triangles with an angle at p between a,b and at q between c,d (triangles {p,a,b} != {q,c,d}) such that
|pa| = |qc| and |pb| = |qd|:   |ab| = |cd|  =>  A(p;a,b) = A(q;c,d);   |ab| < |cd|  =>  A(p;a,b) < A(q;c,d);  > likewise.
Literals: chord-pair literals ('X', a, b, c, d, rel) meaning |ab| rel |cd| with (a,b) < (c,d) lexicographically, a<b, c<d.
(A local literal ('L',u,v,w,rel) is the chord pair (u,v),(u,w).)"""
FL = {'<': '>', '>': '<', '=': '='}


def ch(a, b): return (a, b) if a < b else (b, a)


def xlit(e1, e2, rel):
    e1, e2 = ch(*e1), ch(*e2)
    if e1 == e2: return None
    return ('X',) + e1 + e2 + (rel,) if e1 < e2 else ('X',) + e2 + e1 + (FL[rel],)


def to_x(l):
    """L or X literal -> canonical X literal"""
    if l[0] == 'X': return xlit((l[1], l[2]), (l[3], l[4]), l[5])
    _, u, v, w, r = l; return xlit((u, v), (u, w), r)


def row(lp, p, a, b, q, c, d, rel):
    """rel = relation |ab| vs |cd|  -> row on A(p;a,b) - A(q;c,d)"""
    D = dict(lp.ang(p, a, b))
    for k, x in lp.ang(q, c, d).items(): D[k] = D.get(k, 0) - x
    if rel == '=': return D, 0, 'eq'
    if rel == '>':                      # A(p) > A(q): D - t >= 0
        D[lp.T] = -1; return D, 0, 'ge'
    D = {k: -x for k, x in D.items()}; D[lp.T] = -1; return D, 0, 'ge'


def items_for(lp, rel_of, maxrows=20000):
    """rel_of(e1, e2) -> '<','=','>' (relation of |e1| to |e2|) for any two chords. Groups angles (p;a,b) by the
    length classes of their two sides; every pair in a group with matching sides gives a row."""
    n = lp.n; import itertools
    # length classes by sorting chords with the model's preorder
    chords = [(a, b) for a in range(n) for b in range(a + 1, n)]
    cls = {}; reps = []
    for e in chords:
        for i, r in enumerate(reps):
            if rel_of(e, r) == '=': cls[e] = i; break
        else: cls[e] = len(reps); reps.append(e)
    groups = {}
    for p in range(n):
        for a, b in itertools.combinations([x for x in range(n) if x != p], 2):
            ka, kb = cls[ch(p, a)], cls[ch(p, b)]
            if ka > kb: a, b, ka, kb = b, a, kb, ka
            groups.setdefault((ka, kb), []).append((p, a, b))
    out = []
    for (ka, kb), L in groups.items():
        for (p, a, b), (q, c, d) in itertools.combinations(L, 2):
            if {p, a, b} == {q, c, d}: continue
            pairs = [((a, b), (c, d))]
            if ka == kb: pairs.append(((a, b), (d, c)))
            for (a1, b1), (c1, d1) in pairs:
                r = rel_of(ch(a1, b1), ch(c1, d1))
                reqs = [xlit((p, a1), (q, c1), '='), xlit((p, b1), (q, d1), '='), xlit((a1, b1), (c1, d1), r)]
                if any(x is None for x in reqs[2:]) and r != '=': continue
                reqs = [x for x in reqs if x is not None]
                D, rhs, kind = row(lp, p, a1, b1, q, c1, d1, r)
                out.append((('H', p, a1, b1, q, c1, d1, r), D, rhs, kind, reqs))
                if len(out) >= maxrows: return out
    return out


def rows_from_lits(lp, lits):
    """all hinge rows whose three premises are present in the literal set (L or X form)"""
    n = lp.n; import itertools
    R = {}
    for l in lits:
        if l[0] in ('L', 'X'):
            x = to_x(l)
            if x: R[(x[1:3], x[3:5])] = x[5]; R[(x[3:5], x[1:3])] = FL[x[5]]
    def rel(e1, e2):
        e1, e2 = ch(*e1), ch(*e2)
        if e1 == e2: return '='
        return R.get((e1, e2))
    V = sorted({v for e in R for c in e for v in c})
    out = []; seen = set()
    for p in V:
        for q in V:
            L = [(a, c) for a in V if a != p for c in V if c != q and rel((p, a), (q, c)) == '=']
            for (a, c), (b, d) in itertools.permutations(L, 2):
                if a == b or c == d or {p, a, b} == {q, c, d}: continue
                r = rel((a, b), (c, d))
                if r is None: continue
                key = (p, a, b, q, c, d)
                if key in seen or (q, c, d, p, a, b) in seen: continue
                seen.add(key)
                D, rhs, kind = row(lp, p, a, b, q, c, d, r)
                out.append((D, rhs, kind, ('H', p, a, b, q, c, d, r)))
    return out
