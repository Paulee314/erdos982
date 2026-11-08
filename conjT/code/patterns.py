#!/usr/bin/env python3
"""Pattern helpers (theory2).  A pattern is given as n restricted-growth strings, one per centre c, labelling the
other vertices in increasing order.  Functions: parse, global classes (union-find closure), symmetry group,
class table printing."""
import collections, itertools

A10 = '012313210 000123210 011023032 011110232 012332102 012333321 010213312 012103333 012021033 001232100'
B12 = ('01123432110 00123424321 01100234320 01221034043 01122110343 01234432102 01233443321 01021344312 '
       '01210334433 01202103443 00123210044 01234243210')
T12 = ('00123432100 00123141321 00001234321 01221031413 01222210343 01203302104 01234444321 01023044032 '
       '01210344443 01232102442 01234321000 01231413210')   # theory agent's first order-SAT model (F2-order only)


def parse(s):
    parts = s.split(); n = len(parts)
    lab = []
    for c in range(n):
        others = [v for v in range(n) if v != c]
        lab.append({v: int(ch, 36) for v, ch in zip(others, parts[c])})
    return n, lab


def pair(u, v): return (u, v) if u < v else (v, u)


class UF:
    def __init__(self, items): self.p = {x: x for x in items}
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b: self.p[a] = b


def global_classes(n, lab):
    pairs = [(a, b) for a in range(n) for b in range(a + 1, n)]
    uf = UF(pairs)
    for c in range(n):
        groups = collections.defaultdict(list)
        for v in range(n):
            if v != c: groups[lab[c][v]].append(v)
        for g in groups.values():
            for v in g[1:]: uf.union(pair(c, g[0]), pair(c, v))
    roots = {}; cls = {}
    for p in pairs:
        r = uf.find(p); cls[p] = roots.setdefault(r, len(roots))
    return cls


def classes_at(n, lab, c):
    groups = collections.defaultdict(list)
    for v in range(n):
        if v != c: groups[lab[c][v]].append(v)
    return [sorted(g) for g in groups.values()]


def equal(n, lab, c, u, v): return lab[c][u] == lab[c][v]


def apply_map(n, lab, g):
    """relabel pattern by vertex map g (a permutation of range(n)); returns new lab (classes at g(c) are images)"""
    new = [dict() for _ in range(n)]
    for c in range(n):
        gc = g[c]
        others = [v for v in range(n) if v != gc]
        # label others in increasing order by the class of their preimage at c
        inv = {g[v]: v for v in range(n)}
        m = {}
        for v in others:
            key = lab[c][inv[v]]
            new[gc][v] = m.setdefault(key, len(m))
    return new


def to_string(n, lab):
    return ' '.join(''.join(str(lab[c][v]) for v in range(n) if v != c) for c in range(n))


def symmetries(n, lab):
    s0 = to_string(n, lab)
    out = []
    for r in range(n):
        for refl in (1, -1):
            g = [(refl * v + r) % n for v in range(n)]
            if to_string(n, apply_map(n, lab, g)) == s0: out.append((r, refl))
    return out


def describe(s, name=''):
    n, lab = parse(s)
    cls = global_classes(n, lab)
    byc = collections.defaultdict(list)
    for p, k in cls.items(): byc[k].append(p)
    print(f'== {name} n={n}; {len(byc)} global classes; symmetries {symmetries(n, lab)}')
    for k in sorted(byc, key=lambda k: (-len(byc[k]), byc[k])):
        ps = sorted(byc[k], key=lambda p: (min((p[1]-p[0]) % n, (p[0]-p[1]) % n), p))
        gaps = collections.Counter(min((p[1]-p[0]) % n, (p[0]-p[1]) % n) for p in ps)
        print(f'  class {k} ({len(ps)} pairs; gaps {dict(gaps)}): {ps}')
    for c in range(n):
        print(f'  centre {c}: {classes_at(n, lab, c)}')


if __name__ == '__main__':
    describe(A10, 'A (n=10 survivor of F1+order)')
    describe(B12, 'B (n=12 survivor of full production clauses)')
    describe(T12, 'T (n=12 model of F2-order only)')
