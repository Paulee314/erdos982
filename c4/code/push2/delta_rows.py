#!/usr/bin/env python3
"""Family Delta (chord-length LP; valid in EVERY strictly convex polygon).
Variables L(a,b) >= 0 (chord lengths, scaled so that their sum is 1) and the strictness slack t.
  TRI (x,y,z):     L(xy) + L(yz) - L(xz) - t >= 0          (strict triangle inequality; no three vertices collinear)
  QD (a,b,c,d,k):  a<b<c<d (cyclic order): L(ac) + L(bd) - L(ab) - L(cd) - t >= 0  (k=0)
                                           L(ac) + L(bd) - L(ad) - L(bc) - t >= 0  (k=1)
                   (diagonals of a convex quadrilateral cross at X; triangle inequality in aXb, cXd / aXd, bXc)
  RL (a,b,c,d,rel): relation literal |ab| rel |cd|: '=' L(ab)-L(cd) = 0; '<' L(cd)-L(ab)-t >= 0; '>' L(ab)-L(cd)-t >= 0
  LPOS (a,b):       L(ab) >= 0;   NORM: sum of all L = 1.
For a real polygon (scaled), t = min margin > 0 satisfies every row; a Farkas certificate refutes the literal set."""
import itertools
import numpy as np
from fractions import Fraction
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
FL = {'<': '>', '>': '<', '=': '='}


def ch(a, b): return (a, b) if a < b else (b, a)


def row_of(tag, n):
    """(coef dict over ('Lv',a,b) and 't', rhs, kind)"""
    k = tag[0]; Lv = lambda a, b: ('Lv',) + ch(a, b)
    if k == 'TRI':
        _, x, y, z = tag; return {Lv(x, y): 1, Lv(y, z): 1, Lv(x, z): -1, 't': -1}, 0, 'ge'
    if k == 'QD':
        _, a, b, c, d, w = tag
        D = {Lv(a, c): 1, Lv(b, d): 1, 't': -1}
        for (u, v) in (((a, b), (c, d)) if w == 0 else ((a, d), (b, c))):
            D[Lv(u, v)] = D.get(Lv(u, v), 0) - 1
        return D, 0, 'ge'
    if k == 'RL':
        _, a, b, c, d, r = tag
        if r == '=': return {Lv(a, b): 1, Lv(c, d): -1}, 0, 'eq'
        if r == '<': return {Lv(c, d): 1, Lv(a, b): -1, 't': -1}, 0, 'ge'
        return {Lv(a, b): 1, Lv(c, d): -1, 't': -1}, 0, 'ge'
    if k == 'LPOS':
        _, a, b = tag; return {Lv(a, b): 1}, 0, 'ge'
    if k == 'NORM':
        return {('Lv', a, b): 1 for a in range(n) for b in range(a + 1, n)}, 1, 'eq'
    raise ValueError(tag)


def base_tags(n):
    T = [('NORM',)] + [('LPOS', a, b) for a in range(n) for b in range(a + 1, n)]
    for a, b, c in itertools.combinations(range(n), 3):
        T += [('TRI', a, b, c), ('TRI', b, c, a), ('TRI', c, a, b)]
    for a, b, c, d in itertools.combinations(range(n), 4):
        T += [('QD', a, b, c, d, 0), ('QD', a, b, c, d, 1)]
    return T


def rel_tags(lits):
    """relation rows from L / X literals"""
    out = []
    for l in lits:
        if l[0] == 'L':
            _, u, v, w, r = l; e1, e2 = ch(u, v), ch(u, w)
        elif l[0] == 'X':
            e1, e2, r = (l[1], l[2]), (l[3], l[4]), l[5]
        else: continue
        out.append(('RL',) + e1 + e2 + (r,))
    return out


class DeltaLP:
    def __init__(self, n):
        self.n = n; self.base = base_tags(n)
        self.keys = [('Lv', a, b) for a in range(n) for b in range(a + 1, n)] + ['t']
        self.ix = {k: i for i, k in enumerate(self.keys)}

    def solve(self, tags, want_dual=False):
        n = self.n; nv = len(self.keys)
        er, ec, ev, beq, ieq, ur, uc, uv, bub, iub = [], [], [], [], [], [], [], [], [], []
        for idx, tg in enumerate(tags):
            d, r, kind = row_of(tg, n)
            if kind == 'eq':
                i = len(beq)
                for k, x in d.items(): er.append(i); ec.append(self.ix[k]); ev.append(x)
                beq.append(r); ieq.append(idx)
            else:
                i = len(bub)
                for k, x in d.items(): ur.append(i); uc.append(self.ix[k]); uv.append(-x)
                bub.append(-r); iub.append(idx)
        c = np.zeros(nv); c[-1] = -1
        res = linprog(c, A_ub=csr_matrix((uv, (ur, uc)), shape=(len(bub), nv)), b_ub=np.array(bub, float),
                      A_eq=csr_matrix((ev, (er, ec)), shape=(len(beq), nv)), b_eq=np.array(beq, float),
                      bounds=[(None, None)] * (nv - 1) + [(-1, 1)], method='highs')
        if res.status == 2: return -np.inf, None
        if res.status != 0 or res.ineqlin.marginals is None: return float('nan'), None   # numerical trouble: not 'infeasible'
        duals = {}
        if want_dual:
            for i, mu in zip(iub, res.ineqlin.marginals): duals[i] = -mu
            for i, y in zip(ieq, res.eqlin.marginals): duals[i] = y
        return -res.fun, duals

    def infeasible(self, tags): return self.solve(tags)[0] <= 1e-9

    def certificate(self, tags):
        tm, du = self.solve(tags, want_dual=True)
        if du is None or tm > 1e-7: return None
        sup = [i for i, y in du.items() if abs(y) > 1e-11]
        for md in (100, 1000, 10**4, 10**5, 10**6, 10**7):
            cert = {i: Fraction(du[i]).limit_denominator(md) for i in sup}
            if verify(tags, cert, self.n): return {str(tags[i]): str(y) for i, y in cert.items()}
        return None


def verify(tags, cert, n):
    tot = {}; rhs = Fraction(0)
    for i, y in cert.items():
        d, r, kind = row_of(tags[i], n)
        if kind == 'ge' and y < 0: return False
        for k, x in d.items(): tot[k] = tot.get(k, 0) + y * x
        rhs += y * r
    ct = tot.get('t', 0)
    if any(v != 0 for k, v in tot.items() if k != 't'): return False
    return (ct == -1 and rhs >= 0) or (ct == 0 and rhs > 0)


def core(dlp, lits):
    """minimal infeasible subset of relation literals (Farkas support, then deletion filter)"""
    rt = rel_tags(lits); base = dlp.base
    tm, du = dlp.solve(base + rt, want_dual=True)
    if du is None or tm > 1e-9: return None
    nb = len(base)
    cur = [lits[i] for i in range(len(rt)) if abs(du.get(nb + i, 0)) > 1e-11]
    lmap = {}
    if not dlp.infeasible(base + rel_tags(cur)): cur = list(lits)
    i = 0
    while i < len(cur):
        tr = cur[:i] + cur[i + 1:]
        if dlp.infeasible(base + rel_tags(tr)): cur = tr
        else: i += 1
    return cur
