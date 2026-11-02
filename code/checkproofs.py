#!/usr/bin/env python3
"""Check the DRUP proofs written by cube982p.py: for every batch listed in a worker's done file, regenerate the batch CNF
(deterministically, from the same code path), run a DRUP checker on CNF + proof, and write one manifest line per batch:
cover, residue, batch, piece range, number of pieces, clause count, proof size, SHA-256 of the proof, checker verdict.
Usage: checkproofs.py n K residue W batch_size outdir [--checker ./rupcheck | 'drat-trim'] [--keepcnf]
Env:   BELOW=1 / ATMOST=1 as cube982p.py.  Exit status 0 iff every batch is ACCEPTed and had final_unsat True."""
import sys, os, subprocess, hashlib, time, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cube982p import setup, batch_cnf, write_cnf
n = int(sys.argv[1]); K = int(sys.argv[2]); RES = int(sys.argv[3]); W_N = int(sys.argv[4]); BS = int(sys.argv[5]); OUT = sys.argv[6]
CHECKER = sys.argv[sys.argv.index('--checker') + 1] if '--checker' in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rupcheck')
BELOW = os.environ.get('BELOW') == '1'; ATMOST = os.environ.get('ATMOST') == '1'
enc, cubes, keep = setup(n, K, BELOW, ATMOST)
mine = [i for i in range(len(cubes)) if i % W_N == RES and keep[i]]
batches = [mine[b:b + BS] for b in range(0, len(mine), BS)]
tag = 'below' if BELOW else 'atmost' if ATMOST else 'exact'
done = {}
for l in open(os.path.join(OUT, f'w{RES}.done')):
    w = l.split()
    if w and w[0] == 'batch': done[int(w[1])] = l.strip()
allok = True; man = open(os.path.join(OUT, f'manifest_w{RES}.txt'), 'a')
for bi, batch in enumerate(batches):
    t0 = time.time(); F, acts = batch_cnf(enc, cubes, batch, BELOW); nv = enc.pool.top    # built for every batch: same numbering as cube982p.py
    if bi not in done: continue
    name = f'{tag}_w{RES}_b{bi}'; proof = os.path.join(OUT, name + '.drup')
    if not os.path.exists(proof): print(f"{name}: NO PROOF FILE"); allok = False; continue
    cnf = os.path.join(OUT, name + '.cnf')
    write_cnf(cnf, F, nv)
    r = subprocess.run([CHECKER, cnf, proof], capture_output=True, text=True)
    verdict = 'ACCEPT' if ('ACCEPT' in r.stdout and r.returncode == 0) or ('s VERIFIED' in r.stdout) else 'REJECT'
    h = hashlib.sha256(open(proof, 'rb').read()).hexdigest()
    unsat = 'final_unsat True' in done[bi]
    line = f"{tag} w{RES} b{bi} pieces {batch[0]}..{batch[-1]} n_pieces {len(batch)} clauses {len(F)} vars {nv} proof_bytes {os.path.getsize(proof)} sha256 {h} final_unsat {unsat} checker {verdict} check_s {time.time()-t0:.1f}"
    print(line, flush=True); man.write(line + '\n'); man.flush()
    allok &= verdict == 'ACCEPT' and unsat
    if '--keepcnf' not in sys.argv: os.remove(cnf)
print('ALL ACCEPTED' if allok else 'PROBLEM'); sys.exit(0 if allok else 1)
