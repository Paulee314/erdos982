#!/usr/bin/env python3
"""Erdős #982 search encoding, factored out of cube982d.py for experiments (n = 12 feasibility study).
The base clauses (transitivity, exactly K classes per centre, F1, F2) are built exactly as in cube982d.py / sat982.py,
in the same order, with the same variable numbering.  On top of that, optional ingredients:

  sym='list'    : cube982d.py's symmetry clauses (one clause per earlier cube and frame)      -- unchanged
  sym='compact' : the same constraint "partition at every vertex in every frame >= pi (lex)" encoded directly,
                  O(n^2) clauses per frame instead of O(#earlier cubes)                        -- new, equivalent
  sym='full'    : compact + full lex-leader on the whole structure (ties on the vertex-0 partition broken by the
                  partitions at the following vertices, in the frame's order)                  -- new, stronger
  order=True    : add a strict total preorder on all pair distances (LT variables) and the pure-order consequences of
                  convexity: F2-order (both diagonals' sum exceeds both pairs of opposite sides, so e.g. ac <= ab and
                  bd <= cd cannot both hold), chord monotonicity on a circle (three points at the same distance from a
                  centre, in cyclic order: the outer chord is the longest), and the four-in-a-class short chord.
  atmost=True   : at most K classes per centre instead of exactly K (for the below-K part)
"""
import itertools, os
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool


def partitions(m, k, exact=True):
    """restricted-growth strings of length m with exactly (or at most) k blocks, lex order"""
    a = [0] * m
    def rec(i, mx):
        if i == m:
            if (mx + 1 == k) if exact else (mx + 1 <= k): yield tuple(a)
            return
        if exact and (mx + 1) + (m - i) < k: return
        for x in range(min(mx + 2, k)):
            a[i] = x; yield from rec(i + 1, max(mx, x))
    yield from rec(1, 0)


def canon(lab):
    m = {}; return tuple(m.setdefault(x, len(m)) for x in lab)


