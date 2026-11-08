#!/usr/bin/env python3
"""Lazy Lambda filter for T* v2 (Wonder's Phase 2): run on each SAT model BEFORE the Singular core search.
Rows (angle_lp.py, family Lambda only; valid in every strictly convex polygon): positivity, interior < pi, triangle
sums, and for chords sharing a vertex |uv| rel |uw| <=> A(v;u,w) rel A(w;u,v).  NO Lambda-MEC (violator-only), no
circle/bisector/hinge rows (kept out so that every certificate is checkable by check_lambda_certs.py's plain-core path).
Tier 1: equality rows only (Wonder's R4 'T*-Lambda tier').  Tier 2: all rows (equalities + strict).
A kill requires an exact rational Farkas certificate accepted by angle_lp.verify_certificate; the record
{'core': [[u,v,w,rel],...], 'cert': {repr(tag): 'p/q'}} is written so that check_lambda_certs.py can re-verify it
independently.  Anything else (feasible, LP numerical trouble, certificate not found) -> fall back to Singular."""
import itertools
from fractions import Fraction
from angle_lp import AngleLP, farkas, exact_certificate, verify_certificate


class LambdaFilter:
    def __init__(self, enc):
        self.enc = enc; n = enc.n; self.n = n
        self.lp = AngleLP(n); self.base = self.lp.base_rows(); self.lp.build_cache(self.base)
        self.stats = dict(calls=0, kill_eq=0, kill_full=0, feasible=0, nocert=0)

    def literals(self, m):
        """all ('L',u,v,w,rel) with v<w, from the model (set of true vars)"""
        enc = self.enc; pr, E, LT = enc.pr, enc.E, enc.LT; out = []
        for u in range(self.n):
            oth = [x for x in range(self.n) if x != u]
            for v, w in itertools.combinations(oth, 2):
                a, b = pr(u, v), pr(u, w)
                rel = '=' if E(a, b) in m else ('<' if LT(a, b) in m else '>')
                out.append(('L', u, v, w, rel))
        return out

    def var(self, l):
        enc = self.enc; _, u, v, w, rel = l; a, b = enc.pr(u, v), enc.pr(u, w)
        return enc.E(a, b) if rel == '=' else (enc.LT(a, b) if rel == '<' else enc.LT(b, a))

    def rows(self, lits):
        rows = list(self.base)
        for l in lits:
            d, r, k = self.lp.lit_row(l[1], l[2], l[3], l[4]); rows.append((d, r, k, l))
        return rows

    def _try(self, lits):
        lp = self.lp; rows = self.rows(lits)
        tm, _ = lp.solve(rows, want_dual=False)
        if not (tm <= 1e-9): return None
        nb = len(self.base)
        y = farkas(lp, rows)
        if y is None:
            _, y = lp.solve(rows); y = y or {}
        core = [rows[i][3] for i, v in y.items() if i >= nb and abs(v) > 1e-11]
        if not core: return None
        crow = self.rows(core)
        tm2, _ = lp.solve(crow, want_dual=False)
        if not (tm2 <= 1e-9): core = list(lits); crow = rows
        cert = exact_certificate(lp, crow)
        if cert is None or not verify_certificate(lp, crow, cert): return 'nocert'
        rec = {'core': [[l[1], l[2], l[3], l[4]] for l in core],
               'cert': {repr(tuple(crow[i][3])): str(Fraction(y_)) for i, y_ in cert.items() if y_ != 0}}
        return core, rec

    def check(self, m):
        """returns (clause, record, tier) or None"""
        self.stats['calls'] += 1
        lits = self.literals(m)
        for tier, sub in (('eq', [l for l in lits if l[4] == '=']), ('full', lits)):
            r = self._try(sub)
            if r == 'nocert': self.stats['nocert'] += 1; return None
            if r is None: continue
            core, rec = r
            self.stats['kill_' + tier] += 1
            rec['tier'] = tier
            return [-self.var(l) for l in core], rec, tier
        self.stats['feasible'] += 1
        return None
