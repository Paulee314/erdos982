#!/usr/bin/env python3
"""C5 check: does every LP-feasible local pattern in OUT.jsonl.feasible equal (up to D_n) the local equality pattern
of R_n (n odd) / A_n (n even)?   Usage: c5_match.py n file.feasible"""
import sys, json, math
from c4_sanity import regular, biregular


def pattern(P, perm, tol=1e-9):
    n = len(P); Q = [P[perm[i]] for i in range(n)]; line = []
    for c in range(n):
        others = [v for v in range(n) if v != c]; lab = {}; st = ''
        for v in others:
            for u in others:
                if u == v: lab[v] = len(set(lab.values())); break
                if abs(math.dist(Q[c], Q[u]) - math.dist(Q[c], Q[v])) < tol: lab[v] = lab[u]; break
            st += str(lab[v])                     # same format as Enc.structure
        line.append(st)
    return ' '.join(line)


n = int(sys.argv[1]); P = regular(n) if n % 2 else biregular(n)
ref = {pattern(P, [(r + o * i) % n for i in range(n)]) for r in range(n) for o in (1, -1)}
tot = ok = 0
for line in open(sys.argv[2]):
    J = json.loads(line); tot += 1
    hit = J['pattern'] in ref; ok += hit
    if not hit: print("OTHER pattern:", J['pattern'], 'sum t', J.get('sumt'))
print(f"n={n}: {tot} LP-feasible patterns at sum t = C(n,2); {ok} match {'R' if n % 2 else 'A'}_{n}; {tot-ok} others")
