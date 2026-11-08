#!/usr/bin/env python3
"""Family Sigma (law-of-sines coupling), generator side.  Cloud prototype; NOT deployed.

Given a literal set (local 'L' and chord-pair 'X' literals of one model), build
  * the Lambda angle rows (cegar2.rows_for_lits: base, L, circle K, bisector P, hinge H rows),
  * log-length rows   ('LR', a,b,c,d, rel):  lv(ab) - lv(cd) = 0 / lv(cd) - lv(ab) - t >= 0 / lv(ab) - lv(cd) - t >= 0,
  * law of sines      ('SL', x,y,z):  lv(xy) - lv(xz) - g(z;x,y) + g(y;x,z) = 0        (triangle x,y,z),
  * rational tangent  ('TAN', p,a,b, m, c):  m*A(p;a,b) + c - g(p;a,b) >= 0,  valid iff c >= max_u G(u) - m u,
  * rational secant   ('SEC', p,a,b, lo, hi, m, c):  g(p;a,b) - m*A(p;a,b) - c >= 0, valid when lo <= A <= hi iff
                        m*lo + c <= G(lo) and m*hi + c <= G(hi)  (G concave),  where A in [lo,hi] is proved by two
                        exact Lambda certificates (system + 'BLO'/'BHI' row infeasible),
with G(u) = log sin(pi u) (g(p;a,b) stands for G of the angle at p in triangle p,a,b).
The clause is the union of the literal premises of every row in the supports of all certificates.
Usage (test): sigma.py n model.jsonl index"""
import sys, os, json, itertools, math
from fractions import Fraction
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from angle_lp import AngleLP, exact_certificate, verify_certificate
import cegar2, circle_rows, hinge_rows
from mpmath import iv, mpf
iv.dps = 40
FL = {'<': '>', '>': '<', '=': '='}


def G(u): return math.log(math.sin(math.pi * u))
def dG(u): return math.pi / math.tan(math.pi * u)
def Giv(q):           # interval enclosure of G at rational q
    x = iv.mpf(q.numerator) / q.denominator
    return iv.log(iv.sin(iv.pi * x))
from mpmath.libmp import to_rational
def _exact(t):        # exact rational value of an mpf tuple
    p, q = to_rational(t); return Fraction(p, q)
import math as _m
def frac_up(x):       # rational >= interval upper end, on a 1e-9 grid (small denominators)
    v = _exact(x._mpi_[1]); return Fraction(_m.floor(v * 10 ** 9) + 1, 10 ** 9)
def frac_dn(x):
    v = _exact(x._mpi_[0]); return Fraction(_m.ceil(v * 10 ** 9) - 1, 10 ** 9)


def tan_bound(m):
    """rigorous upper bound of max_{0<u<1} h(u), h(u) = G(u) - m u (concave): for any u0, max h <= h(u0) + |h'(u0)|
    (since |u - u0| < 1). u0 = float maximiser; returns an interval upper end."""
    u0 = math.atan2(math.pi, float(m)) / math.pi                  # cot(pi u0) = m/pi
    u = iv.mpf(Fraction(u0).limit_denominator(10 ** 12).numerator) / Fraction(u0).limit_denominator(10 ** 12).denominator
    mi = iv.mpf(m.numerator) / m.denominator
    h = iv.log(iv.sin(iv.pi * u)) - mi * u
    dh = iv.pi * iv.cos(iv.pi * u) / iv.sin(iv.pi * u) - mi
    return iv.mpf(h.b) + iv.mpf(max(abs(dh.a), abs(dh.b)))


def tan_cut(m):
    return frac_up(tan_bound(m))


def sec_cut(lo, hi):
    m = Fraction((G(float(hi)) - G(float(lo))) / float(hi - lo)).limit_denominator(10 ** 6)
    c = min(frac_dn(Giv(lo) - iv.mpf(m.numerator) / m.denominator * (iv.mpf(lo.numerator) / lo.denominator)),
            frac_dn(Giv(hi) - iv.mpf(m.numerator) / m.denominator * (iv.mpf(hi.numerator) / hi.denominator)))
    return m, c


