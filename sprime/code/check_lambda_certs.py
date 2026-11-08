#!/usr/bin/env python3
"""INDEPENDENT exact checker for learned Lambda clauses (does not import angle_lp.py or cegar.py).
Each record: core = list of (u,v,w,rel) literals '|uv| rel |uw|' (rel in = < >); cert = {row tag: rational}.
Row semantics (all angles in units of pi; z = (x, t)):
  ('pos',p,k):   x[p,k] - t >= 0                          elementary angle at p between L_p[k], L_p[k+1] is > 0
  ('int',p):     -sum_k x[p,k] - t >= -1                  interior angle at p < pi
  ('tri',p,a,b): A(p;a,b) + A(a;p,b) + A(b;p,a) = 1       triangle angle sum
  ('L',u,v,w,'='): A(v;u,w) - A(w;u,v) = 0                 |uv| = |uw|  <=> equal opposite angles
  ('L',u,v,w,'<'): A(v;u,w) - A(w;u,v) - t >= 0            |uv| < |uw|  <=> angle at w < angle at v
  ('L',u,v,w,'>'): A(w;u,v) - A(v;u,w) - t >= 0
with L_p = (p+1, ..., p-1) mod n and A(p;a,b) = sum of x[p,k] for k from min to max-1 of the positions of a,b in L_p.
A valid certificate: multipliers y (>= 0 on inequality rows, any sign on equalities), every L row in the core, with
sum y_i * coef_i == 0 on every x[p,k], and either (a) == -1 on t and sum y_i * rhs_i >= 0 (then every point satisfying
the rows has -t >= 0, contradicting t > 0 for a real polygon, where t := min margin of the strict rows > 0), or
(b) == 0 on t and sum y_i * rhs_i > 0 (then 0 >= positive: the rows are inconsistent outright).
Usage: check_lambda_certs.py n file.jsonl [types.json]"""
import sys, os, json, ast
from fractions import Fraction

n = int(sys.argv[1])
def posn(p, v): return (v - p) % n - 1
def A(p, a, b):
    i, j = sorted((posn(p, a), posn(p, b)))
    return {('x', p, k): 1 for k in range(i, j)}
class Bad(Exception): pass
def vert(v):
    if type(v) is not int or not (0 <= v < n): raise Bad(f"vertex {v!r} out of range")
    return v
def row(tag):
    """explicit domain validation (no asserts): wrong arity / type / range / relation -> Bad"""
    if not isinstance(tag, tuple) or not tag: raise Bad(tag)
    kind = tag[0]
    if kind == 'pos':
        if len(tag) != 3: raise Bad(tag)
        p, k = vert(tag[1]), tag[2]
        if type(k) is not int or not (0 <= k < n - 2): raise Bad(tag)
        return {('x', p, k): 1, 't': -1}, 0, 'ge'
    if kind == 'int':
        if len(tag) != 2: raise Bad(tag)
        p = vert(tag[1]); d = {('x', p, k): -1 for k in range(n - 2)}; d['t'] = -1; return d, -1, 'ge'
    if kind == 'tri':
        if len(tag) != 4: raise Bad(tag)
        p, a, b = vert(tag[1]), vert(tag[2]), vert(tag[3])
        if len({p, a, b}) != 3: raise Bad(tag)
        d = {}
        for c, u, v in ((p, a, b), (a, p, b), (b, p, a)):
            for key, x in A(c, u, v).items(): d[key] = d.get(key, 0) + x
        return d, 1, 'eq'
    if kind == 'L':
        if len(tag) != 5: raise Bad(tag)
        u, v, w, rel = vert(tag[1]), vert(tag[2]), vert(tag[3]), tag[4]
        if len({u, v, w}) != 3 or rel not in ('=', '<', '>'): raise Bad(tag)
        d = dict(A(v, u, w))
        for key, x in A(w, u, v).items(): d[key] = d.get(key, 0) - x
        if rel == '=': return d, 0, 'eq'
        if rel == '>': d = {key: -x for key, x in d.items()}
        d['t'] = -1; return d, 0, 'ge'
    if kind in ('C', 'I', 'R'):
        return mec_row(tag)
    if kind == 'K':
        return k_row(tag)
    if kind == 'P':
        return p_row(tag)
    if kind == 'H':
        return h_row(tag)
    if kind in ('TRI', 'QD', 'RL', 'LPOS', 'NORM'):
        return delta_row(tag)
    raise Bad(tag)

