# Check that a run's done files list every kept piece index exactly once (and nothing else).
# Usage: cover_check.py dir exact|below|atmost   (for cube982o.py done files: lines "<index> <count> ..." or "<index> mirror ...")
import sys, os, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cube982p import setup
d, cov = sys.argv[1], sys.argv[2]
enc, cubes, keep = setup(12, 5, cov == 'below', cov == 'atmost')
kept = {i for i in range(len(cubes)) if keep[i]}
seen = collections.Counter(); struct = 0; mirror = 0
for f in sorted(os.listdir(d)):
    if not f.endswith('.done'): continue
    for l in open(os.path.join(d, f)):
        w = l.split()
        if not w or not w[0].isdigit(): continue
        if w[1] == 'mirror': mirror += 1; continue
        seen[int(w[0])] += 1; struct += int(w[1])
dup = [i for i, c in seen.items() if c > 1]; missing = kept - set(seen); extra = set(seen) - kept
print(f"{d} [{cov}]: pieces total {len(cubes)}, kept {len(kept)}, solved {len(seen)}, mirror lines {mirror}, duplicates {len(dup)}, missing {len(missing)}, extra {len(extra)}, structures {struct}")
print('COVER OK' if not dup and not missing and not extra else 'COVER PROBLEM')
