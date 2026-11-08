#!/usr/bin/env python3
"""Empirical soundness test of mec_rows (Lambda-MEC). Polygons: (a) random strictly convex (Valtr / near-circle),
(b) 'circle' polygons: m >= 3 vertices exactly on the unit circle, the rest strictly inside, strictly convex,
centre inside conv(support) (so the unit circle is the MEC and we are in case (M)), incl. regular-ish configurations.
For each case-(M) polygon: compute true MEC support, build all items, evaluate on the TRUE angles: eq rows within 1e-9,
strict rows with positive margin. plant=1 flips the side rule of I rows (must be caught).
Usage: val_mec.py n count seed [plant=1]"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sat')); sys.path.insert(0, HERE)
import validate as V
from angle_lp import AngleLP
import mec_rows
args = [a for a in sys.argv[1:] if '=' not in a]; kw = dict(a.split('=') for a in sys.argv[1:] if '=' in a)
n, count, seed = int(args[0]), int(args[1]), int(args[2]); plant = int(kw.get('plant', 0))
rng = random.Random(seed); lp = AngleLP(n)
if plant == 1:
    orig = mec_rows.same_side
    mec_rows.same_side = lambda x, y, a, b, n: not orig(x, y, a, b, n)

def true_z(P):
    z = [0.0] * lp.nv
    for p in range(n):
        L = lp.L[p]
        for k in range(n - 2):
            a, b = P[L[k]], P[L[k + 1]]
            u = (a[0] - P[p][0], a[1] - P[p][1]); w = (b[0] - P[p][0], b[1] - P[p][1])
            c = (u[0] * w[0] + u[1] * w[1]) / (math.hypot(*u) * math.hypot(*w))
            z[lp.xi(p, k)] = math.acos(max(-1, min(1, c))) / math.pi
    return z

def circle_poly():
    m = rng.randint(3, n)
    ang = sorted(rng.uniform(0, 2 * math.pi) for _ in range(n))
    if rng.random() < 0.3:   # near-regular
        ang = sorted((2 * math.pi * i / n + rng.uniform(-0.2, 0.2) / n) % (2 * math.pi) for i in range(n))
    S = set(rng.sample(range(n), m))
    return [((1.0 if i in S else rng.uniform(0.9, 0.999)) * math.cos(a), (1.0 if i in S else rng.uniform(0.9, 0.999)) * math.sin(a)) for i, a in enumerate(ang)]

def evaluate(P):
    mc = V.mec(P)
    if mc is None: return None
    O, R = mc
    sup = [abs(math.dist(O, p) - R) <= 1e-9 * R for p in P]
    T = [v for v in range(n) if sup[v]]
    if len(T) < 3: return None
    if any(abs(math.dist(P[a], P[b]) - 2 * R) <= 1e-9 * R for a in T for b in T if a < b): return None
    z = true_z(P); bad = []; nrows = 0
    for tag, d, rhs, kind, reqs in mec_rows.items_for(lp, sup):
        nrows += 1
        val = sum(x * z[k] for k, x in d.items() if k != lp.T)
        if kind == 'eq':
            if abs(val - rhs) > 1e-8: bad.append((tag, val - rhs))
        elif val - float(rhs) <= 1e-12: bad.append((tag, val - float(rhs)))
    return bad, nrows, len(T)

tested = badp = rows = 0; first = None; msz = {}
gens = [lambda: V.valtr(n, rng), lambda: V.near_circle(n, rng, 0.05), circle_poly, circle_poly, circle_poly]
for t in range(count):
    for _ in range(200):
        P = gens[t % len(gens)]()
        if V.strictly_convex(P): break
    else: continue
    r = evaluate(P)
    if r is None: continue
    bad, nr, m = r; tested += 1; rows += nr; msz[m] = msz.get(m, 0) + 1
    if bad:
        badp += 1
        if first is None: first = bad[:3]
print(f"n={n} plant={plant}: {tested} case-(M) polygons, {rows} rows evaluated, {badp} polygons with a violated row; "
      f"support sizes {sorted(msz.items())}")
if first: print("  first failure:", first)
