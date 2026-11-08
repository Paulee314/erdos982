import realise, sys
def eqs_of(line, n):
    parts=line.split(); eqs=[]
    for c in range(n):
        others=[v for v in range(n) if v!=c]; lab=dict(zip(others,parts[c])); g={}
        for v in others: g.setdefault(lab[v],[]).append(v)
        for gg in g.values():
            for v in gg[1:]: eqs.append((c,gg[0],v))
    return eqs
for line in ['0000 0120 0121 0122 0012','0000 0120 0121 0123 0012','0000 0120 0123 0121 0012']:
    r = realise.realise(5, eqs_of(line,5), tries=200, verbose=True)
    print(line, None if r is None else r[1:])