SL = {}            # support literals of the clause being checked: v -> bool
LS = set()         # distance literals (u,v,w,rel) of the clause being checked
FLIPR = {'<': '>', '>': '<', '=': '='}
def k_row(tag):
    """Lambda-circle: |pa|=|pb| (centre p), vertex v, |px| rel |pv| (x in {a,b}); inscribed angle of chord ab on v's
    side is c/2 if p is on that side else 1-c/2 (c = A(p;a,b)); v inside/on/outside the circle -> >, =, <."""
    if len(tag) != 7: raise Bad(tag)
    p, a, b, v, x = (vert(z) for z in tag[1:6]); rel = tag[6]
    if len({p, a, b, v}) != 4 or a >= b or x not in (a, b) or rel not in ('<', '=', '>'): raise Bad(tag)
    if (p, a, b, '=') not in LS: raise Bad("missing equality literal")
    lit = (p, x, v, rel) if x < v else (p, v, x, FLIPR[rel])
    if lit not in LS: raise Bad("missing relation literal")
    same = on_arc(v, a, b) == on_arc(p, a, b)
    d = {}; addA(d, v, a, b, 1); addA(d, p, a, b, Fraction(-1, 2) if same else Fraction(1, 2)); off = 0 if same else 1
    if rel == '=': return d, off, 'eq'                      # |px| = |pv|: v on the circle
    if rel == '>': d['t'] = -1; return d, off, 'ge'          # |px| > |pv|: v inside -> larger angle
    d = {k: -c for k, c in d.items()}; d['t'] = -1; return d, -off, 'ge'
def on_arc(x, a, b): return 0 < (x - a) % n < (b - a) % n
CR = {}            # chord-pair relations of the clause being checked: ((a,b),(c,d)) -> rel, chords as sorted pairs
def chd(a, b): return (a, b) if a < b else (b, a)
def crel(e1, e2):
    if e1 == e2: return '='
    return CR.get((e1, e2))
def h_row(tag):
    """Lambda-hinge (Euclid I.8, I.24, I.25): |pa|=|qc|, |pb|=|qd| and |ab| rel |cd|  =>  A(p;a,b) rel A(q;c,d)."""
    if len(tag) != 8: raise Bad(tag)
    p, a, b, q, c, d = (vert(z) for z in tag[1:7]); rel = tag[7]
    if rel not in ('<', '=', '>') or len({p, a, b}) != 3 or len({q, c, d}) != 3 or {p, a, b} == {q, c, d}: raise Bad(tag)
    if crel(chd(p, a), chd(q, c)) != '=' or crel(chd(p, b), chd(q, d)) != '=': raise Bad("missing hinge premise")
    if crel(chd(a, b), chd(c, d)) != rel: raise Bad("missing third-side literal")
    D = {}; addA(D, p, a, b, 1); addA(D, q, c, d, -1)
    if rel == '=': return D, 0, 'eq'
    if rel == '<': D = {k: -x for k, x in D.items()}
    D['t'] = -1; return D, 0, 'ge'
