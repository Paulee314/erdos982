#!/usr/bin/env python3
"""TEST A (Erdős #982, strategy 1 "injective half"): SAT enumeration of equal-distance patterns that violate S' or Q at
EVERY vertex, under all the convexity / distance-order clauses of the n <= 13 verification, WITHOUT the class-count bound.

Encoding = e982lib.Enc(n, K=n-1, order=True, atmost=True)   ("at most n-1 classes" is vacuous, i.e. no class-count bound)
  base: E transitivity, F1, F2, order axioms (LT total preorder), F2-order, chord monotonicity, four-in-a-class.
Added, for every vertex p (h = floor(n/2), indices mod n, boundary order):
  mode S : OR_{u<v in {p+1..p+h}} e(p,u,v)      and      OR_{u<v in {p-h..p-1}} e(p,u,v)       ("S'(p) fails")
  mode Q : aux t(p,a,b,c) -> e(p,a,b) & e(p,a,c);  OR_{a<b<c} t(p,a,b,c)                         ("p has a class >= 3")
Symmetry breaking (sym=lex): generic dihedral lex-leader on the vector of LOCAL literals
  X = [e(t, t+a, t+b) : t = 0..n-1, 1 <= a < b <= n-1]   and   X <=_lex X o g  for all 2n-1 non-identity g in D_n.
  Sound for any D_n-invariant clause set (all clauses above are D_n-invariant: S/Q windows map prefix <-> suffix under
  reflection, and both are imposed); it does not depend on any class count.  Exactly one solution per D_n-orbit of
  local patterns.  sym=none: no symmetry breaking.
Enumeration:
  enum=full : block each local pattern exactly (all n*C(n-1,2) local literals)  -> one line per dihedral orbit.
  enum=min  : first shrink the model to an inclusion-minimal set of local equalities (re-solve with assumptions
              'all equalities outside the current set false' + clause 'drop at least one'), then block every superset
              ('pos' blocking).  Sound for the realizability question because S/Q violation is monotone in the equalities:
              every real polygon violating S'/Q everywhere has a pattern that contains some reported minimal set.
Output: one pattern per line (n restricted-growth strings, one per centre; the e982lib format) + a summary line.
Usage: testA_sat.py n S|Q full|min out.txt [sym=lex|none] [maxsol=N] [timelimit=SECONDS]"""
import sys, os, time, itertools, resource
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e982lib import Enc
from pysat.solvers import Cadical153

def build(n, mode, sym):
    enc = Enc(n, n - 1, order=True, atmost=True)
    cl = enc.clauses; h = n // 2; pool = enc.pool
    n_base = len(cl)
    for p in range(n):
        if mode == 'S':
            for W in ([(p + i) % n for i in range(1, h + 1)], [(p - i) % n for i in range(1, h + 1)]):
                cl.append([enc.e(p, u, v) for u, v in itertools.combinations(W, 2)])
        elif mode == 'Q':
            others = [(p + i) % n for i in range(1, n)]; big = []
            for a, b, c in itertools.combinations(others, 3):
                t = pool.id(('trip', p, a, b, c)); big.append(t)
                cl += [[-t, enc.e(p, a, b)], [-t, enc.e(p, a, c)]]
            cl.append(big)
        else: raise ValueError(mode)
    n_mode = len(cl) - n_base
    def vec(v, o):
        return [enc.e((v + o * t) % n, (v + o * (t + a)) % n, (v + o * (t + b)) % n)
                for t in range(n) for a in range(1, n) for b in range(a + 1, n)]
    n_sym = 0
    if sym == 'lex':
        X = vec(0, 1); m = len(X); c0 = len(cl)
        for v in range(n):
            for o in (1, -1):
                if (v, o) == (0, 1): continue
                Y = vec(v, o); prev = None
                for i in range(m):
                    # eq_prev and X[i] -> Y[i]
                    cl.append(([-prev] if prev else []) + [-X[i], Y[i]])
                    if i == m - 1: break
                    nxt = pool.id(('lexeq', v, o, i))
                    pre = [prev] if prev else []
                    # nxt <-> prev & (X[i] <-> Y[i])
                    if prev: cl.append([-nxt, prev])
                    cl += [[-nxt, -X[i], Y[i]], [-nxt, X[i], -Y[i]],
                           [nxt] + [-x for x in pre] + [X[i], Y[i]], [nxt] + [-x for x in pre] + [-X[i], -Y[i]]]
                    prev = nxt
        n_sym = len(cl) - c0
    return enc, n_mode, n_sym

def main():
    n = int(sys.argv[1]); mode = sys.argv[2]; enum = sys.argv[3]; out = sys.argv[4]
    kw = dict(a.split('=') for a in sys.argv[5:])
    sym = kw.get('sym', 'lex'); maxsol = int(kw.get('maxsol', 10**9)); tl = float(kw.get('timelimit', 1e18))
    t0 = time.time()
    enc, n_mode, n_sym = build(n, mode, sym)
    lits = enc.lits
    print(f"n={n} mode={mode} enum={enum} sym={sym}: {len(enc.clauses)} clauses ({n_mode} mode, {n_sym} symmetry), "
          f"{enc.pool.top} vars, {len(lits)} local literals; build {time.time()-t0:.1f}s", flush=True)
    s = Cadical153(bootstrap_with=enc.clauses)
    nsol = 0; complete = False; nsolve = 0
    with open(out, 'w') as f:
        f.write(f"# testA_sat.py n={n} mode={mode} enum={enum} sym={sym}\n")
        while True:
            if time.time() - t0 > tl or nsol >= maxsol: break
            nsolve += 1
            if not s.solve(): complete = True; break
            m = set(x for x in s.get_model() if x > 0)
            if enum == 'min':
                cur = [x for x in lits if x in m]
                while True:
                    off = [-x for x in lits if x not in set(cur)]
                    sel = enc.pool.id(('shrink', nsol, len(cur)))      # fresh selector for the 'drop one' clause
                    s.add_clause([-sel] + [-x for x in cur])
                    nsolve += 1
                    if s.solve(assumptions=off + [sel]):
                        mm = set(x for x in s.get_model() if x > 0); cur = [x for x in lits if x in mm]; m = mm
                    else:
                        s.add_clause([-sel]); break
                s.add_clause([-x for x in cur])                       # block every superset
                f.write(f"{enc.structure(m)} | eqs {len(cur)}\n")
            else:
                s.add_clause(enc.block_clause(m))
                f.write(enc.structure(m) + '\n')
            nsol += 1
            f.flush()
            if nsol % 100 == 0:
                print(f"  {nsol} patterns, {time.time()-t0:.0f}s", flush=True)
        hwm = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // (1024 * 1024 if sys.platform == 'darwin' else 1024)
        summ = f"# SUMMARY n={n} mode={mode} enum={enum} sym={sym} patterns={nsol} complete={complete} solves={nsolve} wall={time.time()-t0:.1f}s peakMB={hwm}"
        f.write(summ + '\n')
    print(summ, flush=True)

if __name__ == '__main__': main()
