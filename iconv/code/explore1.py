import math, itertools, sys
from geom import *
for n in range(5, 13):
    reg = Zof(regular(n))[0]
    agg = aggarwal_formula(n)
    fz = Zof(fan(n, 0.37))  # generic theta
    best_fan = None
    for k in range(1, n):
        th = math.pi / 3 / k
        if (n - 2) * th >= math.pi - 1e-9: continue
        P = fan(n, th)
        if not strictly_convex(P): continue
        z = Zof(P)[0]; e = equilaterals(P)
        if best_fan is None or z > best_fan[0]: best_fan = (z, k, z - 2 * e)
    # subsets of regular N-gon with centre: n-1 points in an arc of < N/2 positions
    bestc = None; bestnc = None
    for N in range(n, 40):
        # with centre
        m = n - 1
        maxpos = (N - 1) // 2 if N % 2 else N // 2 - 1   # positions 0..maxpos give span < pi
        if maxpos + 1 >= m:
            for rest in itertools.combinations(range(1, maxpos + 1), m - 1):
                S = (0,) + rest
                z, per, eq = subset_Z(N, S, True)
                if bestc is None or z > bestc[0]: bestc = (z, N, S, z - 2 * eq)
        # without centre (full search for small N)
        if math.comb(N - 1, n - 1) <= 200000:
            for rest in itertools.combinations(range(1, N), n - 1):
                S = (0,) + rest
                z, per, eq = subset_Z(N, S, False)
                if bestnc is None or z > bestnc[0]: bestnc = (z, N, S, z - 2 * eq)
    print(f'n={n} regular={reg} aggarwal={agg} fan_generic={fz[0]} best60fan={best_fan} 3n2/4={3*n*n/4:.1f}', flush=True)
    print(f'    regsub+centre={bestc}', flush=True)
    print(f'    regsub={bestnc}', flush=True)
