#!/usr/bin/env python3
"""Angle linear-programming relaxation ("family Λ") for the Erdős #982 / S' SAT encodings.

Linear facts valid in EVERY strictly convex n-gon (angles measured in units of pi):
  variables  x[p][k] > 0   elementary angle at vertex p between rays to L_p[k], L_p[k+1]  (L_p = p+1, ..., p-1)
  A(p;a,b) = sum of x[p][k] for k between the positions of a and b in L_p     (fan additivity; rays in label order)
  (I)  sum_k x[p][k] < 1                         interior angle < pi
  (T)  A(p;a,b) + A(a;p,b) + A(b;p,a) = 1          angle sum of triangle {p,a,b}
  (S)  for chords pa, pb sharing p (triangle pab):  |pa| = |pb|  <=>  A(b;p,a) = A(a;p,b)
                                                    |pa| < |pb|  <=>  A(b;p,a) < A(a;p,b)   (larger side, larger angle)
A full assignment of the E/LT literals between chords that share a vertex therefore gives a system of linear
equalities and STRICT inequalities in the x's; if it is infeasible, the literals used in a Farkas certificate form
a sound conflict clause. Strictness is handled with one slack t: maximize t subject to every strict row >= t.
Infeasible  <=>  max t <= 0.

check(assign) returns None (feasible) or a list of 'row' literals in a certificate (to be turned into a clause).
"""
import itertools
import numpy as np
from scipy.optimize import linprog
from fractions import Fraction


