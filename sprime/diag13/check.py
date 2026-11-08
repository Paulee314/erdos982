import sys
# usage: diag13_check.py model_file r1.cnf final.cnf
mf, r1, fin = sys.argv[1:4]
asg = {}
status = None
for line in open(mf):
    if line.startswith('s '):
        status = line.strip()
    elif line.startswith('v '):
        for t in line.split()[1:]:
            v = int(t)
            if v: asg[abs(v)] = v > 0
print('model status:', status, 'assigned vars:', len(asg))

def clauses(path):
    cur = []
    for line in open(path):
        if line[0] in 'cp':
            continue
        for t in line.split():
            v = int(t)
            if v == 0:
                yield tuple(cur); cur = []
            else:
                cur.append(v)

def sat(c):
    return any(asg.get(abs(l), False) == (l > 0) for l in c)

fset = set(tuple(sorted(c)) for c in clauses(fin))
print('final clauses (distinct):', len(fset))
viol = []
n1 = 0
in_final = 0
for c in clauses(r1):
    n1 += 1
    if tuple(sorted(c)) in fset:
        in_final += 1
    if not sat(c):
        viol.append(c)
print('r1 clauses:', n1, 'of which also in final:', in_final)
print('r1 clauses violated by final model:', len(viol))
from collections import Counter
print('violated clause length histogram:', sorted(Counter(len(c) for c in viol).items())[:20])
for c in viol[:15]:
    print('VIOL', ' '.join(map(str, c)))
mx = max((abs(l) for c in viol for l in c), default=0)
print('max var in violated:', mx)
