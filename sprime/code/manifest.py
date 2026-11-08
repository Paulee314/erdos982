#!/usr/bin/env python3
"""Manifest for a certificate bundle: md5 of every file, clause-family counts of the certified learned clauses,
and a consistency check that every learned clause in the final CNF has a certificate record.
Usage: manifest.py bundle_dir n FAMS"""
import sys, os, json, ast, hashlib, collections
B, n, fams = sys.argv[1], int(sys.argv[2]), sys.argv[3]
out = [f"# Manifest for {os.path.abspath(B)}", ""]
out.append("## md5 of every file")
for root, _, files in sorted(os.walk(B)):
    for fn in sorted(files):
        p = os.path.join(root, fn)
        if fn.endswith('.pyc'): continue
        out.append(f"{hashlib.md5(open(p,'rb').read()).hexdigest()}  {os.path.relpath(p, B)}")
fam_of = {'pos': 'Lambda-base', 'int': 'Lambda-base', 'tri': 'Lambda-base', 'L': 'Lambda-L (side-angle)', 'K': 'K (circle)',
          'P': 'P (bisector)', 'H': 'H (hinge)', 'C': 'MEC-C', 'I': 'MEC-I', 'R': 'MEC-R'}
recs = [json.loads(l) for l in open(os.path.join(B, f'lambda_clauses_n{n}.jsonl'))]
per_family = collections.Counter(); xl = 0; sl = 0; kinds_total = collections.Counter()
for J in recs:
    fs = set()
    for k in J['cert']:
        t = ast.literal_eval(k); fs.add(fam_of.get(t[0], t[0])); kinds_total[fam_of.get(t[0], t[0])] += 1
    for f in fs: per_family[f] += 1
    xl += any(l[0] == 'X' for l in J['lits']); sl += any(l[0] == 'S' for l in J['lits'])
out += ["", "## Certified learned clauses in the final CNF", f"records: {len(recs)}",
        f"clauses with chord-pair (X) literals: {xl}; with MEC support (S) literals: {sl}",
        "clauses whose certificate uses each row family (a clause can use several):"]
for f, c in sorted(per_family.items()): out.append(f"  {f}: {c}")
# consistency: learned clauses in CNF == records
sys.path.insert(0, os.path.join(B, 'code')); sys.path.insert(0, os.path.join(B, 'sat'))
from testA_sat import build
from angle_fams import add_families
enc, _, _ = build(n, 'S', 'lex'); ex, V = add_families(enc, set(fams), violator=True)
nbase = len(enc.clauses) + len(ex)
cnf = [l for l in open(os.path.join(B, f'sprime{n}.cnf')) if l[0] not in 'pc']
out += ["", f"final CNF: {len(cnf)} clauses = {len(enc.clauses)} base + {len(ex)} families {fams} + {len(cnf)-nbase} learned; "
        f"certified records: {len(recs)}; match: {len(cnf)-nbase == len(recs)}",
        "(verify.sh step [2] regenerates the CNF from the generators + exactly these records and checks identity)"]
open(os.path.join(B, 'MANIFEST.md'), 'w').write('\n'.join(out) + '\n'); print('\n'.join(out[-12:]))