class AngleLP:
    def __init__(self, n):
        self.n = n
        m = lambda x: x % n
        self.L = {p: [m(p + i) for i in range(1, n)] for p in range(n)}
        self.pos = {p: {v: i for i, v in enumerate(self.L[p])} for p in range(n)}
        self.nx = n * (n - 2)
        self.nv = self.nx + 1          # + t
        self.T = self.nx

    def xi(self, p, k): return p * (self.n - 2) + k

    def ang(self, p, a, b):
        """coefficient dict of A(p;a,b)"""
        i, j = sorted((self.pos[p][a], self.pos[p][b]))
        return {self.xi(p, k): 1 for k in range(i, j)}

    def build_cache(self, base):
        """cache the sparse data of the base rows (used when a row list starts with these exact row objects)"""
        er, ec, ev, beq, ieq, ur, uc, uv, bub, iub = [], [], [], [], [], [], [], [], [], []
        for idx, (d, r, kind, tag) in enumerate(base):
            if kind == 'eq':
                i = len(beq)
                for k, x in d.items(): er.append(i); ec.append(k); ev.append(float(x))
                beq.append(float(r)); ieq.append(idx)
            else:
                i = len(bub)
                for k, x in d.items(): ur.append(i); uc.append(k); uv.append(-float(x))
                bub.append(-float(r)); iub.append(idx)
        self._bcache = (len(base), base[0], base[-1], (er, ec, ev, beq, ieq), (ur, uc, uv, bub, iub))

    def base_rows(self):
        """list of (coef dict, rhs, kind) with kind 'eq' or 'ge' (coef.z >= rhs); t is var T"""
        n = self.n; rows = []
        for p in range(n):
            for k in range(n - 2):
                rows.append(({self.xi(p, k): 1, self.T: -1}, 0, 'ge', ('pos', p, k)))
            d = {self.xi(p, k): -1 for k in range(n - 2)}; d[self.T] = -1
            rows.append((d, -1, 'ge', ('int', p)))
        for p, a, b in itertools.combinations(range(n), 3):
            d = {}
            for (c, u, v) in ((p, a, b), (a, p, b), (b, p, a)):
                for k, w in self.ang(c, u, v).items(): d[k] = d.get(k, 0) + w
            rows.append((d, 1, 'eq', ('tri', p, a, b)))
        return rows

    def lit_row(self, u, v, w, rel):
        """chords c1={u,v}, c2={u,w} sharing u; rel in '=','<','>' is the relation of |uv| to |uw|.
        angle opposite uv is at w: A(w;u,v); angle opposite uw is at v: A(v;u,w)."""
        aw = self.ang(w, u, v); av = self.ang(v, u, w)
        d = dict(av)
        for k, x in aw.items(): d[k] = d.get(k, 0) - x
        # d = A(v) - A(w)
        if rel == '=': return (d, 0, 'eq')
        if rel == '<':                      # |uv| < |uw|  ->  A(w) < A(v)  ->  A(v) - A(w) - t >= 0
            d = dict(d); d[self.T] = -1; return (d, 0, 'ge')
        if rel == '>':
            d = {k: -x for k, x in d.items()}; d[self.T] = -1; return (d, 0, 'ge')
        raise ValueError(rel)

    def solve(self, rows, want_dual=True):
        """rows: list of (dict, rhs, kind, tag). maximize t (t in [-1,1], x free). returns (tmax, duals by row index).
        Sparse construction (same LP as before)."""
        from scipy.sparse import csr_matrix
        nv = self.nv
        er, ec, ev, beq, ieq = [], [], [], [], []
        ur, uc, uv, bub, iub = [], [], [], [], []
        start = 0
        cache = getattr(self, '_bcache', None)
        if cache is not None and len(rows) >= cache[0] and rows[0] is cache[1] and rows[cache[0] - 1] is cache[2]:
            nb, _, _, E0, U0 = cache; start = nb
            er, ec, ev, beq, ieq = [list(x) for x in E0]; ur, uc, uv, bub, iub = [list(x) for x in U0]
        for idx in range(start, len(rows)):
            d, r, kind, tag = rows[idx]
            if kind == 'eq':
                i = len(beq)
                for k, x in d.items(): er.append(i); ec.append(k); ev.append(float(x))
                beq.append(float(r)); ieq.append(idx)
            else:
                i = len(bub)
                for k, x in d.items(): ur.append(i); uc.append(k); uv.append(-float(x))
                bub.append(-float(r)); iub.append(idx)
        if start == 0 and getattr(self, '_base', None) is not None and len(rows) >= len(self._base) \
                and rows[0] is self._base[0] and rows[len(self._base) - 1] is self._base[-1] and cache is None:
            pass
        c = np.zeros(nv); c[self.T] = -1
        bounds = [(None, None)] * self.nx + [(-1, 1)]
        Aeq = csr_matrix((ev, (er, ec)), shape=(len(beq), nv)) if beq else None
        Aub = csr_matrix((uv, (ur, uc)), shape=(len(bub), nv)) if bub else None
        res = linprog(c, A_ub=Aub, b_ub=np.array(bub) if bub else None, A_eq=Aeq, b_eq=np.array(beq) if beq else None,
                      bounds=bounds, method='highs')
        if res.status == 2:
            return -np.inf, None
        if res.status != 0 or (want_dual and (res.ineqlin.marginals is None and bub)):
            return float('nan'), {}         # numerical trouble: treated as NOT infeasible (no clause is learned)
        tmax = -res.fun
        duals = {}
        if want_dual:
            if bub:
                for i, mu in zip(iub, res.ineqlin.marginals): duals[i] = -mu
            if beq:
                for i, y in zip(ieq, res.eqlin.marginals): duals[i] = y
        return tmax, duals


