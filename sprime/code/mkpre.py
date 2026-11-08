import json, sys
n = int(sys.argv[1]); out = open(sys.argv[2], 'w'); k = 0; seen = set()
for fn in sys.argv[3:]:
    for l in open(fn):
        try: J = json.loads(l)
        except Exception: continue
        if 'core' in J and 'image_of' not in J:
            key = tuple(sorted(map(tuple, J['core'])))
            if key in seen: continue
            seen.add(key); out.write(json.dumps(J) + '\n'); k += 1
print(n, k)
