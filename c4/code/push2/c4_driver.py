#!/usr/bin/env python3
"""C4 production driver: sub-cases t(0)=a, t(1)=b (a, b = 1..n-1; together they cover every case of the t(0) split),
SLOTS parallel pipelines; each sub-case = c4_cegar search (learned clauses shared through files) then c4_certcube
certification.  State: DIR/STATUS.json (per sub-case), DIR/ALERTS.txt (any failure or LP-feasible model), DIR/driver.log.
Resumable: sub-cases already VERIFIED in STATUS.json are skipped.
Usage: c4_driver.py n DIR fams=... [slots=6]"""
import sys, os, json, time, subprocess, threading, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
n = int(sys.argv[1]); D = sys.argv[2]; kw = dict(a.split('=', 1) for a in sys.argv[3:])
FAMS = kw.get('fams', 'FGXO'); SLOTS = int(kw.get('slots', 6)); PY = sys.executable
MINFREE = float(kw.get('minfree_gb', 40)) * 1e9
os.makedirs(D, exist_ok=True)
cubes = sorted(((a, b) for a in range(1, n) for b in range(1, n)), key=lambda c: (abs(c[0] - (n - 1) / 2) + abs(c[1] - (n - 1) / 2), c))
files = [os.path.join(D, f"L_{a}_{b}.jsonl") for a, b in cubes]
SH = ','.join(files)
lock = threading.Lock(); SF = os.path.join(D, 'STATUS.json')
status = json.load(open(SF)) if os.path.exists(SF) else {}
def save():
    with open(SF + '.tmp', 'w') as f: json.dump(status, f, indent=0)
    os.replace(SF + '.tmp', SF)
def alert(msg):
    with lock:
        with open(os.path.join(D, 'ALERTS.txt'), 'a') as f: f.write(time.strftime('%H:%M:%S ') + msg + '\n')
def log(msg):
    with lock:
        with open(os.path.join(D, 'driver.log'), 'a') as f: f.write(time.strftime('%H:%M:%S ') + msg + '\n')
queue = [c for c in cubes if status.get(f"{c[0]},{c[1]}", {}).get('state') != 'VERIFIED']
def worker(k):
    while True:
        with lock:
            if not queue: return
            a, b = queue.pop(0)
        key = f"{a},{b}"; cube = f"0:{a},1:{b}"; pre = os.path.join(D, f"c_{a}_{b}")
        with lock: status[key] = {'state': 'SEARCH', 'start': time.time()}; save()
        log(f"slot {k}: search {key}")
        ts = time.time()
        r = subprocess.run([PY, os.path.join(HERE, 'c4_cegar.py'), str(n), files[cubes.index((a, b))], f"fams={FAMS}", f"cube={cube}",
                            f"share={SH}", 'maxcores=8'], capture_output=True, text=True)
        open(pre + '_search.log', 'w').write(r.stdout + r.stderr)
        res = [l for l in r.stdout.splitlines() if l.startswith('RESULT')]
        feas = os.path.exists(files[cubes.index((a, b))] + '.feasible')
        tsearch = time.time() - ts
        if not res or ': UNSAT' not in res[-1] or feas:
            alert(f"sub-case {key}: search {'LP-FEASIBLE MODEL' if feas else 'FAILED'}: {res[-1] if res else r.stderr[-300:]}")
            with lock: status[key].update(state='SEARCH_PROBLEM', search=tsearch); save()
            continue
        with lock: status[key].update(state='CERT', search=round(tsearch, 1), result=res[-1]); save()
        log(f"slot {k}: {key} search UNSAT in {tsearch:.0f}s; certifying")
        import shutil
        while shutil.disk_usage(D).free < MINFREE:           # disk guard: never let raw proofs fill the disk
            log(f"slot {k}: waiting for disk space ({shutil.disk_usage(D).free/1e9:.0f} GB free)"); time.sleep(300)
        r = subprocess.run([PY, os.path.join(HERE, 'c4_certcube.py'), str(n), pre, f"fams={FAMS}", f"cube={cube}"] + files,
                           capture_output=True, text=True)
        open(pre + '_cert.log', 'w').write(r.stdout + r.stderr)
        try: summ = json.load(open(pre + '.json'))
        except Exception: summ = {'status': 'NO_SUMMARY'}
        with lock: status[key].update(state=summ.get('status'), cert=summ, end=time.time()); save()
        if summ.get('status') != 'VERIFIED': alert(f"sub-case {key}: certification {summ.get('status')}: {r.stdout[-400:]} {r.stderr[-400:]}")
        log(f"slot {k}: {key} -> {summ.get('status')}")
ths = [threading.Thread(target=worker, args=(k,)) for k in range(SLOTS)]
log(f"start n={n} fams={FAMS} slots={SLOTS} sub-cases={len(cubes)} pending={len(queue)}")
for t in ths: t.start()
for t in ths: t.join()
ver = sum(1 for c in cubes if status.get(f"{c[0]},{c[1]}", {}).get('state') == 'VERIFIED')
log(f"DONE: {ver}/{len(cubes)} sub-cases VERIFIED")
open(os.path.join(D, 'DONE'), 'w').write(f"{ver}/{len(cubes)} VERIFIED\n")
