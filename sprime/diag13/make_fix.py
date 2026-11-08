# Builds code/final_certify2_fix.py from code/final_certify2.py.
# Fix: round-2 matching of drat-trim core clauses to learned-clause keys ignored the fact that drat-trim
# removes duplicate literals, so keys whose clause had a repeated variable were silently dropped from round 2.
# Changes: (1) match core clauses by literal SET; (2) dedupe literals in round-2 clauses; (3) optionally reuse an
# existing round-1 core (REUSE_R1=1) after checking that every core clause is a base clause or a learned clause.
import sys
src = open(sys.argv[1]).read()

old_r1 = 'if not solve_check(base_cl + lam, OUT + \'_r1\', OUT + \'_r1.core\'): sys.exit("round 1 failed")'
new_r1 = '''if os.environ.get('REUSE_R1') == '1' and os.path.exists(OUT + '_r1.core'):
    log("REUSE_R1: using existing", OUT + '_r1.core')
    baseset = {frozenset(c) for c in base_cl}; lamset = {frozenset(c) for c in lam}; unk = 0; nc = 0
    for line in open(OUT + '_r1.core'):
        if line[0] in 'pc': continue
        c = frozenset(int(x) for x in line.split()[:-1]); nc += 1
        if c not in baseset and c not in lamset: unk += 1
    log(f"REUSE_R1 sanity: {nc} core clauses, {unk} not found among base or learned clauses")
    if unk: sys.exit("REUSE_R1 sanity failed: core does not match this round-1 CNF")
elif not solve_check(base_cl + lam, OUT + '_r1', OUT + '_r1.core'): sys.exit("round 1 failed")'''
assert src.count(old_r1) == 1
src = src.replace(old_r1, new_r1)

old_neg = "neg = {tuple(sorted(c)): k for c, k in zip(lam, keys)}"
new_neg = "neg = {}\nfor c, k in zip(lam, keys): neg.setdefault(frozenset(c), k)"
assert src.count(old_neg) == 1
src = src.replace(old_neg, new_neg)

old_c = "    c = tuple(sorted(int(x) for x in line.split()[:-1]))\n    if c in neg: used.append(keys[neg[c]])"
new_c = "    c = frozenset(int(x) for x in line.split()[:-1])\n    if c in neg: used.append(keys[neg[c]])"
assert src.count(old_c) == 1
src = src.replace(old_c, new_c)

old_g = "good.append([-var(tuple(x)) for x in json.loads(line)['lits']])"
new_g = "good.append(sorted({-var(tuple(x)) for x in json.loads(line)['lits']}))"
assert src.count(old_g) == 1
src = src.replace(old_g, new_g)

open(sys.argv[2], 'w').write(src)
print("wrote", sys.argv[2])
