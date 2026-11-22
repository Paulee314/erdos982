#!/usr/bin/env python3
"""Cover audit for the certified small-n runs (n = 8, 10, 12), rebuilt from the run records.

Why a second audit: c_cover_check.py prints "duplicates 0, missing 0" from batches it generates itself, so that line is
true by construction and says nothing about the records. This script checks the records. For one cover (exact, below or
atmost) of one run directory it:
  1. regenerates, residue by residue and in the solver's order, every batch CNF exactly as cube982p.py and checkproofs.py
     built it (same setup(), same batch_cnf(), hence the same variable numbering);
  2. requires for every batch one solver record (w<r>.done) and one checker record (manifest_w<r>.txt) whose piece range,
     piece count, clause count and variable count all equal the regenerated values;
  3. counts a batch as certified only if, in addition, the checker said ACCEPT, the solver ended with final_unsat True,
     and the solver found 0 structures;
  4. for every other batch, requires each of its pieces to have an ACCEPT line in recert_<cover>/, regenerates that
     piece's CNF (fresh setup, batch_cnf([i]) plus its blocking-clause file if there is one, as recert.py did) and
     compares the clause count, the variable count and the SHA-256 of the CNF text with the recorded ones;
  5. where proof files are kept (n = 8 and 10), compares the SHA-256 of each unpacked proof with the manifest, checks that
     the checker log shows both drat-trim and cake_lpr verdicts, and with --recheck runs both checkers again (chk.sh) on
     the regenerated CNF and the kept proof;
  6. builds the set of covered pieces only from certified batches and certified pieces, and compares it with the kept
     pieces of the cover (each kept piece must be covered exactly once).
What it does not check: that setup()'s piece list and keep() are complete -- that is the mathematical argument in
theory/two_ring_and_local_symmetry.md and in e982lib.py. The audit shows that the records match what the published code
generates, batch for batch, and that every generated batch (or each of its pieces) has an accepted certificate.
Pieces whose CNF had structures (blocked by recorded blocking clauses) are listed; those structures go to the algebra step.
For such pieces the audit also reads the structure back from each blocking clause and compares it with the .sol file.
Note on cube982p.py's docstring: a batch with a satisfiable piece does end with final_unsat True (the structure is blocked
inside the batch), but its proof is not a valid DRUP proof, so the checker rejects it; that is why step 3 also requires
0 structures, and such batches go to step 4.

Usage: cover_audit2.py RUNDIR n K W exact|below|atmost [--bs 50] [--jobs J] [--recheck] [--res 0,3,5]
       (RUNDIR holds C_<cover>/ and, if needed, recert_<cover>/; W is the number of solver workers of that run)
Exit status 0 iff no problem was found (and, when all residues were audited, the cover is complete)."""
import sys, os, hashlib, gzip, subprocess, tempfile, argparse, time, re
from collections import Counter
from multiprocessing import Pool
CODE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, CODE)
from cube982p import setup, batch_cnf, write_cnf


def cnf_sha(F, nv):
    """SHA-256 of the text write_cnf() would write for (F, nv)"""
    h = hashlib.sha256()
    h.update(f'p cnf {nv} {len(F)}\n'.encode())
    h.update(('\n'.join(' '.join(map(str, cl)) + ' 0' for cl in F) + '\n').encode())
    return h.hexdigest()


def field(w, key, typ=str):
    return typ(w[w.index(key) + 1])


def parse_done(path):
    """batch -> list of solver records (a batch restarted after a failure has several lines; the last one counts)"""
    d = {}
    if not os.path.exists(path): return d
    for l in open(path):
        w = l.split()
        if not w or w[0] != 'batch': continue
        d.setdefault(int(w[1]), []).append(dict(rng=w[3], n=int(w[4].strip('()')), structures=field(w, 'structures', int),
                                               unsat=field(w, 'final_unsat') == 'True', clauses=field(w, 'clauses', int), vars=field(w, 'vars', int)))
    return d


def parse_manifest(path):
    """batch -> list of checker records"""
    d = {}
    if not os.path.exists(path): return d
    for l in open(path):
        w = l.split()
        if len(w) < 4 or not w[2].startswith('b'): continue
        d.setdefault(int(w[2][1:]), []).append(dict(cov=w[0], res=w[1], rng=field(w, 'pieces'), n=field(w, 'n_pieces', int), clauses=field(w, 'clauses', int),
                                                   vars=field(w, 'vars', int), sha=field(w, 'sha256'), unsat=field(w, 'final_unsat') == 'True', verdict=field(w, 'checker')))
    return d


def parse_recert(d):
    """piece -> ACCEPT record of recert.py; returns (records, problems)"""
    rec, probs = {}, []
    if not os.path.isdir(d): return rec, probs
    for f in sorted(os.listdir(d)):
        if not f.startswith('manifest_'): continue
        for l in open(os.path.join(d, f)):
            w = l.split()
            if len(w) < 3 or w[-1] != 'ACCEPT': continue
            r = dict(structures=field(w, 'structures', int), blocks=field(w, 'blocks', int), clauses=field(w, 'clauses', int), vars=field(w, 'vars', int),
                     cnf_sha=field(w, 'cnf_sha256'), proof_sha=field(w, 'proof_sha256'))
            i = int(w[1])
            if i in rec and rec[i]['cnf_sha'] != r['cnf_sha']: probs.append(f'recert piece {i}: two ACCEPT lines with different CNF hashes')
            rec[i] = r
    return rec, probs


