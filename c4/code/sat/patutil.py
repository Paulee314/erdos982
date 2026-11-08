"""Pattern utilities for TEST A: a pattern line is n restricted-growth strings, one per centre c, giving the class label of
each other vertex (in increasing vertex order, skipping c).  Equalities = pairs (c,u,v) with the same label at c."""
import itertools

def eqset(line, n):
    parts = line.split('|')[0].split(); assert len(parts) == n, line
    S = set()
    for c in range(n):
        others = [v for v in range(n) if v != c]
        for (u, a), (v, b) in itertools.combinations(zip(others, parts[c]), 2):
            if a == b: S.add((c, min(u, v), max(u, v)))
    return frozenset(S)

def classes(line, n):
    parts = line.split('|')[0].split(); out = {}
    for c in range(n):
        others = [v for v in range(n) if v != c]; g = {}
        for v, a in zip(others, parts[c]): g.setdefault(a, []).append(v)
        out[c] = list(g.values())
    return out

def images(S, n):
    for v in range(n):
        for o in (1, -1):
            f = lambda x: (v + o * x) % n
            yield frozenset((f(c), min(f(u), f(w)), max(f(u), f(w))) for c, u, w in S)

def canon(S, n):
    return min(tuple(sorted(T)) for T in images(S, n))

def reduce_family(sets, n):
    """drop every set that contains a dihedral image of another (kept) set; returns indices kept.  Sound for the question
    'is some polygon realizing a superset of the equalities': if P contains g(Q), any realization of P is g of one of Q."""
    order = sorted(range(len(sets)), key=lambda i: len(sets[i]))
    kept = []; keptimgs = []
    for i in order:
        S = sets[i]
        if any(T <= S for T in keptimgs): continue
        kept.append(i); keptimgs.extend(set(images(sets[i], n)))
    return sorted(kept)
