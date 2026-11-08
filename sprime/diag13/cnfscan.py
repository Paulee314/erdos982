import sys
taut = dup = n = 0
first = []
for line in open(sys.argv[1]):
    if line[0] in 'pc':
        continue
    lits = [int(x) for x in line.split()[:-1]]
    n += 1
    s = set(lits)
    if any(-l in s for l in s):
        taut += 1
        if len(first) < 5:
            first.append((n, 'taut', lits))
    elif len(s) != len(lits):
        dup += 1
        if len(first) < 5:
            first.append((n, 'dup', lits))
print('clauses', n, 'tautologies', taut, 'dup-literal clauses', dup)
for f in first:
    print(f)