def gkey(p, a, b): return ('g', p) + tuple(sorted((a, b)))
def lkey(a, b): return ('lv',) + ((a, b) if a < b else (b, a))


def sig_row(lp, tag):
    """coefficient dict over Lambda x-indices (int), 't', ('lv',..), ('g',..)"""
    k = tag[0]
    if k == 'LR':
        _, a, b, c, d, r = tag
        if r == '=': return {lkey(a, b): 1, lkey(c, d): -1}, 0, 'eq'
        if r == '<': return {lkey(c, d): 1, lkey(a, b): -1, 't': -1}, 0, 'ge'
        return {lkey(a, b): 1, lkey(c, d): -1, 't': -1}, 0, 'ge'
    if k == 'SL':
        _, x, y, z = tag
        return {lkey(x, y): 1, lkey(x, z): -1, gkey(z, x, y): -1, gkey(y, x, z): 1}, 0, 'eq'
    if k == 'TAN':
        _, p, a, b, m, c = tag; m = Fraction(m); c = Fraction(c)
        d = {i: m * x for i, x in lp.ang(p, a, b).items()}; d[gkey(p, a, b)] = -1
        return d, -c, 'ge'
    if k == 'SEC':
        _, p, a, b, lo, hi, m, c = tag; m = Fraction(m); c = Fraction(c)
        d = {i: -m * x for i, x in lp.ang(p, a, b).items()}; d[gkey(p, a, b)] = 1
        return d, c, 'ge'
    raise ValueError(tag)


def premises(tag):
    """literals a row depends on (normalized L/X)"""
    k = tag[0]
    if k == 'L': return [tag]
    if k == 'K':
        _, p, a, b, v, x, r = tag; return [('L', p, a, b, '='), circle_rows.norm(('L', p, x, v, r))]
    if k == 'P':
        _, p, a, b, v, r = tag; return [('L', p, a, b, '='), circle_rows.norm(('L', v, a, b, r))]
    if k == 'H':
        _, p, a, b, q, c, d, r = tag
        out = [hinge_rows.xlit((p, a), (q, c), '='), hinge_rows.xlit((p, b), (q, d), '='), hinge_rows.xlit((a, b), (c, d), r)]
        return [x for x in out if x is not None]
    if k == 'LR':
        return [hinge_rows.xlit(tag[1:3], tag[3:5], tag[5])]
    return []


