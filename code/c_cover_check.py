# Job C audit: every kept piece of the exactly-K and below-K covers is in exactly one batch with a done line, and every batch is
# either (both checkers ACCEPT and structures 0) or re-certified piece by piece in recert_<cover>/ (every piece ACCEPT).
import sys, os, re; R = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, R)
from cube982p import setup
W, BS = int(os.environ.get('W', 16)), 50; allok = True
for cov in (sys.argv[1:] or ['exact', 'below']):
    enc, cubes, keep = setup(int(os.environ.get('N', 12)), int(os.environ.get('K', 5)), cov == 'below', cov == 'atmost')
    kept = {i for i in range(len(cubes)) if keep[i]}; covered = {}; nb = okb = recb = 0; structs = 0
    rec = {}
    d = os.path.join(R, f'recert_{cov}')
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.startswith('manifest_'):
                for l in open(os.path.join(d, f)):
                    w = l.split()
                    if w[-1] == 'ACCEPT': rec[int(w[1])] = int(w[3])
    for r in range(W):
        mine = [i for i in range(len(cubes)) if i % W == r and keep[i]]
        batches = [mine[b:b + BS] for b in range(0, len(mine), BS)]
        acc = {}; st = {}; rng = {}
        for l in open(os.path.join(R, f'C_{cov}', f'manifest_w{r}.txt')):
            w = l.split(); acc[int(w[2][1:])] = w[w.index('checker') + 1]
        for l in open(os.path.join(R, f'C_{cov}', f'w{r}.done')):
            w = l.split()
            if w and w[0] == 'batch':
                bi = int(w[1]); st[bi] = int(w[w.index('structures') + 1]); rng[bi] = w[3]
        for bi, b in enumerate(batches):
            nb += 1
            if rng.get(bi) != f'{b[0]}..{b[-1]}': print(cov, r, bi, 'range mismatch', rng.get(bi)); allok = False
            if acc.get(bi) == 'ACCEPT' and st.get(bi) == 0: okb += 1
            elif all(i in rec for i in b): recb += 1; structs += sum(rec[i] for i in b)
            else: print(cov, r, bi, 'NOT CERTIFIED', acc.get(bi), st.get(bi)); allok = False
            for i in b: covered[i] = covered.get(i, 0) + 1
    dup = sum(1 for c in covered.values() if c > 1); missing = len(kept - set(covered)); extra = len(set(covered) - kept)
    print(f"{cov}: kept {len(kept)} pieces in {nb} batches; batch proofs accepted {okb}; re-certified per piece {recb}; structures (all in re-certified pieces) {structs}; duplicates {dup}, missing {missing}, extra {extra}")
    allok &= dup == 0 and missing == 0 and extra == 0
print('JOB C CERTIFIED COVER OK' if allok else 'JOB C PROBLEM')
