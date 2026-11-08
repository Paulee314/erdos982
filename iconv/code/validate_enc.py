#!/usr/bin/env python3
"""No-over-pruning test of the I_conv CNF (same build as iconv_sat.py / proof_check.py): for real strictly convex
polygons with exactly known distance ties (subsets of regular N-gons, with or without the centre, cyclically
relabelled and mirrored), assume every E/LT literal of the polygon and the cardinality 'objective >= Z(P)' (resp.
T_sets(P)); the CNF (+ families) must be SAT.  A single UNSAT = an invalid clause somewhere.
Distances: exact class label (chord index d = min(k, N-k), radius == chord iff 6d = N); order by float value of the
label (labels are distinct reals, separation >= ~1e-3 here)."""
import sys, os, random, itertools, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
from proof_check import build
from pysat.solvers import Cadical153
from geom import subset_Z


def poly_labels(N, S, centre, rot, mirror):
    key = [('s', s) for s in sorted(S)] + ([('O',)] if centre else [])
    n = len(key)
    order = list(range(n))
    if mirror: order = order[::-1]
    order = order[rot:] + order[:rot]          # vertex i of the labelled polygon = key[order[i]]
    K = [key[o] for o in order]
    def lab(a, b):
        ka, kb = K[a], K[b]
        if ka[0] == 'O' or kb[0] == 'O': return 1.0
        d = (ka[1] - kb[1]) % N; d = min(d, N - d)
        return 1.0 if 6 * d == N else 2 * math.sin(math.pi * d / N)
    return n, lab


def run(n, trials, seed=0, sets=False):
    rng = random.Random(seed)
    enc, cl, tot, Nobj = build(n, 1, ['G', 'X', 'O'], sets)
    s = Cadical153(bootstrap_with=cl)
    bad = 0; done = 0; maxZ = 0
    for t in range(trials):
        centre = rng.random() < 0.6
        if centre:
            N = rng.choice([12, 18, 24, 30, 36, 13, 20]); half = (N - 1) // 2 if N % 2 else N // 2 - 1
            if half + 1 < n - 1: continue
            S = [0] + sorted(rng.sample(range(1, half + 1), n - 2))
        else:
            N = rng.choice([n, n + 1, 2 * n, 12, 18, 24]);
            if N < n: continue
            S = sorted(rng.sample(range(N), n))
        nn, lab = poly_labels(N, S, centre, rng.randrange(n), rng.random() < 0.5)
        Z, per, eq = subset_Z(N, S, centre)
        obj = Z - 2 * eq if sets else Z
        assum = []
        pairs = enc.pairs
        for p, q in itertools.combinations(range(len(pairs)), 2):
            a, b = lab(*pairs[p]), lab(*pairs[q])
            if abs(a - b) < 1e-12: assum.append(enc.E(p, q))
            else:
                assum.append(-enc.E(p, q))
                assum.append(enc.LT(p, q) if a < b else enc.LT(q, p))
        k = Nobj - obj
        if k < len(tot.rhs): assum.append(-tot.rhs[k])
        ok = s.solve(assumptions=assum)
        done += 1; maxZ = max(maxZ, obj)
        if not ok:
            bad += 1; print('UNSAT on real polygon!', N, S, centre, Z, flush=True)
    print(f'n={n} sets={sets}: {done} polygons with exact ties tested, {bad} wrongly excluded; max objective seen {maxZ}')
    return bad


if __name__ == '__main__':
    n = int(sys.argv[1]); trials = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    run(n, trials, sets='--sets' in sys.argv)