class Sys:
    """generic LP over named keys; rows: (dict, rhs, kind, tag)"""
    def __init__(self, rows):
        self.rows = rows; keys = set()
        for d, r, k, t in rows: keys |= set(d)
        keys.discard('t'); self.keys = sorted(keys, key=str) + ['t']; self.ix = {k: i for i, k in enumerate(self.keys)}

    def solve(self, want_dual=False):
        nv = len(self.keys); er, ec, ev, beq, ieq, ur, uc, uv, bub, iub = [], [], [], [], [], [], [], [], [], []
        for idx, (d, r, kind, tag) in enumerate(self.rows):
            if kind == 'eq':
                i = len(beq)
                for k, x in d.items(): er.append(i); ec.append(self.ix[k]); ev.append(float(x))
                beq.append(float(r)); ieq.append(idx)
            else:
                i = len(bub)
                for k, x in d.items(): ur.append(i); uc.append(self.ix[k]); uv.append(-float(x))
                bub.append(-float(r)); iub.append(idx)
        c = np.zeros(nv); c[-1] = -1
        res = linprog(c, A_ub=csr_matrix((uv, (ur, uc)), shape=(len(bub), nv)), b_ub=np.array(bub),
                      A_eq=csr_matrix((ev, (er, ec)), shape=(len(beq), nv)), b_eq=np.array(beq),
                      bounds=[(None, None)] * (nv - 1) + [(-1, 1)], method='highs')
        if res.status == 2: return -np.inf, None
        if res.status != 0 or res.ineqlin.marginals is None:     # numerical trouble: let the Farkas LP decide
            return -np.inf, None
        du = {}
        if want_dual:
            for i, mu in zip(iub, res.ineqlin.marginals): du[i] = -mu
            for i, y in zip(ieq, res.eqlin.marginals): du[i] = y
        return -res.fun, du

    def check(self, cert):
        tot = {}; rhs = Fraction(0)
        for i, y in cert.items():
            d, r, kind, tag = self.rows[i]
            if kind == 'ge' and y < 0: return False
            for k, x in d.items(): tot[k] = tot.get(k, 0) + y * Fraction(x)
            rhs += y * Fraction(r)
        ct = tot.get('t', 0)
        if any(v != 0 for k, v in tot.items() if k != 't'): return False
        return (ct == -1 and rhs >= 0) or (ct == 0 and rhs > 0)

    def farkas(self):
        """L1-minimal Motzkin certificate: y>=0 on ge, free on eq, c>=0: sum y a = 0 on vars, sum y a[t] = -c,
        sum y r >= 0, c + sum y r = 1"""
        m = len(self.rows); nk = len(self.keys) - 1
        ge = [i for i in range(m) if self.rows[i][2] == 'ge']; eq = [i for i in range(m) if self.rows[i][2] == 'eq']
        cols = [(i, 1) for i in ge] + [(i, 1) for i in eq] + [(i, -1) for i in eq]; N = len(cols) + 1
        rr, cc, vv = [], [], []
        for j, (i, sg) in enumerate(cols):
            d, r, kind, tag = self.rows[i]
            for k, x in d.items(): rr.append(self.ix[k] if k != 't' else nk); cc.append(j); vv.append(sg * float(x))
            rr.append(nk + 1); cc.append(j); vv.append(sg * float(r))
        if getattr(self, 'fmode', 'ab') == 'b':      # pure type (b): no t contribution, sum y r = 1
            rr += [nk + 1]; cc += [N - 1]; vv += [0.0]
        else:
            rr += [nk, nk + 1]; cc += [N - 1, N - 1]; vv += [1.0, 1.0]
        Aeq = csr_matrix((vv, (rr, cc)), shape=(nk + 2, N)); beq = np.zeros(nk + 2); beq[nk + 1] = 1
        Aub = csr_matrix(([-sg * float(self.rows[i][1]) for (i, sg) in cols], ([0] * len(cols), list(range(len(cols))))), shape=(1, N))
        cost = np.ones(N); cost[-1] = 0
        if getattr(self, 'fseed', None) is not None:          # randomized L1 weights -> different vertex/support
            cost[:-1] = np.random.default_rng(self.fseed).uniform(0.5, 1.5, N - 1)
        res = linprog(cost, A_ub=Aub, b_ub=[0], A_eq=Aeq, b_eq=beq, bounds=[(0, None)] * N, method=getattr(self, 'fmethod', 'highs'))
        if res.status != 0: return None
        y = {}
        for j, (i, sg) in enumerate(cols):
            if res.x[j] > 1e-13: y[i] = y.get(i, 0) + sg * res.x[j]
        return {i: v for i, v in y.items() if abs(v) > 1e-13}

    def exact_repair(self, sup, du):
        """solve sum_i y_i a_i = -e_t exactly on the support (parametric Gauss-Jordan); free parameters are set to
        the rationalized float multipliers, so the exact solution stays close to the float certificate"""
        import sympy
        keys = sorted({k for i in sup for k in self.rows[i][0]}, key=str)
        if 't' not in keys: keys.append('t')
        R = lambda x: sympy.Rational(str(Fraction(x)))
        M = sympy.Matrix([[R(self.rows[i][0].get(k, 0)) for i in sup] for k in keys])
        rrow = sympy.Matrix([[R(self.rows[i][1]) for i in sup]])
        for target in ('a', 'a0', 'b'):
            if target == 'a': MM = M; rhs = sympy.Matrix([(-1 if k == 't' else 0) for k in keys])
            elif target == 'a0':     # tight type (a): also force sum y*rhs = 0 exactly
                MM = M.col_join(rrow); rhs = sympy.Matrix([(-1 if k == 't' else 0) for k in keys] + [0])
            else:
                MM = M.col_join(rrow); rhs = sympy.Matrix([0] * len(keys) + [1])
                sc = sum(float(self.rows[i][1]) * du[i] for i in sup)
                if sc <= 0: continue
            try:
                sol, params = MM.gauss_jordan_solve(rhs)
            except ValueError:
                continue
            # params are named tau0, tau1, ... in column order of the free columns: map via symbols in sol
            free = sorted(params, key=lambda p: int(str(p)[3:]))
            # identify which column each parameter stands for: the column whose solution entry is exactly that param
            subs = {}
            for j, e in enumerate(sol):
                if e in free and e not in subs:
                    v = du[sup[j]] if target == 'a' else du[sup[j]] / sc
                    subs[e] = sympy.Rational(str(Fraction(v).limit_denominator(10 ** 12)))
            for p in free:
                subs.setdefault(p, 0)
            for trial in (subs, {p: 0 for p in free}):
                vals = sol.subs(trial)
                cert = {sup[j]: Fraction(int(sympy.fraction(v)[0]), int(sympy.fraction(v)[1])) for j, v in enumerate(vals) if v != 0}
                if self.check(cert): return cert
        return None

    def exact_simplex(self, sup):
        """exact Phase-1 simplex on the support: y>=0 (free eq rows split), sum y a = -e_t, sum y r - s = 0, s >= 0"""
        from exact_simplex import feasible
        cols = []
        for i in sup:
            cols.append((i, 1))
            if self.rows[i][2] == 'eq': cols.append((i, -1))
        keys = sorted({k for i in sup for k in self.rows[i][0]}, key=str)
        if 't' not in keys: keys.append('t')
        A = [[sg * Fraction(self.rows[i][0].get(k, 0)) for (i, sg) in cols] + [Fraction(0)] for k in keys]
        A.append([sg * Fraction(self.rows[i][1]) for (i, sg) in cols] + [Fraction(-1)])      # sum y r - s = 0
        b = [Fraction(-1) if k == 't' else Fraction(0) for k in keys] + [Fraction(0)]
        y = feasible(A, b)
        if y is None: return None
        cert = {}
        for (i, sg), v in zip(cols, y[:-1]):
            if v != 0: cert[i] = cert.get(i, Fraction(0)) + sg * v
        cert = {i: v for i, v in cert.items() if v != 0}
        return cert if self.check(cert) else None

    def exact_lp(self, sup):
        """exact rational feasibility LP on the support (sympy simplex): y>=0 on ge rows (free eq rows split),
        sum y a = 0 on variables, sum y a[t] = -1, sum y r >= 0"""
        import sympy
        from sympy.solvers.simplex import linprog as slp
        cols = []
        for i in sup:
            cols.append((i, 1))
            if self.rows[i][2] == 'eq': cols.append((i, -1))
        keys = sorted({k for i in sup for k in self.rows[i][0]}, key=str)
        if 't' not in keys: keys.append('t')
        R = lambda x: sympy.Rational(str(Fraction(x)))
        Aeq = sympy.Matrix([[sg * R(self.rows[i][0].get(k, 0)) for (i, sg) in cols] for k in keys])
        beq = sympy.Matrix([(-1 if k == 't' else 0) for k in keys])
        A = sympy.Matrix([[-sg * R(self.rows[i][1]) for (i, sg) in cols]]); b = sympy.Matrix([0])
        try:
            val, x = slp(sympy.Matrix([0] * len(cols)), A=A, b=b, A_eq=Aeq, b_eq=beq)
        except Exception:
            return None
        cert = {}
        for (i, sg), v in zip(cols, x):
            if v != 0: cert[i] = cert.get(i, Fraction(0)) + sg * Fraction(int(sympy.fraction(v)[0]), int(sympy.fraction(v)[1]))
        cert = {i: v for i, v in cert.items() if v != 0}
        return cert if self.check(cert) else None

    def certificate(self):
        tm, du = self.solve(True)
        if du is None and tm == -np.inf: du = self.farkas()
        elif tm <= 1e-8:
            fk = self.farkas()
            if fk: du = fk
        if du is None or tm > 1e-8: return None
        sup = [i for i, y in du.items() if abs(y) > 1e-12]
        for md in (10 ** 4, 10 ** 6, 10 ** 8, 10 ** 10, 10 ** 12):
            cert = {i: Fraction(du[i]).limit_denominator(md) for i in sup}
            if self.check(cert): return cert
        ex = self.exact_repair(sup, du)
        if ex is not None: return ex
        for seed in (None, 1, 2, 3, 4, 5):
            self.fmode = 'b'; self.fseed = seed; dub = self.farkas(); self.fmode = 'ab'; self.fseed = None
            if dub:
                supb = [i for i, y in dub.items() if abs(y) > 1e-13]
                ex = self.exact_repair(supb, dub)
                if ex is not None: return ex
        for meth in ('highs-ds', 'highs-ipm'):        # other vertex/interior solutions of the Farkas LP
            self.fmethod = meth; du2 = self.farkas(); self.fmethod = 'highs'
            if du2:
                sup2 = [i for i, y in du2.items() if abs(y) > 1e-12]
                ex = self.exact_repair(sup2, du2)
                if ex is not None: return ex
        import sympy
        keys = sorted({k for i in sup for k in self.rows[i][0]}, key=str)
        M = sympy.Matrix([[sympy.Rational(str(Fraction(self.rows[i][0].get(k, 0)))) for i in sup] for k in keys])
        for target in ('a', 'b'):
            if target == 'a': MM = M; rhs = sympy.Matrix([(-1 if k == 't' else 0) for k in keys])
            else:
                MM = M.col_join(sympy.Matrix([[sympy.Rational(str(Fraction(self.rows[i][1]))) for i in sup]]))
                rhs = sympy.Matrix([0] * len(keys) + [1])
            try:
                sol, params = MM.gauss_jordan_solve(rhs)
            except ValueError:
                continue
            sol = sol.subs({p: 0 for p in params})
            cert = {i: Fraction(int(sympy.fraction(v)[0]), int(sympy.fraction(v)[1])) for i, v in zip(sup, sol)}
            if self.check(cert): return cert
        return None


