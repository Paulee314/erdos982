"""Lift n-gon cores without support literals to (n+1)-gon clauses: a core on vertex set U is a k-point lemma (its
Lambda rows only involve U); insert the new vertex in any of the n gaps (order-preserving maps Z_n -> Z_{n+1}).
Only cores whose literal set is LP-infeasible on the |U|-gon alone are kept (checked with the angle LP).
Usage: lift.py n maxk out.jsonl files..."""
import sys, json
sys.path.insert(0, '.')
from angle_lp import AngleLP
from cegar2 import rows_for_lits, norm_lit
n = int(sys.argv[1]); maxk = int(sys.argv[2]); out = open(sys.argv[3], 'w')
lps = {}; seen = set(); nin = nk = nout = 0
def infeas(k, lits):
    if k not in lps: lp = AngleLP(k); lps[k] = (lp, lp.base_rows())
    lp, base = lps[k]; tm, _ = lp.solve(rows_for_lits(lp, base, lits), want_dual=False); return tm <= 1e-9
for fn in sys.argv[4:]:
    for line in open(fn):
        try: J = json.loads(line)
        except Exception: continue
        lits = [tuple(x) for x in J['lits']] if 'lits' in J else [('L',) + tuple(x) for x in J.get('core', [])]
        if not lits or any(l[0] == 'S' for l in lits): continue
        nin += 1
        U = sorted({v for l in lits for v in l[1:4]}); k = len(U)
        if k > maxk: continue
        key = tuple(sorted(lits))
        if key in seen: continue
        seen.add(key)
        rel = {v: i for i, v in enumerate(U)}
        sub = [norm_lit(('L', rel[l[1]], rel[l[2]], rel[l[3]], l[4])) for l in lits]
        if not infeas(k, sub): continue
        nk += 1
        for g in range(n):            # new vertex inserted after old vertex g: old v -> v if v <= g else v+1
            f = lambda v: v if v <= g else v + 1
            out.write(json.dumps({'lits': [list(norm_lit(('L', f(l[1]), f(l[2]), f(l[3]), l[4]))) for l in lits]}) + '\n'); nout += 1
print(f"{nin} support-free cores read, {nk} distinct with k <= {maxk} infeasible on their own vertex set, {nout} lifted clauses")
