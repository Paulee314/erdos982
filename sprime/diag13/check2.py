import json
V = [[-792, -1192, -2443, -2944], [-1872, -1977, -2443, -2944], [-2264, -2851, -30701, -30705, -30706, -30707],
     [-1872, -1977, -2060, -2944], [-1860, -1907, -2520, -2520, -6402, -7151]]
S = [frozenset(v) for v in V]
core = []
for line in open('../state/fc13_r1.core'):
    if line[0] in 'pc':
        continue
    c = [int(x) for x in line.split()[:-1]]
    if frozenset(c) in S:
        print('IN CORE:', c)
# how many times each violated clause appears in r1.cnf, and with what exact literal lists
cnt = {s: [] for s in S}
cur = []
for line in open('../state/fc13_r1.cnf'):
    if line[0] in 'pc':
        continue
    for t in line.split():
        v = int(t)
        if v == 0:
            f = frozenset(cur)
            if f in cnt:
                cnt[f].append(list(cur))
            cur = []
        else:
            cur.append(v)
for s, occ in cnt.items():
    print('r1 occurrences', sorted(s), len(occ), occ[:3])
# core clauses with duplicate literals, and core clauses not matched by sorted-tuple lookup into r1 clause set
dup = 0
for line in open('../state/fc13_r1.core'):
    if line[0] in 'pc':
        continue
    c = [int(x) for x in line.split()[:-1]]
    if len(set(c)) != len(c):
        dup += 1
print('core clauses with duplicate literals:', dup)