def closed_bounds(lp, rows, angles):
    """float min/max of each angle over the closed Lambda LP (strict rows with slack 0)"""
    nv = lp.nv; Aub = []; bub = []; Aeq = []; beq = []
    for d, r, kind, tag in rows:
        v = np.zeros(nv)
        for k, x in d.items(): v[k] += float(x)
        v[lp.T] = 0
        if kind == 'eq': Aeq.append(v); beq.append(float(r))
        else: Aub.append(-v); bub.append(-float(r))
    Aub = np.array(Aub); Aeq = np.array(Aeq); out = {}
    for (p, a, b) in angles:
        res2 = []
        for sgn in (1, -1):
            c = np.zeros(nv)
            for k, x in lp.ang(p, a, b).items(): c[k] = sgn * x
            res = linprog(c, A_ub=Aub, b_ub=bub, A_eq=Aeq, b_eq=beq, bounds=[(None, None)] * (nv - 1) + [(0, 0)], method='highs')
            res2.append(sgn * res.fun if res.status == 0 else None)
        out[(p, a, b)] = res2
    return out


def build_and_certify(n, lits, grid=(0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.98)):
    lp = AngleLP(n); base = lp.base_rows()
    lits = [cegar2.norm_lit(tuple(l)) for l in lits]
    lam = cegar2.rows_for_lits(lp, base, lits)
    tris = list(itertools.combinations(range(n), 3))
    angles = [(v, w1, w2) for t3 in tris for (v, w1, w2) in ((t3[0], t3[1], t3[2]), (t3[1], t3[0], t3[2]), (t3[2], t3[0], t3[1]))]
    bd = closed_bounds(lp, lam, angles)
    rows = list(lam)
    seenx = set()
    for l in lits:
        x = hinge_rows.to_x(l) if l[0] in ('L', 'X') else None
        if x is None or x in seenx: continue
        seenx.add(x); tg = ('LR',) + x[1:]; d, r, k = sig_row(lp, tg); rows.append((d, r, k, tg))
    for t3 in tris:
        a, b, c = t3
        for (x, y, z) in ((a, b, c), (b, c, a), (c, a, b)):
            tg = ('SL', x, y, z); d, r, k = sig_row(lp, tg); rows.append((d, r, k, tg))
    tans = {}
    for u0 in grid:
        m = Fraction(dG(u0)).limit_denominator(10 ** 4); tans[m] = str(tan_cut(m))
    for (p, a, b) in angles:
        for m, c in tans.items():
            tg = ('TAN', p, a, b, str(m), c); d, r, k = sig_row(lp, tg); rows.append((d, r, k, tg))
        lo, hi = bd[(p, a, b)]
        if lo is None or hi is None: continue
        lo_q = Fraction(math.floor((lo - 1e-7) * 10 ** 6), 10 ** 6); hi_q = Fraction(math.ceil((hi + 1e-7) * 10 ** 6), 10 ** 6)
        if lo_q < Fraction(1, 10 ** 4) or hi_q > 1 - Fraction(1, 10 ** 4) or hi_q - lo_q < Fraction(1, 10 ** 6): continue
        m, c = sec_cut(lo_q, hi_q)
        tg = ('SEC', p, a, b, str(lo_q), str(hi_q), str(m), str(c)); d, r, k = sig_row(lp, tg); rows.append((d, r, k, tg))
    S = Sys(rows)
    cert = S.certificate()
    if cert is None: return None
    used = [rows[i][3] for i in cert]
    # bound certificates for every SEC row used
    bcerts = {}
    for tg in used:
        if tg[0] != 'SEC': continue
        _, p, a, b, lo, hi, m, c = tg; lo = Fraction(lo); hi = Fraction(hi)
        bc = {}
        for side in ('BLO', 'BHI'):
            A = lp.ang(p, a, b)
            if side == 'BLO': d = {k: -x for k, x in A.items()}; rhs = -lo      # lo - A - t >= 0  (A < lo)
            else: d = dict(A); rhs = hi                                       # A - hi - t >= 0  (A > hi)
            d[lp.T] = -1
            r2 = list(lam) + [(d, rhs, 'ge', (side, p, a, b, str(lo if side == 'BLO' else hi)))]
            ce = exact_certificate(lp, r2)
            if ce is None or not verify_certificate(lp, r2, ce): return None
            bc[side] = {str(r2[i][3]): str(y) for i, y in ce.items()}
            for i in ce: used.append(r2[i][3])
        bcerts[str(tg)] = bc
    clause = set()
    for tg in used:
        for l in premises(tg): clause.add(l)
    return {'lits': [list(x) for x in sorted(clause, key=str)],
            'sigma': {'main': {str(rows[i][3]): str(y) for i, y in cert.items()}, 'bounds': bcerts}}


if __name__ == '__main__':
    import time
    n = int(sys.argv[1]); J = json.loads(open(sys.argv[2]).readlines()[int(sys.argv[3])])
    lits = []
    for key, r in J['rels'].items():
        p, q = key.split('|'); p = eval(p); q = eval(q); lits.append(('X',) + p + q + (r,))
        sh = set(p) & set(q)
        if sh:
            u = sh.pop(); v = p[0] if p[1] == u else p[1]; w = q[0] if q[1] == u else q[1]
            lits.append(circle_rows.norm(('L', u, v, w, r)))
    t0 = time.time(); rec = build_and_certify(n, lits)
    if rec is None: print("no certificate", time.time() - t0)
    else:
        print(f"certified: clause {len(rec['lits'])} literals, main cert {len(rec['sigma']['main'])} rows, "
              f"{len(rec['sigma']['bounds'])} secant bounds, {time.time()-t0:.0f}s")
        if len(sys.argv) > 4: open(sys.argv[4], 'a').write(json.dumps(rec) + '\n')
