#!/usr/bin/env python3
"""Exact Farkas certificates for Lambda/Lambda-MEC literal-set records ({'lits': ...}).
Usage: certify_lits.py n in.jsonl out.jsonl"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from angle_lp import AngleLP, exact_certificate, verify_certificate
from cegar2 import rows_for_lits
import delta_rows
n = int(sys.argv[1]); lp = AngleLP(n); base = lp.base_rows(); ok = fail = 0; DLP = delta_rows.DeltaLP(n)
with open(sys.argv[3], 'w') as g:
    for line in open(sys.argv[2]):
        J = json.loads(line)
        lits = [tuple(x) for x in J['lits']]
        rows = rows_for_lits(lp, base, lits); cert = exact_certificate(lp, rows)
        if cert is not None and verify_certificate(lp, rows, cert):
            J['cert'] = {str(rows[i][3]): str(y) for i, y in cert.items()}; ok += 1
        elif (dc := DLP.certificate(DLP.base + delta_rows.rel_tags(lits))) is not None:
            J['cert'] = dc; ok += 1
        else: fail += 1; J['cert'] = None
        g.write(json.dumps(J) + '\n')
print(f"n={n}: certified {ok}, failed {fail}")