def delta_row(tag):
    """Family Delta (chord lengths Lv(a,b) >= 0 summing to 1): strict triangle inequality; strict convex-quadrilateral
    inequality (diagonal sum > each pair of opposite sides); relation literal rows (premise must be in the clause)."""
    k = tag[0]; Lv = lambda a, b: ('Lv',) + chd(a, b)
    if k == 'NORM':
        if len(tag) != 1: raise Bad(tag)
        return {('Lv', a, b): 1 for a in range(n) for b in range(a + 1, n)}, 1, 'eq'
    if k == 'LPOS':
        if len(tag) != 3: raise Bad(tag)
        a, b = vert(tag[1]), vert(tag[2])
        if a >= b: raise Bad(tag)
        return {Lv(a, b): 1}, 0, 'ge'
    if k == 'TRI':
        if len(tag) != 4: raise Bad(tag)
        x, y, z = (vert(v) for v in tag[1:])
        if len({x, y, z}) != 3: raise Bad(tag)
        return {Lv(x, y): 1, Lv(y, z): 1, Lv(x, z): -1, 't': -1}, 0, 'ge'
    if k == 'QD':
        if len(tag) != 6: raise Bad(tag)
        a, b, c, d = (vert(v) for v in tag[1:5]); w = tag[5]
        if not (a < b < c < d) or w not in (0, 1): raise Bad(tag)
        D = {Lv(a, c): 1, Lv(b, d): 1, 't': -1}
        for (u, v) in (((a, b), (c, d)) if w == 0 else ((a, d), (b, c))):
            D[Lv(u, v)] = D.get(Lv(u, v), 0) - 1
        return D, 0, 'ge'
    if k == 'RL':
        if len(tag) != 6: raise Bad(tag)
        a, b, c, d = (vert(v) for v in tag[1:5]); r = tag[5]
        if a == b or c == d or chd(a, b) == chd(c, d) or r not in ('<', '=', '>'): raise Bad(tag)
        if crel(chd(a, b), chd(c, d)) != r: raise Bad("missing relation literal")
        if r == '=': return {Lv(a, b): 1, Lv(c, d): -1}, 0, 'eq'
        if r == '<': return {Lv(c, d): 1, Lv(a, b): -1, 't': -1}, 0, 'ge'
        return {Lv(a, b): 1, Lv(c, d): -1, 't': -1}, 0, 'ge'
    raise Bad(tag)
def p_row(tag):
    """Lambda-bisector: |pa|=|pb| (a<b), |va| rel |vb|; F = fan position at p (from the ray to p+1):
    rel '=' -> 2F(v)-F(a)-F(b) = 0;  v closer to a -> on a's side -> (2F(v)-F(a)-F(b)) has the sign of F(a)-F(b)."""
    if len(tag) != 6: raise Bad(tag)
    p, a, b, v = (vert(z) for z in tag[1:5]); rel = tag[5]
    if len({p, a, b, v}) != 4 or a >= b or rel not in ('<', '=', '>'): raise Bad(tag)
    if (p, a, b, '=') not in LS or (v, a, b, rel) not in LS: raise Bad("missing literal")
    def F(w): return {('x', p, k): 1 for k in range(posn(p, w))}
    d = {}
    for k, x in F(v).items(): d[k] = d.get(k, 0) + 2 * x
    for w in (a, b):
        for k, x in F(w).items(): d[k] = d.get(k, 0) - x
    if rel == '=': return d, 0, 'eq'
    sgn = 1 if posn(p, a) > posn(p, b) else -1
    if rel == '>': sgn = -sgn
    d = {k: sgn * x for k, x in d.items()}; d['t'] = -1
    return d, 0, 'ge'
def need(v, b):
    if SL.get(v) is not b: raise Bad(f"support literal ({v},{b}) missing")
def addA(d, p, a, b, c):
    for key, x in A(p, a, b).items(): d[key] = d.get(key, 0) + c * x
def mec_row(tag):
    kind = tag[0]
    if kind == 'C':
        if len(tag) != 5: raise Bad(tag)
        a, b, t1, t2 = (vert(x) for x in tag[1:])
        if len({a, b, t1, t2}) != 4 or on_arc(t1, a, b) != on_arc(t2, a, b): raise Bad(tag)
        for v in (a, b, t1, t2): need(v, True)
        d = {}; addA(d, t1, a, b, 1); addA(d, t2, a, b, -1); return d, 0, 'eq'
    if kind == 'I':
        if len(tag) != 6: raise Bad(tag)
        v, a, b, t = (vert(x) for x in tag[1:5]); side = tag[5]
        if len({v, a, b, t}) != 4: raise Bad(tag)
        same = on_arc(v, a, b) == on_arc(t, a, b)
        if side != ('s' if same else 'o'): raise Bad(tag)
        need(v, False); need(a, True); need(b, True); need(t, True)
        d = {}; addA(d, v, a, b, 1); addA(d, t, a, b, -1 if same else 1); d['t'] = -1
        return d, (0 if same else 1), 'ge'
    if kind == 'R':
        if len(tag) != 4: raise Bad(tag)
        x, y, t = (vert(z) for z in tag[1:])
        if len({x, y, t}) != 3 or on_arc(t, x, y): raise Bad(tag)
        need(x, True); need(y, True); need(t, True)
        for z in range(n):
            if on_arc(z, x, y): need(z, False)
        d = {}; addA(d, t, x, y, -1); d['t'] = -1; return d, Fraction(-1, 2), 'ge'
    raise Bad(tag)

