#!/bin/bash
# End-to-end check of "no strictly convex 10-gon violates S'" (modulo soundness of the documented clause families).
# Needs: python3 with python-sat, a compiled drat-trim (path in $DRAT, default ../../drat-trim/drat-trim).
set -e
cd "$(dirname "$0")"
DRAT=${DRAT:-../../drat-trim/drat-trim}
echo "[1] exact Farkas certificates of every Lambda clause (independent checker, rational arithmetic)"
python3 code/check_lambda_certs.py 10 lambda_clauses_n10.jsonl | tail -1
echo "[2] regenerate the CNF from the generators + the Lambda clause file and compare with the shipped CNF"
python3 code/regen_cnf.py lambda_clauses_n10.jsonl regen.cnf
python3 - <<'PY'
def cls(fn):
    out = []
    for l in open(fn):
        if l[0] in 'pc': continue
        out.append(tuple(sorted(int(x) for x in l.split()[:-1])))
    return sorted(out)
a, b = cls('regen.cnf'), cls('sprime10_F_lambda.cnf')
print("    regenerated == shipped (as clause multisets):", a == b, f"({len(a)} clauses)")
assert a == b
PY
echo "[3] DRUP refutation of the shipped CNF"
$DRAT sprime10_F_lambda.cnf sprime10_F_lambda.drup -t 50000 | tr "\r" "\n" | grep -E "s VERIFIED|s NOT VERIFIED|lemmas in core"
sha256sum sprime10_F_lambda.cnf sprime10_F_lambda.drup lambda_clauses_n10.jsonl
