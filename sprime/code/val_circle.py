#!/usr/bin/env python3
"""Empirical soundness of circle_rows (Lambda-circle) on random and tie-rich strictly convex polygons: every K row,
built from the TRUE local equalities and TRUE distance relations, must hold on the TRUE angles.
plant=1 swaps the side rule (must be caught).  Usage: val_circle.py n count seed [plant=1]"""
import sys, os, math, random, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sat')); sys.path.insert(0, HERE)
import validate as V
from angle_lp import AngleLP
import circle_rows
args = [a for a in sys.argv[1:] if '=' not in a]; kw = dict(a.split('=') for a in sys.argv[1:] if '=' in a)
n, count, seed = int(args[0]), int(args[1]), int(args[2]); rng = random.Random(seed); lp = AngleLP(n)
if kw.get('plant') == '1':
    o = circle_rows.on_arc; circle_rows.on_arc = lambda x, a, b, n: (not o(x, a, b, n)) if x == 0 else o(x, a, b, n)
if kw.get('plant') == '2':
    q = circle_rows.p_row; circle_rows.p_row = lambda lp, p, a, b, v, r: q(lp, p, a, b, v, {'<': '>', '>': '<', '=': '='}[r] if v == 0 else r)
exec(open(os.path.join(HERE, 'val_lambda.py')).read().split('# ---------- generators')[1].split('stats =')[0])
def true_z(P):
    z = [0.0] * lp.nv
    for p in range(n):
        L = lp.L[p]
        for k in range(n - 2):
            a, b = P[L[k]], P[L[k + 1]]
            u = (a[0] - P[p][0], a[1] - P[p][1]); w = (b[0] - P[p][0], b[1] - P[p][1])
            z[lp.xi(p, k)] = math.acos(max(-1, min(1, (u[0]*w[0]+u[1]*w[1]) / (math.hypot(*u)*math.hypot(*w))))) / math.pi
    return z
def ev(P, tol=1e-9):
    D = {(i, j): math.dist(P[i], P[j]) for i in range(n) for j in range(n)}
    def rel(p, x, v):
        a, b = D[p, x], D[p, v]; return '=' if abs(a - b) <= tol * max(a, b) else ('<' if a < b else '>')
    eqs = [(p, a, b) for p in range(n) for a, b in itertools.combinations([x for x in range(n) if x != p], 2) if rel(p, a, b) == '=']
    z = true_z(P); bad = 0; nr = 0
    for tag, d, rhs, kind, reqs in circle_rows.items_for(lp, eqs, rel) + circle_rows.p_items_for(lp, eqs, lambda v, a, b: rel(v, a, b)):
        nr += 1; val = sum(float(x) * z[k] for k, x in d.items() if k != lp.T)
        if kind == 'eq': bad += abs(val - float(rhs)) > 1e-7
        else: bad += val - float(rhs) <= 1e-12
    return bad, nr, len(eqs)
tested = badp = rows = 0; neq = 0
for t in range(count):
    name, g = gens[t % len(gens)]
    for _ in range(300):
        P = g()
        if V.strictly_convex(P): break
    else: continue
    b, nr, ne = ev(P); tested += 1; badp += (b > 0); rows += nr; neq += ne
P = regular(); b, nr, ne = ev(P); tested += 1; badp += b > 0; rows += nr
print(f"n={n} plant={kw.get('plant','0')}: {tested} polygons, {rows} K rows evaluated (mean equalities {neq/max(1,tested):.1f}), {badp} polygons with a violated row")