def residue_task(a):
    rundir, n, K, W, cov, r, bs, recheck = a
    BELOW = cov == 'below'
    enc, cubes, keep = setup(n, K, BELOW, cov == 'atmost')          # one fresh encoding per worker, as in cube982p.py
    mine = [i for i in range(len(cubes)) if i % W == r and keep[i]]
    batches = [mine[b:b + bs] for b in range(0, len(mine), bs)]
    d = os.path.join(rundir, f'C_{cov}')
    done = parse_done(os.path.join(d, f'w{r}.done')); man = parse_manifest(os.path.join(d, f'manifest_w{r}.txt'))
    out = dict(r=r, nb=len(batches), cert=[], need=[], problems=[], hashed=0, logs=0, rechecked=0)
    P = out['problems'].append
    for bi in sorted(set(done) - set(range(len(batches)))): P(f'{cov} w{r} b{bi}: solver record for a batch the code does not generate')
    for bi in sorted(set(man) - set(range(len(batches)))): P(f'{cov} w{r} b{bi}: checker record for a batch the code does not generate')
    for bi, b in enumerate(batches):
        F, acts = batch_cnf(enc, cubes, b, BELOW); nv = enc.pool.top    # built for every batch, so the numbering matches
        name = f'{cov} w{r} b{bi}'; rng = f'{b[0]}..{b[-1]}'; ok = True
        dl = done[bi][-1] if bi in done else None; ml = man[bi][-1] if bi in man else None
        if dl is None: P(f'{name}: no solver record'); ok = False
        else:
            for k, v in (('rng', rng), ('n', len(b)), ('clauses', len(F)), ('vars', nv)):
                if dl[k] != v: P(f'{name}: solver record {k} {dl[k]} != regenerated {v}'); ok = False
        if ml is None: P(f'{name}: no checker record'); ok = False
        else:
            for k, v in (('cov', cov), ('res', f'w{r}'), ('rng', rng), ('n', len(b)), ('clauses', len(F)), ('vars', nv)):
                if ml[k] != v: P(f'{name}: checker record {k} {ml[k]} != regenerated {v}'); ok = False
        cert = ok and dl['unsat'] and dl['structures'] == 0 and ml['unsat'] and ml['verdict'] == 'ACCEPT'
        pz = os.path.join(d, f'{cov}_w{r}_b{bi}.drup.gz')
        if ml is not None and os.path.exists(pz):
            data = gzip.open(pz, 'rb').read()
            if hashlib.sha256(data).hexdigest() != ml['sha']: P(f'{name}: kept proof does not match the manifest hash'); cert = False
            else: out['hashed'] += 1
            lg = os.path.join(d, f'{cov}_w{r}_b{bi}.chk.log')
            txt = open(lg).read() if os.path.exists(lg) else ''
            if re.search(r'^s VERIFIED\s*$', txt, re.M) and 's VERIFIED UNSAT' in txt: out['logs'] += 1
            else: P(f'{name}: checker log missing or without both verdicts')
            if recheck:
                with tempfile.TemporaryDirectory() as td:
                    cf, pf = os.path.join(td, 'b.cnf'), os.path.join(td, 'b.drup')
                    write_cnf(cf, F, nv); open(pf, 'wb').write(data)
                    rr = subprocess.run([os.path.join(CODE, 'chk.sh'), cf, pf], capture_output=True, text=True)
                    if rr.returncode == 0 and 'ACCEPT' in rr.stdout: out['rechecked'] += 1
                    else: P(f'{name}: re-check REJECTED ({rr.stdout.strip()})'); cert = False
        if cert: out['cert'].append(b)
        else: out['need'].append((bi, b))
    return out