def lit_ok(x):
    try:
        u, v, w, rel = x
        vert(u); vert(v); vert(w)
        return len({u, v, w}) == 3 and rel in ('=', '<', '>')
    except (Bad, ValueError, TypeError):
        return False

def verify(nn, core, cert):
    """exact check of one certificate for an nn-gon; core = set of literal tuples"""
    global n
    saved = n; n = nn
    try:
        if not core or not all(lit_ok(x) for x in core): return False
        tot = {}; rhs = Fraction(0)
        try:
            for key, val in cert.items():
                tag = ast.literal_eval(key); y = Fraction(val)
                if tag[0] == 'L' and tuple(tag[1:]) not in core: return False
                d, r, kind = row(tag)
                if kind == 'ge' and y < 0: return False
                for k, x in d.items(): tot[k] = tot.get(k, 0) + y * x
                rhs += y * r
        except Exception:            # any malformed tag/value: reject (fail closed)
            return False
        ct = tot.get('t', 0)
        return all(v == 0 for k, v in tot.items() if k != 't') and ((ct == -1 and rhs >= 0) or (ct == 0 and rhs > 0))
    finally:
        n = saved

def verify_nolits(cert):
    tot = {}; rhs = Fraction(0)
    try:
        for key, val in cert.items():
            tag = ast.literal_eval(key); y = Fraction(val)
            if tag[0] == 'L': return False
            d, r, kind = row(tag)
            if kind == 'ge' and y < 0: return False
            for k, x in d.items(): tot[k] = tot.get(k, 0) + y * x
            rhs += y * r
    except Exception:            # any malformed tag/value: reject (fail closed)
        return False
    ct = tot.get('t', 0)
    return all(v == 0 for k, v in tot.items() if k != 't') and ((ct == -1 and rhs >= 0) or (ct == 0 and rhs > 0))

# ---------------- family Sigma (law-of-sines coupling): rows over angles ('x',p,k), log-lengths ('lv',a,b),
# g-variables ('g',p,a,b) (a<b; g stands for G(angle at p in triangle p,a,b), G(u) = log sin(pi u), concave), 't'.
def sigma_row(tag):
    k = tag[0]
    if k == 'LR':
        if len(tag) != 6: raise Bad(tag)
        a, b, c, d = (vert(v) for v in tag[1:5]); r = tag[5]
        if a == b or c == d or chd(a, b) == chd(c, d) or r not in ('<', '=', '>'): raise Bad(tag)
        if crel(chd(a, b), chd(c, d)) != r: raise Bad("missing relation literal")
        e1, e2 = ('lv',) + chd(a, b), ('lv',) + chd(c, d)
        if r == '=': return {e1: 1, e2: -1}, 0, 'eq'
        if r == '<': return {e2: 1, e1: -1, 't': -1}, 0, 'ge'
        return {e1: 1, e2: -1, 't': -1}, 0, 'ge'
    if k == 'SL':                      # triangle x,y,z: lv(xy) - lv(xz) = g(z) - g(y)   (law of sines)
        if len(tag) != 4: raise Bad(tag)
        x, y, z = (vert(v) for v in tag[1:])
        if len({x, y, z}) != 3: raise Bad(tag)
        gk = lambda p, a, b: ('g', p) + chd(a, b)
        return {('lv',) + chd(x, y): 1, ('lv',) + chd(x, z): -1, gk(z, x, y): -1, gk(y, x, z): 1}, 0, 'eq'
    if k == 'TAN':                     # m*A(p;a,b) + c - g >= 0, valid iff c >= sup_u (G(u) - m u)
        if len(tag) != 6: raise Bad(tag)
        p, a, b = (vert(v) for v in tag[1:4]); m = Fraction(tag[4]); c = Fraction(tag[5])
        if len({p, a, b}) != 3: raise Bad(tag)
        if not tan_ok(m, c): raise Bad("tangent cut not valid")
        d = {}; addA(d, p, a, b, m); d[('g', p) + chd(a, b)] = -1
        return d, -c, 'ge'
    if k == 'SEC':                     # g - m*A - c >= 0 on [lo,hi]; validity + bound certificates checked separately
        if len(tag) != 8: raise Bad(tag)
        p, a, b = (vert(v) for v in tag[1:4]); lo, hi, m, c = (Fraction(v) for v in tag[4:8])
        if len({p, a, b}) != 3 or not (0 < lo < hi < 1): raise Bad(tag)
        if not sec_ok(lo, hi, m, c): raise Bad("secant cut not valid")
        d = {}; addA(d, p, a, b, -m); d[('g', p) + chd(a, b)] = 1
        return d, c, 'ge'
    raise Bad(tag)

