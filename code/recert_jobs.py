# list the pieces of every job-C batch that is not (ACCEPT and structures 0) -> recert_<cover>_jobs.txt
import sys, os; R = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, R)
from cube982p import setup
W, BS = int(os.environ.get('W', 16)), 50
for cov in (sys.argv[1:] or ['exact', 'below']):
    enc, cubes, keep = setup(int(os.environ.get('N', 12)), int(os.environ.get('K', 5)), cov == 'below', cov == 'atmost')
    bad = []
    for r in range(W):
        mine = [i for i in range(len(cubes)) if i % W == r and keep[i]]
        batches = [mine[b:b + BS] for b in range(0, len(mine), BS)]
        acc = {}; st = {}
        for l in open(os.path.join(R, f'C_{cov}', f'manifest_w{r}.txt')):
            w = l.split(); acc[int(w[2][1:])] = w[w.index('checker') + 1]
        for l in open(os.path.join(R, f'C_{cov}', f'w{r}.done')):
            w = l.split()
            if w and w[0] == 'batch': st[int(w[1])] = int(w[w.index('structures') + 1])
        for bi, b in enumerate(batches):
            if acc.get(bi) != 'ACCEPT' or st.get(bi) != 0: bad.append((r, bi, b))
    with open(os.path.join(R, f'recert_{cov}_jobs.txt'), 'w') as f:
        for r, bi, b in bad: f.write('\n'.join(map(str, b)) + '\n')
    print(cov, 'batches to recertify:', [(r, bi) for r, bi, b in bad], 'pieces:', sum(len(b) for _, _, b in bad))