def piece_task(a):
    rundir, n, K, cov, i, rl = a
    enc, cubes, keep = setup(n, K, cov == 'below', cov == 'atmost')   # fresh encoding per piece, as in recert.py
    if not keep[i]: return i, [f'recert piece {i}: not a kept piece']
    F, acts = batch_cnf(enc, cubes, [i], cov == 'below'); nv = enc.pool.top
    bp = os.path.join(rundir, f'recert_{cov}', f'{cov}_p{i}.blocks')
    blocks = [list(map(int, l.split()[:-1])) for l in open(bp) if l.strip()] if os.path.exists(bp) else []
    G = F + blocks; pr = []
    if len(blocks) != rl['blocks'] or rl['blocks'] != rl['structures']: pr.append(f'recert piece {i}: blocks {len(blocks)} / recorded {rl["blocks"]} / structures {rl["structures"]}')
    if len(G) != rl['clauses']: pr.append(f'recert piece {i}: clauses {len(G)} != recorded {rl["clauses"]}')
    if nv != rl['vars']: pr.append(f'recert piece {i}: vars {nv} != recorded {rl["vars"]}')
    if not pr and cnf_sha(G, nv) != rl['cnf_sha']: pr.append(f'recert piece {i}: regenerated CNF hash differs from the recorded one')
    if blocks:     # each blocking clause must exclude exactly the recorded structure: read the structure back from the clause
        sp = os.path.join(rundir, f'recert_{cov}', f'{cov}_p{i}.sol')
        sols = [l.strip() for l in open(sp) if l.strip()] if os.path.exists(sp) else []
        back = [enc.structure({-x for x in b if x < 0}) for b in blocks]
        if back != sols: pr.append(f'recert piece {i}: blocking clauses do not match the recorded structures')
    return i, pr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rundir'); ap.add_argument('n', type=int); ap.add_argument('K', type=int); ap.add_argument('W', type=int)
    ap.add_argument('cover', choices=['exact', 'below', 'atmost']); ap.add_argument('--bs', type=int, default=50)
    ap.add_argument('--jobs', type=int, default=1); ap.add_argument('--recheck', action='store_true'); ap.add_argument('--res', default=None)
    A = ap.parse_args(); t0 = time.time()
    res = list(range(A.W)) if A.res is None else [int(x) for x in A.res.split(',')]
    enc, cubes, keep = setup(A.n, A.K, A.cover == 'below', A.cover == 'atmost')
    kept = {i for i in range(len(cubes)) if keep[i]}
    if A.res is not None: kept = {i for i in kept if i % A.W in res}
    print(f'n={A.n} K={A.K} cover {A.cover}: {len(cubes)} pieces generated, {len(kept)} kept (residues {res if A.res else "all"}); W={A.W} batch size {A.bs}', flush=True)
    problems = []; covered = Counter(); need = []; nb = hashed = logs = rechecked = 0
    with Pool(A.jobs) as pool:
        for out in pool.imap_unordered(residue_task, [(A.rundir, A.n, A.K, A.W, A.cover, r, A.bs, A.recheck) for r in res]):
            nb += out['nb']; hashed += out['hashed']; logs += out['logs']; rechecked += out['rechecked']; problems += out['problems']
            for b in out['cert']: covered.update(b)
            need += [(out['r'], bi, b) for bi, b in out['need']]
            print(f"  residue {out['r']}: {out['nb']} batches, {len(out['cert'])} certified as batches, {len(out['need'])} left to per-piece re-certification ({time.time()-t0:.0f}s)", flush=True)
        rec, pr = parse_recert(os.path.join(A.rundir, f'recert_{A.cover}')); problems += pr
        need_pieces = [i for _, _, b in need for i in b]
        absent = [i for i in need_pieces if i not in rec]
        if absent: problems.append(f'{len(absent)} pieces of uncertified batches have no ACCEPT re-certification, e.g. {absent[:10]}')
        todo = [(A.rundir, A.n, A.K, A.cover, i, rec[i]) for i in need_pieces if i in rec]
        good = 0
        for i, pr in pool.imap_unordered(piece_task, todo, chunksize=4):
            if pr: problems += pr
            else: covered[i] += 1; good += 1
    structs = sorted(i for i in need_pieces if i in rec and rec[i]['structures'] > 0)
    unused = len(set(rec) - set(need_pieces))
    dup = [i for i, c in covered.items() if c > 1]; missing = kept - set(covered); extra = set(covered) - kept
    print(f'{A.cover}: {nb} batches; {nb - len(need)} certified as whole batches (records match the regenerated CNF, checker ACCEPT, final UNSAT, 0 structures)')
    print(f'{A.cover}: {len(need)} batches re-certified per piece: {len(need_pieces)} pieces, {good} with matching regenerated CNF (count, variables, SHA-256) and ACCEPT')
    if structs: print(f'{A.cover}: pieces with structures, blocked and passed to the algebra step: ' + ', '.join(f'{i} ({rec[i]["structures"]})' for i in structs))
    if unused: print(f'{A.cover}: {unused} extra re-certified pieces not needed by the cover (harmless)')
    if hashed or logs or rechecked: print(f'{A.cover}: kept proofs matching the manifest hash: {hashed}; checker logs with both verdicts: {logs}; re-checked now with drat-trim + cake_lpr: {rechecked}')
    print(f'{A.cover}: covered pieces {len(covered)} of {len(kept)} kept; covered twice {len(dup)}, not covered {len(missing)}, outside the kept set {len(extra)}')
    for p in problems[:50]: print('PROBLEM', p)
    if len(problems) > 50: print(f'... and {len(problems) - 50} more problems')
    ok = not problems and not dup and not missing and not extra
    print(f'{A.cover}: AUDIT OK ({time.time()-t0:.0f}s)' if ok else f'{A.cover}: AUDIT FAILED ({len(problems)} problems)', flush=True)
    sys.exit(0 if ok else 1)


if __name__ == '__main__': main()
