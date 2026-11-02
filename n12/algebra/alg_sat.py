#!/usr/bin/env python3
"""Algebra step for #982 survivors with DISTINCTNESS SATURATION (needed at n = 12, see FEASIBILITY.md §6d).

A pattern (one line of n restricted-growth strings, one per centre) gives the equalities d(c,u)^2 = d(c,v)^2 for every
pair u, v in the same class at centre c.  With v0 = (0,0), v1 = (1,0) they generate an ideal I in Q[x2..x_{n-1}, y2..y_{n-1}].
At n = 8, 10 every pattern had std(I) = {1} (no complex solution at all).  At n = 12 the first order-SAT model of the
theory agent has std(I) != {1}: its only solutions have coincident vertices, which the equalities alone cannot exclude.
A real strictly convex polygon has d(i,j)^2 > 0 for every pair i != j, so it lies in V(I) minus V(d_ij^2) for every pair,
i.e. in V(I : (prod d_ij^2)^inf).  This script therefore
  1. computes std(I); if {1}, certifies 1 = sum c_i f_i (as sing982.py);
  2. otherwise saturates greedily: at each round, for every pair {i,j} the (dim, vdim) of I : (d_ij^2)^inf is computed
     and the pair that removes the most is kept (the chosen pairs are the coincidences that actually occur);
     stops when the saturated ideal is {1} or when no pair removes anything (genuine algebraic survivor -> realsolve);
  3. certifies: with g = prod_{chosen} d_ij^2, finds the least m with g^m in I (reduce by std(I)) and cofactors
     g^m = sum c_i f_i (lift), re-verified by exact expansion in sympy.  The certificate proves: every complex solution
     of the equalities has two coincident vertices among the chosen pairs; hence no polygon with distinct vertices.
Usage: alg_sat.py n patterns.txt [max] [--outdir certs]      (pattern lines may carry " | ..." comments)
Output per pattern: std={1} or not; chosen pairs; exponent m; cofactor size; VERIFIED / FAILED / SURVIVOR."""
import sys, os, time, subprocess, itertools, re
import sympy as sp
n = int(sys.argv[1]); pats = [l.split('|')[0].strip() for l in open(sys.argv[2]) if l.strip() and not l.startswith('#')]
pats = [p for p in pats if len(p.split()) == n]
mx = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else len(pats); pats = pats[:mx]
outdir = sys.argv[sys.argv.index('--outdir') + 1] if '--outdir' in sys.argv else 'certs_sat'; os.makedirs(outdir, exist_ok=True)
VARS = [f'x{i}' for i in range(2, n)] + [f'y{i}' for i in range(2, n)]
def pt(i): return ('0', '0') if i == 0 else ('1', '0') if i == 1 else (f'x{i}', f'y{i}')
def d2(a, b):
    (ax, ay), (bx, by) = pt(a), pt(b); return f'(({ax})-({bx}))^2+(({ay})-({by}))^2'
def eqs_of(line):
    parts = line.split(); eqs = []
    for c in range(n):
        others = [v for v in range(n) if v != c]; lab = dict(zip(others, parts[c])); groups = {}
        for v in others: groups.setdefault(lab[v], []).append(v)
        for g in groups.values():
            for v in g[1:]: eqs.append((c, g[0], v))
    return eqs
def sing(script, timeout=3600):
    r = subprocess.run([os.environ.get('SINGULAR', 'Singular'), '-q'], input='LIB "elim.lib"; option(redSB); ' + script + ' quit;', capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0: raise RuntimeError(r.stderr[-2000:])
    return r.stdout
PAIRS = [(i, j) for i in range(n) for j in range(i + 1, n) if (i, j) != (0, 1)]
for k, line in enumerate(pats):
    t0 = time.time(); eqs = eqs_of(line); tt = {}
    polys = [f'({d2(c,u)})-({d2(c,v)})' for c, u, v in eqs]
    head = f'ring R = 0, ({",".join(VARS)}), dp; ideal I = {", ".join(polys)}; ideal G = std(I);'
    out = sing(head + ' print(dim(G)); if (dim(G) == 0) { print(vdim(G)); } else { print(-1); } print(size(G) == 1 && G[1] == 1);')
    dim0, vdim0, unit = [int(x) for x in out.split()[:3]]
    chosen = []; state = (dim0, vdim0)
    def key_of(d, vd): return (-1, 0) if d == -1 else (d, vd if d == 0 else 10**9)   # smaller = fewer solutions left ({1} has dim -1)
    if not unit:
        # greedy saturation by single squared distances
        while True:
            best = None
            # one Singular run tests every remaining pair against the current saturated ideal S
            sat_chain = ''.join(f' S = sat(S, ideal({d2(i,j)}));' for i, j in chosen)
            tests = ''.join(f' T = sat(S, ideal({d2(i,j)})); T = std(T); print({i}); print({j}); print(dim(T)); if (dim(T) == 0) {{ print(vdim(T)); }} else {{ print(-1); }}' for i, j in PAIRS if (i, j) not in chosen)
            out = sing(head + ' ideal S = G; ideal T;' + sat_chain + tests)
            w = [int(x) for x in out.split()]
            for q in range(0, len(w), 4):
                i, j, d, vd = w[q:q + 4]
                if best is None or key_of(d, vd) < best[0]: best = (key_of(d, vd), (i, j), (d, vd))
            if best is None or best[0] >= key_of(*state):
                break                       # nothing removes anything: genuine algebraic survivor with distinct complex points
            chosen.append(best[1]); state = best[2]
            if state[0] == -1: break
    unit_after = unit or state[0] == -1
    if not unit_after:
        print(f"pattern {k}: std(I) dim {dim0} vdim {vdim0}; saturation by {chosen} leaves dim {state[0]} vdim {state[1]}: SURVIVOR (needs real/convexity check) ({time.time()-t0:.1f}s)", flush=True)
        continue
    # certificate: g^m in I with g = prod of chosen d_ij^2 (g = 1 if std(I) = {1}); cofactors by lift, checked in sympy
    g = '*'.join(f'({d2(i,j)})' for i, j in chosen) or '1'
    certf = f'{outdir}/cert_{k}.txt'
    if os.path.exists(certf): os.remove(certf)
    script = head + f' poly g = {g}; int m = 0; poly h = 1; while (reduce(h, G) != 0) {{ m = m + 1; h = h * g; }} print(m); matrix T = lift(I, ideal(h)); int i; for (i = 1; i <= ncols(I); i++) {{ write(":a {certf}", string(T[i,1])); }}'
    out = sing(script); m = int(out.split()[0])
    syms = sp.symbols(' '.join(VARS)); env = dict(zip(VARS, syms))
    T = [sp.sympify(s.replace('^', '**'), locals=env) for s in open(certf).read().strip().split('\n')]
    F = [sp.sympify(p.replace('^', '**'), locals=env) for p in polys]
    G = sp.sympify(g.replace('^', '**'), locals=env) ** m
    ok = sp.expand(sum(c * f for c, f in zip(T, F)) - G) == 0
    nterms = sum(len(sp.Add.make_args(sp.expand(c))) for c in T)
    print(f"pattern {k}: std(I) {'= {1}' if unit else f'dim {dim0} vdim {vdim0}'}; saturation pairs {chosen}; certificate g^{m} = sum c_i f_i with g = prod d_ij^2 over those pairs: "
          f"{'VERIFIED' if ok else 'FAILED'} ({nterms} cofactor terms, {time.time()-t0:.1f}s)", flush=True)
