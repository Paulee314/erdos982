"""Enumerate inclusion-minimal local-equality sets (as sprime_fams 'min') under base + families + learned clauses
(with dihedral images). Usage: probe_min.py n FAMS seconds out.txt files..."""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'sat')); sys.path.insert(0, HERE)
from testA_sat import build
from angle_fams import add_families
from cegar2 import norm_lit
from pysat.solvers import Cadical153
n = int(sys.argv[1]); fams = set(sys.argv[2]); tl = float(sys.argv[3]); out = sys.argv[4]; t0 = time.time()
enc, _, _ = build(n, 'S', 'lex'); ex, V = add_families(enc, fams, violator=True); S = V['s']; pr, LT, E = enc.pr, enc.LT, enc.E
def var(l):
    if l[0] == 'S': return S[l[1]] if l[2] else -S[l[1]]
    _, u, v, w, rel = l; a, b = pr(u, v), pr(u, w)
    return E(a, b) if rel == '=' else (LT(a, b) if rel == '<' else LT(b, a))
s = Cadical153(bootstrap_with=enc.clauses + ex); seen = set(); k = 0
for fn in sys.argv[5:]:
    for line in open(fn):
        try: J = json.loads(line)
        except Exception: continue
        base = [tuple(x) for x in J['lits']] if 'lits' in J else [('L',) + tuple(x) for x in J.get('core', [])]
        if not base: continue
        for r in range(n):
            for o in (1, -1):
                g = lambda x: (r + o * x) % n
                c = tuple(sorted(-var(norm_lit(('L', g(l[1]), g(l[2]), g(l[3]), l[4])) if l[0] == 'L' else ('S', g(l[1]), l[2])) for l in base))
                h = hash(c)
                if h in seen: continue
                seen.add(h); s.add_clause(list(c)); k += 1
print(f"loaded {k} clauses, {time.time()-t0:.0f}s", flush=True); t1 = time.time()
lits = enc.lits; nsol = 0; f = open(out, 'w'); complete = False
while time.time() - t1 < tl:
    if not s.solve(): complete = True; break
    m = set(x for x in s.get_model() if x > 0); cur = [x for x in lits if x in m]
    while True:
        cs = set(cur); off = [-x for x in lits if x not in cs]
        sel = enc.pool.id(('shrink', nsol, len(cur))); s.add_clause([-sel] + [-x for x in cur])
        if s.solve(assumptions=off + [sel]):
            mm = set(x for x in s.get_model() if x > 0); cur = [x for x in lits if x in mm]; m = mm
        else: s.add_clause([-sel]); break
    s.add_clause([-x for x in cur]); nsol += 1; f.write(f"{enc.structure(m)} | eqs {len(cur)}\n"); f.flush()
print(f"PROBE n={n}: {nsol} minimal sets in {time.time()-t1:.0f}s, complete={complete}", flush=True)