class Enc:
    def __init__(self, n, K, order=False, atmost=False, order_extras=True):
        self.n, self.K = n, K
        V = range(n); self.V = V
        pairs = [(a, b) for a in V for b in V if a < b]; self.pairs = pairs
        P = {p: i for i, p in enumerate(pairs)}; self.P = P
        pool = IDPool(); self.pool = pool
        self.NP = len(pairs)
        self.clauses = clauses = []
        E, e, pr = self.E, self.e, self.pr
        # transitivity of E (verbatim order)
        for p, q, r in itertools.combinations(range(self.NP), 3):
            a, b, d = E(p, q), E(q, r), E(p, r)
            clauses += [[-a, -b, d], [-a, -d, b], [-b, -d, a]]
        # exactly (or at most) K classes at each centre
        self.REPS = {}
        for c in V:
            others = [v for v in V if v != c]
            reps = []
            for i, v in enumerate(others):
                rv = pool.id(('r', c, v)); reps.append(rv)
                prev = [e(c, u, v) for u in others[:i]]
                for x in prev: clauses.append([-rv, -x])
                clauses.append([rv] + prev)
            self.REPS[c] = reps
            if atmost:
                clauses += CardEnc.atmost(lits=reps, bound=K, vpool=pool, encoding=EncType.seqcounter).clauses
            else:
                clauses += CardEnc.equals(lits=reps, bound=K, vpool=pool, encoding=EncType.seqcounter).clauses
        # F1
        def between(x, lo, hi): return lo < x < hi if lo < hi else (x > lo or x < hi)
        def separates(c1, c2, a, b): return between(a, c1, c2) != between(b, c1, c2)
        for u, v in pairs:
            cs = [c for c in V if c not in (u, v)]
            for c1, c2 in itertools.combinations(cs, 2):
                if not separates(c1, c2, u, v): clauses.append([-e(c1, u, v), -e(c2, u, v)])
            for c1, c2, c3 in itertools.combinations(cs, 3):
                clauses.append([-e(c1, u, v), -e(c2, u, v), -e(c3, u, v)])
        # F2
        for a, b, c, d in itertools.combinations(V, 4):
            ac, bd, ab, cd, ad, bc = pr(a, c), pr(b, d), pr(a, b), pr(c, d), pr(a, d), pr(b, c)
            clauses += [[-E(ac, ab), -E(bd, cd)], [-E(ac, cd), -E(bd, ab)], [-E(ac, ad), -E(bd, bc)], [-E(ac, bc), -E(bd, ad)]]
        self.n_base = len(clauses); self.top_base = pool.top
        self.local = [(c, u, v) for c in V for u in V for v in V if c != u and c != v and u < v]
        self.lits = [e(c, u, v) for (c, u, v) in self.local]
        self.others0 = [v for v in V if v != 0]
        if order: self.add_order(order_extras)
        self.n_total = len(clauses)
        # frames for symmetry breaking (as in cube982d: vertices 1..n-1, both directions)
        self.FR = {(v, o): self.frame_lits(v, o) for v in range(1, n) for o in (1, -1)}

    # --- variables
    def E(self, p, q):
        if p > q: p, q = q, p
        return self.pool.id(('E', p, q))
    def pr(self, a, b): return self.P[(a, b) if a < b else (b, a)]
    def e(self, c, u, v): return self.E(self.pr(c, u), self.pr(c, v))
    def LT(self, p, q): return self.pool.id(('LT', p, q))      # distance of pair p < distance of pair q

    # --- order extension
    def add_order(self, extras=True):
        n, V, pr, E, LT, cl = self.n, self.V, self.pr, self.E, self.LT, self.clauses
        NP = self.NP
        n0 = len(cl)
        for p, q in itertools.combinations(range(NP), 2):
            a, b, c = E(p, q), LT(p, q), LT(q, p)
            cl += [[a, b, c], [-a, -b], [-a, -c], [-b, -c]]                 # exactly one of =, <, >
        for p, q, r in itertools.permutations(range(NP), 3):
            cl.append([-LT(p, q), -LT(q, r), LT(p, r)])                    # transitivity of <
        for p, q in itertools.combinations(range(NP), 2):
            for r in range(NP):
                if r in (p, q): continue
                cl += [[-E(p, q), -LT(p, r), LT(q, r)], [-E(p, q), -LT(q, r), LT(p, r)],
                       [-E(p, q), -LT(r, p), LT(r, q)], [-E(p, q), -LT(r, q), LT(r, p)]]   # = is a congruence for <
        self.n_order_axioms = len(cl) - n0; self.n_order_geom = 0
        if not extras: return
        if extras is True: extras = {'f2', 'chord', 'gap'}
        # F2-order: for a<b<c<d (convex quadrilateral), ac+bd > ab+cd and ac+bd > ad+bc, so
        #   not(ac <= ab and bd <= cd), not(ac <= cd and bd <= ab), not(ac <= ad and bd <= bc), not(ac <= bc and bd <= ad)
        #   where x <= y is not LT(y, x).
        for a, b, c, d in (itertools.combinations(V, 4) if 'f2' in extras else []):
            ac, bd, ab, cd, ad, bc = pr(a, c), pr(b, d), pr(a, b), pr(c, d), pr(a, d), pr(b, c)
            cl += [[LT(ab, ac), LT(cd, bd)], [LT(cd, ac), LT(ab, bd)], [LT(ad, ac), LT(bc, bd)], [LT(bc, ac), LT(ad, bd)]]
        # chord monotonicity: p_i, p_j, p_k at the same distance r from c, in cyclic order starting after c (= angular order
        # from c, all within the half-plane at c): |p_i p_k| > |p_i p_j| and |p_i p_k| > |p_j p_k|
        for c in V:
            others = [(c + t) % n for t in range(1, n)]
            for i, j, k in (itertools.combinations(range(n - 1), 3) if 'chord' in extras else []):
                pi, pj, pk = others[i], others[j], others[k]
                cl += [[-self.e(c, pi, pj), -self.e(c, pj, pk), LT(pr(pi, pj), pr(pi, pk))],
                       [-self.e(c, pi, pj), -self.e(c, pj, pk), LT(pr(pj, pk), pr(pi, pk))]]
            # four points of one class at c: the three angular gaps sum to < 180 deg, so one gap is < 60 deg and that
            # chord is shorter than the radius
            for i, j, k, l in (itertools.combinations(range(n - 1), 4) if 'gap' in extras else []):
                ps = [others[i], others[j], others[k], others[l]]
                base = [-self.e(c, ps[0], ps[1]), -self.e(c, ps[1], ps[2]), -self.e(c, ps[2], ps[3])]
                cl.append(base + [LT(pr(ps[t], ps[t + 1]), pr(c, ps[0])) for t in range(3)])
        self.n_order_geom = len(cl) - n0 - self.n_order_axioms

    # --- pieces
    def cubes(self, exact=True):
        return list(partitions(self.n - 1, self.K if exact else self.K - 1, exact))
    def mirror(self, rg):
        n = self.n
        return canon(tuple(rg[(n - (x + 1)) - 1] for x in range(n - 1)))
    def keep(self, cubes):
        return [self.mirror(rg) >= rg for rg in cubes]
    def unit_clauses(self, rg):
        out = []; o0 = self.others0
        for x in range(len(o0)):
            for y in range(x + 1, len(o0)):
                lit = self.e(0, o0[x], o0[y]); out.append([lit if rg[x] == rg[y] else -lit])
        return out

    # --- symmetry breaking
    def frame_lits(self, v, o):
        n = self.n
        w = [(v + o * (k + 1)) % n for k in range(n - 1)]
        return [[self.e(v, w[k1], w[k2]) for k2 in range(n - 1)] for k1 in range(n - 1)]
    def sym_list(self, cubes, idx):
        """cube982d.py's clauses: for every earlier cube sigma and every frame, 'partition at v in frame != sigma'"""
        n = self.n; out = []
        for sig in cubes[:idx]:
            for (v, o), L in self.FR.items():
                out.append([(-L[k1][k2] if sig[k1] == sig[k2] else L[k1][k2]) for k1 in range(n - 1) for k2 in range(k1 + 1, n - 1)])
        return out
    def sym_compact(self, pi, frames=None):
        """'partition at v read in frame (v,o), as a restricted-growth string, is lexicographically >= pi', directly:
        sigma < pi iff for some position k the prefixes agree and sigma[k] < pi[k]; given the prefix agrees (as a partition
        of positions < k), sigma[k] = pi[j] for any earlier j in the same class as k (transitivity), so sigma[k] < pi[k]
        iff some j < k with pi[j] < pi[k] is in k's class.  Forbid each such (k, j): clause = (prefix differs) or not L[j][k]."""
        n = self.n; out = []
        for (v, o), L in (self.FR.items() if frames is None else frames):
            for k in range(1, n - 1):
                prefix_differs = [(L[j1][j2] if pi[j1] != pi[j2] else -L[j1][j2]) for j1 in range(k) for j2 in range(j1 + 1, k)]
                for j in range(k):
                    if pi[j] < pi[k]:
                        out.append(prefix_differs + [-L[j][k]])
        return out
    def sym_full(self, pi):
        """compact lex-leader on the whole structure: rows = partitions at vertices 0,1,...,n-1 read in frame (0,+1), compared
        with rows at v, v+o, v+2o, ... read in frame (v,o).  Row 0 vs pi is the compact constraint; on a tie (row equal to pi)
        the next rows are compared via the global literals: row t of frame (0,+1) is the vector of e(t, t+a, t+b) (a<b),
        row t of frame (v,o) is e(v+ot, v+o(t+a), v+o(t+b)); lex-leader: frame (0,+1) <= frame (v,o) with aux equality vars."""
        n = self.n; pool = self.pool; out = []
        def row(v, o, t):
            c = (v + o * t) % n
            return [self.e(c, (c + o * a) % n, (c + o * b) % n) for a in range(1, n) for b in range(a + 1, n)]
        base = [row(0, 1, t) for t in range(n)]
        for (v, o) in self.FR:
            other = [row(v, o, t) for t in range(n)]
            # X = concat(base rows), Y = concat(other rows); require X <= Y lexicographically with 1 > 0 ... we want the
            # vertex-0-partition order to be the RG lex order used for pieces, so row 0 is handled by sym_compact (pi fixed);
            # here rows 1.. are compared only when row 0 of Y equals pi (as a partition), using plain literal-vector lex order
            # (any fixed total order on structures is fine for lex-leader as long as it is the same for all group elements:
            # we use (RG order of the vertex-0 partition, then literal vectors of rows 1..n-1)).
            X = [l for t in range(1, n) for l in base[t]]; Y = [l for t in range(1, n) for l in other[t]]
            # eq0: row 0 of Y equals pi as a partition (a conjunction of fixed-sign literals of other[0])
            L = self.FR[(v, o)]
            eq0_lits = [(L[j1][j2] if pi[j1] == pi[j2] else -L[j1][j2]) for j1 in range(n - 1) for j2 in range(j1 + 1, n - 1)]
            a0 = pool.id(('eq0', v, o, tuple(pi)))
            # a0 <-> and(eq0_lits)
            for l in eq0_lits: out.append([-a0, l])
            out.append([a0] + [-l for l in eq0_lits])
            # lex: X <= Y given a0.  aux eq_i: X[:i] == Y[:i].  Standard: eq_0 = a0; eq_{i+1} <-> eq_i and (X[i] == Y[i]);
            # constraint: eq_i -> (X[i] <= Y[i]) i.e. eq_i and X[i] -> Y[i]   (0 < 1)
            prev = a0
            m = len(X)
            for i in range(m):
                out.append([-prev, -X[i], Y[i]])
                if i == m - 1: break
                nxt = pool.id(('eqf', v, o, tuple(pi), i))
                # nxt <-> prev and (X[i] <-> Y[i])
                out += [[-nxt, prev], [-nxt, -X[i], Y[i]], [-nxt, X[i], -Y[i]],
                        [nxt, -prev, X[i], Y[i]], [nxt, -prev, -X[i], -Y[i]]]
                prev = nxt
        return out

    # --- output
    def structure(self, m):
        n = self.n; line = []
        for c in self.V:
            others = [v for v in self.V if v != c]; lab = {}; st = ''
            for v in others:
                for u in others:
                    if u == v: lab[v] = len(set(lab.values())); break
                    if self.e(c, u, v) in m: lab[v] = lab[u]; break
                st += str(lab[v])
            line.append(st)
        return ' '.join(line)
    def block_clause(self, m, mode='full'):
        if mode == 'full':
            return [-x if x in m else x for x in self.lits]
        if mode == 'pos':          # block all structures containing these equalities (sound: more equations, fewer solutions)
            return [-x for x in self.lits if x in m]
        raise ValueError(mode)
