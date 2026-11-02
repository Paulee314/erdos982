#!/usr/bin/env python3
"""Re-certify, piece by piece, the job-C batches whose batch proof was not accepted by both checkers.
Why: cube982p.py adds the unit (-act_i) with add_clause() after each assumption-UNSAT. If CaDiCaL did not itself log that
unit as a lemma, later lemmas are not RUP for the checker (drat-trim then needs a RAT step; cake_lpr rejected those).
Here every piece gets its own CNF = batch_cnf(enc, cubes, [i]) (base + the piece's clauses guarded by act_i + the unit clause
(act_i)), solved by a FRESH CaDiCaL with proof tracing and no assumptions and no clauses added after a solve. If the piece is
satisfiable, the structure is recorded, its blocking clause (over the E literals) is appended to the CNF, and a fresh solver is
run again, until UNSAT. CNF and proof are written, checked with chk.sh (drat-trim, then cake_lpr on drat-trim's LRAT), and a
manifest line is written: piece, structures, number of blocking clauses, CNF sha256, proof sha256, verdict.
The piece numbering is the cover's (setup() of cube982p.py), so the CNF can be regenerated from (cover, piece, blocks file).
Usage: recert.py exact|below|atmost jobs.txt worker W   (jobs.txt: one piece index per line)"""
import sys, os, hashlib, subprocess, time
R = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, R)
from cube982p import setup, batch_cnf, write_cnf
from pysat.solvers import Cadical153
cov, jobs, me, W = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
ATMOST = cov == 'atmost'
BELOW = cov == 'below'
out = os.path.join(R, f'recert_{cov}'); os.makedirs(out, exist_ok=True)
pieces = [int(l) for l in open(jobs) if l.strip()][me::W]
man = open(os.path.join(out, f'manifest_{me}.txt'), 'a')
done = set()
for f in os.listdir(out):
    if f.startswith('manifest_'):
        for l in open(os.path.join(out, f)):
            w = l.split()
            if len(w) > 2 and w[-1] == 'ACCEPT': done.add(int(w[1]))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
for i in pieces:
    if i in done: continue
    t0 = time.time()
    enc, cubes, keep = setup(int(os.environ.get('N', 12)), int(os.environ.get('K', 5)), BELOW, ATMOST)         # fresh encoding per piece: the numbering depends only on (cover, piece)
    assert keep[i], i
    F, acts = batch_cnf(enc, cubes, [i], BELOW); nv = enc.pool.top
    blocks = []; sols = []
    while True:
        s = Cadical153(bootstrap_with=F + blocks, with_proof=True)
        if s.solve():
            m = set(x for x in s.get_model() if x > 0); sols.append(enc.structure(m)); blocks.append(enc.block_clause(m)); s.delete(); continue
        proof = s.get_proof(); s.delete(); break
    name = f'{cov}_p{i}'; cnf = os.path.join(out, name + '.cnf'); prf = os.path.join(out, name + '.drup')
    write_cnf(cnf, F + blocks, nv)
    with open(prf, 'w') as f: f.write('\n'.join(proof) + '\n')
    if sols:
        with open(os.path.join(out, name + '.sol'), 'w') as f: f.write('\n'.join(sols) + '\n')
        with open(os.path.join(out, name + '.blocks'), 'w') as f: f.write('\n'.join(' '.join(map(str, b)) + ' 0' for b in blocks) + '\n')
    r = subprocess.run([os.path.join(R, 'chk.sh'), cnf, prf], capture_output=True, text=True)
    verdict = 'ACCEPT' if r.returncode == 0 and 'ACCEPT' in r.stdout else 'REJECT'
    line = f"piece {i} structures {len(sols)} blocks {len(blocks)} clauses {len(F)+len(blocks)} vars {nv} cnf_sha256 {sha(cnf)} proof_sha256 {sha(prf)} t {time.time()-t0:.1f} {verdict}"
    man.write(line + '\n'); man.flush(); print(line, flush=True)
    os.remove(cnf); subprocess.run(['gzip', '-1', '-f', prf])
