#!/usr/bin/env python3
"""Erdős #982 search, version o ("order"): cube982d.py's search with
  * the compact lex-leader symmetry breaking (same constraint as cube982d.py, ~1,200 short clauses per piece, index-independent);
  * the distance-order extension: a strict total preorder on all pair distances plus the pure-order consequences of
    convexity (F2-order: the diagonals of a convex quadrilateral sum to more than either pair of opposite sides; chord
    monotonicity on a circle; four-in-a-class short chord) -- see FEASIBILITY.md §5;
  * one solver per worker, reused across pieces (base clauses loaded once); each piece is activated by assumptions
    (its unit literals and one activation literal guarding its symmetry clauses, retired with a unit clause afterwards).
Every structure found (none expected) is written to w<id>.sol exactly as cube982d.py would, and would then need the
algebra check.  Records "i count seconds utc cpu=<cpu seconds>" per piece in w<id>.done; "i mirror 0 -" for mirror-skipped pieces.
Usage: cube982o.py n K residues W outdir [done_before]
Env:   BELOW=1   below-K part exactly as below982.py: pieces = RG strings with <= K-1 blocks at vertex 0, every other centre
                 has >= b (the piece's block count) and <= K classes, mirror skip, and NO lex-leader clauses (below982's
                 canonical choice -- vertex 0 has the fewest classes -- is not compatible with the lex-leader one).
       ATMOST=1  unified alternative: at most K classes at every centre, pieces = ALL RG strings with <= K blocks at vertex 0
                 (exactly-K and below-K together), lex-leader + mirror skip.  Covers everything BELOW + default cover.
       default:  exactly-K part as cube982d.py (exactly K classes at every centre, lex-leader, mirror skip).
       FRESH=1   fresh solver per piece (slower; the mode benchmarked in runpiece.py) instead of the incremental one.
       PROOF=dir write a DRUP proof per piece to dir/p<i>.drup (only in FRESH mode; CaDiCaL via pysat).
       ORDER=0   switch the order extension off (validation against cube982d.py only)."""
import sys, os, time, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e982lib import Enc
from pysat.solvers import Cadical153
from pysat.card import CardEnc, EncType
n = int(sys.argv[1]); K = int(sys.argv[2]); RES = sorted(int(x) for x in sys.argv[3].split(',')); W_N = int(sys.argv[4]); OUT = sys.argv[5]
W_ID = RES[0]; DONE_BEFORE = sys.argv[6] if len(sys.argv) > 6 else None
BELOW = os.environ.get('BELOW') == '1'; FRESH = os.environ.get('FRESH') == '1'; PROOF = os.environ.get('PROOF'); ATMOST = os.environ.get('ATMOST') == '1'
assert not (BELOW and ATMOST)
ORDER = os.environ.get('ORDER', '1') == '1'                 # ORDER=0: no order extension (only for validation against cube982d.py)
enc = Enc(n, K, order=ORDER, atmost=BELOW or ATMOST)
from e982lib import partitions
cubes = list(partitions(n - 1, K - 1, False)) if BELOW else list(partitions(n - 1, K, False)) if ATMOST else enc.cubes(); keep = enc.keep(cubes)
LEX = not BELOW
os.makedirs(OUT, exist_ok=True)
done_path = os.path.join(OUT, f'w{W_ID}.done'); sol_path = os.path.join(OUT, f'w{W_ID}.sol')
done = set()
for path in ([DONE_BEFORE] if DONE_BEFORE else []) + ([done_path] if os.path.exists(done_path) else []):
    for line in open(path):
        if line.strip(): done.add(int(line.split()[0]))
# below-K: at-least-b clauses for every other centre, per b, guarded by an activation literal (as below982.py)
ACT = {}
if BELOW:
    for b in range(2, K):
        a = enc.pool.id(('act', b)); ACT[b] = a
        for c in enc.V:
            if c == 0: continue
            for cl in CardEnc.atleast(lits=enc.REPS[c], bound=b, vpool=enc.pool, encoding=EncType.seqcounter).clauses:
                enc.clauses.append([-a] + cl)
print(f"n={n} K={K} {'below-K' if BELOW else 'at-most-K unified' if ATMOST else 'exactly-K'} ({'order extension' if ORDER else 'NO order extension'}, compact symmetry breaking, {'fresh' if FRESH else 'incremental'}): "
      f"{enc.pool.top} variables, {len(enc.clauses)} clauses; {len(cubes)} pieces, {sum(keep)} after mirror symmetry; residues {RES} of {W_N}; {len(done)} already done", flush=True)
s = None if FRESH else Cadical153(bootstrap_with=enc.clauses)
total = 0
for i, rg in enumerate(cubes):
    if i % W_N not in RES or i in done: continue
    if not keep[i]:
        with open(done_path, 'a') as f: f.write(f"{i} mirror 0 -\n")
        continue
    t0 = time.time(); c0 = time.process_time(); cnt = 0
    units = [cl[0] for cl in enc.unit_clauses(rg)]
    sym = enc.sym_compact(rg) if LEX else []
    if FRESH:
        F = enc.clauses + sym + [[u] for u in units]
        if BELOW and max(rg) + 1 >= 2: F.append([ACT[max(rg) + 1]])
        if PROOF:
            os.makedirs(PROOF, exist_ok=True)
            sv = Cadical153(bootstrap_with=F, with_proof=True)
        else:
            sv = Cadical153(bootstrap_with=F)
        while sv.solve():
            m = set(x for x in sv.get_model() if x > 0)
            with open(sol_path, 'a') as f: f.write(enc.structure(m) + '\n')
            cnt += 1; sv.add_clause(enc.block_clause(m))
        if PROOF and cnt == 0:
            with open(os.path.join(PROOF, f'p{i}.drup'), 'w') as f: f.write('\n'.join(sv.get_proof()) + '\n')
        sv.delete()
    else:
        act = enc.pool.id(('piece', i))
        for cl in sym: s.add_clause(cl + [-act])
        asm = units + [act] + ([ACT[max(rg) + 1]] if BELOW and max(rg) + 1 >= 2 else [])
        while s.solve(assumptions=asm):
            m = set(x for x in s.get_model() if x > 0)
            with open(sol_path, 'a') as f: f.write(enc.structure(m) + '\n')
            cnt += 1; s.add_clause(enc.block_clause(m) + [-act])
        s.add_clause([-act])                                   # retire this piece's symmetry clauses
    total += cnt
    with open(done_path, 'a') as f:
        f.write(f"{i} {cnt} {time.time()-t0:.2f} {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} cpu={time.process_time()-c0:.2f}\n")
print(f"worker {RES}/{W_N} finished: {total} structures", flush=True)