def _ivq(q):
    from mpmath import iv
    return iv.mpf(q.numerator) / q.denominator
def tan_ok(m, c):
    """c >= h(u0) + |h'(u0)| >= max_u h(u), h(u) = G(u) - m u concave on (0,1) (any u0 in (0,1) works)"""
    import math
    from mpmath import iv, mpf
    iv.dps = 40
    u0 = Fraction(math.atan2(math.pi, float(m)) / math.pi).limit_denominator(10 ** 12)
    if not (0 < u0 < 1): return False
    u = _ivq(u0); mi = _ivq(m)
    h = iv.log(iv.sin(iv.pi * u)) - mi * u
    dh = iv.pi * iv.cos(iv.pi * u) / iv.sin(iv.pi * u) - mi
    bound = iv.mpf(h.b) + iv.mpf(max(abs(dh.a), abs(dh.b)))     # interval sum: outward rounding
    return _ivq(c).a >= bound.b
def sec_ok(lo, hi, m, c):
    """the line m*u + c lies below G at u = lo and u = hi (hence on [lo,hi], G concave)"""
    from mpmath import iv
    iv.dps = 40
    for q in (lo, hi):
        Gq = iv.log(iv.sin(iv.pi * _ivq(q)))
        if not ((_ivq(m) * _ivq(q) + _ivq(c)).b <= Gq.a): return False
    return True

def farkas_ok(rows_y):
    tot = {}; rhs = Fraction(0)
    for (d, r, kind), y in rows_y:
        if kind == 'ge' and y < 0: return False
        for k, x in d.items(): tot[k] = tot.get(k, 0) + y * x
        rhs += y * r
    ct = tot.get('t', 0)
    return all(v == 0 for k, v in tot.items() if k != 't') and ((ct == -1 and rhs >= 0) or (ct == 0 and rhs > 0))

def lam_row(tag):
    if tag[0] == 'L' and tuple(tag[1:]) not in LS: raise Bad("L row literal not in clause")
    return row(tag)

def verify_sigma(J):
    """record {'lits': [...], 'sigma': {'main': {tag: y}, 'bounds': {SEC tag: {'BLO': cert, 'BHI': cert}}}}"""
    try:
        sg = J['sigma']; main = sg['main']; bounds = sg['bounds']
        ry = []; secs = []
        for key, val in main.items():
            tag = ast.literal_eval(key); y = Fraction(val)
            if tag[0] in ('LR', 'SL', 'TAN', 'SEC'):
                ry.append((sigma_row(tag), y))
                if tag[0] == 'SEC': secs.append(tag)
            else: ry.append((lam_row(tag), y))
        if not farkas_ok(ry):
            if os.environ.get('SIGDEBUG'): print('main farkas failed')
            return False
        for tag in secs:                 # every secant used needs exact proofs of lo <= A <= hi (Lambda rows only)
            bc = bounds[str(tag)]; p, a, b = tag[1:4]; lo, hi = Fraction(tag[4]), Fraction(tag[5])
            for side, bnd in (('BLO', lo), ('BHI', hi)):
                ry2 = []; special = 0
                for key, val in bc[side].items():
                    t2 = ast.literal_eval(key); y = Fraction(val)
                    if t2[0] in ('BLO', 'BHI'):
                        if t2 != (side, p, a, b, str(bnd)): return False
                        d = {}; addA(d, p, a, b, -1 if side == 'BLO' else 1); d['t'] = -1
                        ry2.append(((d, -bnd if side == 'BLO' else bnd, 'ge'), y)); special += 1
                    elif t2[0] in ('LR', 'SL', 'TAN', 'SEC'): return False
                    else: ry2.append((lam_row(t2), y))
                if special != 1 or not farkas_ok(ry2):
                    if os.environ.get('SIGDEBUG'): print('bound failed', tag, side, special)
                    return False
        return True
    except Exception as ex:
        if os.environ.get('SIGDEBUG'): print('exception', repr(ex))
        return False

