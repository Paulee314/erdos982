#!/usr/bin/env python3
"""Family Lambda-circle (valid in EVERY strictly convex polygon). Angles in units of pi.
For vertices p, a, b with |pa| = |pb| = r, circle Gamma_p (centre p, radius r) passes through a, b; the central angle
c = A(p;a,b) < 1 (fan). For any other vertex v (v not on line ab: strict convexity), with H = v's open side of line ab:
  inscribed angle of chord ab on side H:  c/2 if p is on side H (major arc side),  1 - c/2 otherwise.
  |pv| < r  ->  A(v;a,b) > inscribed;   |pv| = r  ->  A(v;a,b) = inscribed;   |pv| > r  ->  A(v;a,b) < inscribed.
(For v in H: v is inside the region bounded by the arc of Gamma_p in H and the chord ab iff |pv| < r; points of H
inside that region see ab under a larger angle, points of H outside it under a smaller one.)
Item: (tag, coef, rhs, kind, reqs) with tag ('K', p, a, b, v, x, rel): reqs = [('L',p,a,b,'='), ('L',p,x,v,rel)]
(x in {a, b}; rel = relation of |px| to |pv|, normalised so the literal's 2nd index < 3rd)."""
from fractions import Fraction
FL = {'<': '>', '>': '<', '=': '='}


def on_arc(x, a, b, n): return 0 < (x - a) % n < (b - a) % n


def norm(l):
    _, u, v, w, r = l
    return ('L', u, v, w, r) if v < w else ('L', u, w, v, FL[r])


def k_row(lp, p, a, b, v, inside):
    """inside in {'in','on','out'}; returns (coef, rhs, kind)"""
    n = lp.n
    same = on_arc(v, a, b, n) == on_arc(p, a, b, n)
    d = dict(lp.ang(v, a, b))
    c = lp.ang(p, a, b)
    # inscribed = c/2 (same) or 1 - c/2 (opposite);  row in terms of  D = A(v) - inscribed
    if same:
        for k, x in c.items(): d[k] = d.get(k, 0) - Fraction(x, 2)
        off = 0
    else:
        for k, x in c.items(): d[k] = d.get(k, 0) + Fraction(x, 2)
        off = 1
    # now D = sum(d) - off
    if inside == 'on': return d, off, 'eq'
    if inside == 'in':
        d[lp.T] = -1; return d, off, 'ge'
    d = {k: -x for k, x in d.items()}; d[lp.T] = -1; return d, -off, 'ge'


def items_for(lp, eqs, relation):
    """eqs: list of (p,a,b) with a<b and |pa|=|pb|; relation(p,x,v) -> '<','=','>' for |px| vs |pv|"""
    n = lp.n; out = []
    for (p, a, b) in eqs:
        for v in range(n):
            if v in (p, a, b): continue
            rel = relation(p, a, v)
            inside = {'>': 'in', '=': 'on', '<': 'out'}[rel]      # |pa| > |pv|  <=>  v inside
            d, rhs, kind = k_row(lp, p, a, b, v, inside)
            out.append((('K', p, a, b, v, a, rel), d, rhs, kind, [('L', p, a, b, '='), norm(('L', p, a, v, rel))]))
    return out


def fanpos(lp, p, v):
    """angular position of the ray p->v in p's fan, measured from the ray to p+1: dict of x coefficients"""
    i = lp.pos[p][v]
    return {lp.xi(p, k): 1 for k in range(i)}


def p_row(lp, p, a, b, v, rel):
    """Lambda-bisector: |pa|=|pb| (a<b), vertex v not in {p,a,b}, rel = relation of |va| to |vb|.
    Ray p->m (m = midpoint of ab) bisects angle apb inside p's fan, and within the fan (opening < pi) the directions on
    a's side of the bisector line are exactly those on a's side of p->m.  With F(v) = fan position:
      |va| < |vb|  <=>  v strictly on a's side  <=>  s * (2F(v) - F(a) - F(b)) > 0,   s = +1 if F(a) > F(b) else -1
      |va| = |vb|  <=>  2F(v) - F(a) - F(b) = 0."""
    d = {}
    for k, x in fanpos(lp, p, v).items(): d[k] = d.get(k, 0) + 2 * x
    for w in (a, b):
        for k, x in fanpos(lp, p, w).items(): d[k] = d.get(k, 0) - x
    if rel == '=': return d, 0, 'eq'
    s = 1 if lp.pos[p][a] > lp.pos[p][b] else -1
    if rel == '>': s = -s                      # v closer to b: on b's side
    d = {k: s * x for k, x in d.items()}; d[lp.T] = -1
    return d, 0, 'ge'


def p_items_for(lp, eqs, relation):
    """relation(v, a, b): relation of |va| to |vb|"""
    n = lp.n; out = []
    for (p, a, b) in eqs:
        for v in range(n):
            if v in (p, a, b): continue
            rel = relation(v, a, b)
            d, rhs, kind = p_row(lp, p, a, b, v, rel)
            out.append((('P', p, a, b, v, rel), d, rhs, kind, [('L', p, a, b, '='), norm(('L', v, a, b, rel))]))
    return out