def farkas(lp, rows):
    """Direct Motzkin/Farkas LP: y_i (>= 0 on 'ge' rows, free on 'eq'), c >= 0 with
         sum_i y_i a_i[x_k] = 0 (all k),  sum_i y_i a_i[t] = -c,  sum_i y_i r_i >= 0,  c + sum_i y_i r_i = 1,
    minimizing sum |y_i| (sparse support). Exists iff the strict system is infeasible. Returns float dict or None."""
    m = len(rows); nx = lp.nx
    ge = [i for i in range(m) if rows[i][2] == 'ge']; eq = [i for i in range(m) if rows[i][2] == 'eq']
    # variables: y_ge (m_ge, >=0), y_eq+ , y_eq- (>=0), c (>=0)
    cols = [(i, 1) for i in ge] + [(i, 1) for i in eq] + [(i, -1) for i in eq]
    N = len(cols) + 1
    Aeq = np.zeros((nx + 2, N)); beq = np.zeros(nx + 2)
    for j, (i, sg) in enumerate(cols):
        for k, x in rows[i][0].items():
            if k == lp.T: Aeq[nx, j] += sg * x
            else: Aeq[k, j] += sg * x
        Aeq[nx + 1, j] += sg * float(rows[i][1])
    Aeq[nx, N - 1] = 1.0                       # sum y a[t] + c = 0
    Aeq[nx + 1, N - 1] = 1.0; beq[nx + 1] = 1  # c + sum y r = 1
    Aub = np.zeros((1, N)); Aub[0, :len(cols)] = [-sg * float(rows[i][1]) for (i, sg) in cols]   # -sum y r <= 0
    cost = np.ones(N); cost[-1] = 0
    res = linprog(cost, A_ub=Aub, b_ub=[0], A_eq=Aeq, b_eq=beq, bounds=[(0, None)] * N, method='highs')
    if res.status != 0: return None
    y = {}
    for j, (i, sg) in enumerate(cols):
        if res.x[j] > 1e-12: y[i] = y.get(i, 0) + sg * res.x[j]
    return {i: v for i, v in y.items() if abs(v) > 1e-12}


def exact_certificate(lp, rows, maxden=10**5):
    """Exact (rational) Farkas certificate that the strict system 'rows' is infeasible: float certificate from the
    max-t duals or from farkas(), rationalized; else exact rational solve on the support. Checked by
    verify_certificate (pure Fractions). Returns {row: Fraction} or None."""
    tries = []
    tmax, duals = lp.solve(rows)
    if duals is not None and tmax <= 1e-7: tries.append(duals)
    fk = farkas(lp, rows)
    if fk is not None: tries.append(fk)
    for duals in tries:
        sup = [i for i, y in duals.items() if abs(y) > 1e-11]
        for md in (100, 1000, 10**4, maxden, 10**7):
            cert = {i: Fraction(duals[i]).limit_denominator(md) for i in sup}
            if verify_certificate(lp, rows, cert): return cert
    import sympy
    for duals in tries:
        sup = [i for i, y in duals.items() if abs(y) > 1e-11]
        keys = sorted({k for i in sup for k in rows[i][0]})
        M = sympy.Matrix([[sympy.Rational(rows[i][0].get(k, 0)) for i in sup] for k in keys])
        for target in ('a', 'b'):
            if target == 'a': rhs = sympy.Matrix([(-1 if k == lp.T else 0) for k in keys]); MM = M
            else:   # type (b): zero on all variables, rhs-combination = 1
                MM = M.col_join(sympy.Matrix([[sympy.Rational(str(rows[i][1])) for i in sup]]))
                rhs = sympy.Matrix([0] * len(keys) + [1])
            try:
                sol, params = MM.gauss_jordan_solve(rhs)
            except ValueError:
                continue
            sol = sol.subs({p: 0 for p in params})
            cert = {i: Fraction(int(sympy.fraction(v)[0]), int(sympy.fraction(v)[1])) for i, v in zip(sup, sol)}
            if verify_certificate(lp, rows, cert): return cert
    return None


def verify_certificate(lp, rows, cert):
    """pure-Fraction verification. Valid certificate: y >= 0 on 'ge' rows, sum y a = 0 on every x, and either
    (a) sum y a[t] = -1 and sum y r >= 0   (=> t <= 0), or (b) sum y a[t] = 0 and sum y r > 0  (=> 0 >= positive)."""
    tot = {}
    rhs = Fraction(0)
    for i, y in cert.items():
        d, r, kind = rows[i][0], rows[i][1], rows[i][2]
        if kind == 'ge' and y < 0: return False
        for k, x in d.items(): tot[k] = tot.get(k, Fraction(0)) + y * x
        rhs += y * r
    if any(v != 0 for k, v in tot.items() if k != lp.T): return False
    ct = tot.get(lp.T, 0)
    if ct == -1: return rhs >= 0
    if ct == 0: return rhs > 0
    return False