# optional k-point lemma library (records {'core','type','U'}): type certificates are checked on the k-gon; the record
# is accepted iff U is an injective map Z_k -> Z_n preserving or reversing cyclic order and core = U(type core).
types = None
if len(sys.argv) > 3:
    types = json.load(open(sys.argv[3])); tgood = []
    for T in types:
        k = T['k']; ck = {tuple(x) for x in T['core']}
        tgood.append(type(k) is int and 3 <= k <= n and verify(k, ck, T['cert']))
    print(f"types: {sum(tgood)} of {len(types)} type certificates verified on their k-gons")
FLIP = {'<': '>', '>': '<', '=': '='}
def cyclic_ok(U):
    k = len(U)
    if len(set(U)) != k or not all(type(u) is int and 0 <= u < n for u in U): return False
    for seq in (U, U[::-1]):
        steps = [(seq[(i + 1) % k] - seq[i]) % n for i in range(k)]
        if all(s > 0 for s in steps) and sum(steps) == n: return True   # winds exactly once ccw
    return False

ok = bad = 0
for ln, line in enumerate(open(sys.argv[2])):
    J = json.loads(line)
    if 'feasible' in J and 'core' not in J: continue          # informational record, not a clause
    if 'lits' in J:              # Lambda + Lambda-MEC record: L literals and support literals
        good = isinstance(J['lits'], list) and len(J['lits']) > 0 and ('cert' in J or 'sigma' in J)
        if good:
            Ls = LS; Ls.clear(); SL.clear(); CR.clear()
            for l in J['lits']:
                if l[0] == 'L' and len(l) == 5:
                    Ls.add(tuple(l[1:]))
                    if lit_ok(tuple(l[1:])):
                        e1, e2 = chd(l[1], l[2]), chd(l[1], l[3]); r = l[4]
                        CR[(e1, e2)] = r; CR[(e2, e1)] = FLIPR[r]
                elif l[0] == 'X' and len(l) == 6:
                    try:
                        for z in l[1:5]: vert(z)
                    except Bad: good = False; continue
                    e1, e2 = chd(l[1], l[2]), chd(l[3], l[4]); r = l[5]
                    if l[1] == l[2] or l[3] == l[4] or e1 == e2 or r not in ('<', '=', '>'): good = False; continue
                    if CR.get((e1, e2), r) != r: good = False
                    CR[(e1, e2)] = r; CR[(e2, e1)] = FLIPR[r]
                elif l[0] == 'S' and len(l) == 3 and type(l[1]) is int and 0 <= l[1] < n and type(l[2]) is bool:
                    if l[1] in SL and SL[l[1]] != l[2]: good = False
                    SL[l[1]] = l[2]
                else: good = False
            if 'sigma' in J: good = good and verify_sigma(J)
            else: good = good and verify(n, Ls, J['cert']) if Ls else good and verify_nolits(J['cert'])
        SL.clear(); LS.clear(); CR.clear()
        if good: ok += 1
        else:
            bad += 1; print("FAILED line", ln, J.get('lits'))
        continue
    good = 'core' in J and isinstance(J['core'], list) and len(J['core']) > 0
    if good and 'type' in J:
        good = types is not None and type(J['type']) is int and 0 <= J['type'] < len(types) and tgood[J['type']]
        if good:
            T = types[J['type']]; U = J['U']
            good = isinstance(U, list) and len(U) == T['k'] and cyclic_ok(U)
            if good:
                img = set()
                for (c, u, w, r) in T['core']:
                    a, b = U[u], U[w]; rr = r
                    if a > b: a, b, rr = b, a, FLIP[r]
                    img.add((U[c], a, b, rr))
                good = img == {tuple(x) for x in J['core']}
    elif good:
        good = 'cert' in J and verify(n, {tuple(x) for x in J['core']}, J['cert'])
    if good: ok += 1
    else:
        bad += 1; print("FAILED line", ln, J.get('core'))
print(f"n={n} {sys.argv[2]}: {ok} certificates verified exactly, {bad} failed")
