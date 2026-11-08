#!/usr/bin/env python3
"""C4 driver for the fast pipeline (B+C).  Runs an EXPLICIT list of sub-cases (one 'c:a,c:b' cube per line), in order.
Per sub-case: c4_fastcube (single CaDiCaL LRAT solve + cake_lpr + exact certificates for referenced learned clauses).
  SAT        -> fallback: c4_cegar search (CEGAR/LP loop, learned clauses shared via files) then c4_certcube (two rounds).
  CERT_FAIL  -> fallback: c4_certcube (two rounds).
  anything else -> ALERT.
Concurrency: at most `slots` pipelines; a new sub-case starts only while (own active pipelines) + (CPU-heavy processes of
OTHER drivers: c4_cegar.py / cadical / cake_lpr / drat-trim whose command line contains `tag` but not DIR) < `maxheavy`
(so the old driver's in-flight jobs on the same machine are counted).
State: DIR/STATUS.json, DIR/ALERTS.txt, DIR/driver.log; resumable (VERIFIED sub-cases skipped).
Usage: c4_driver2.py n DIR fams=... list=FILE slots=K maxheavy=K tag=STR [share=f1,f2,...] [minfree_gb=40]"""
import sys, os, json, time, subprocess, threading, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
n = int(sys.argv[1]); D = os.path.abspath(sys.argv[2]); kw = dict(a.split('=', 1) for a in sys.argv[3:])
FAMS = kw['fams']; SLOTS = int(kw.get('slots', 6)); MAXH = int(kw.get('maxheavy', SLOTS)); TAG = kw['tag']; PY = sys.executable
MINFREE = float(kw.get('minfree_gb', 40)) * 1e9; MAXPROOF = float(kw.get('maxproof_gb', 100)) * 1e9
def proof_bytes():
    return sum(os.path.getsize(os.path.join(D, f)) for f in os.listdir(D) if f.endswith(('.lrat', '.drat')))
os.makedirs(D, exist_ok=True)
cubes = [l.strip() for l in open(kw['list']) if l.strip()]
own = {c: os.path.join(D, 'L_' + c.replace('0:', '').replace(',1:', '_') + '.jsonl') for c in cubes}
extra = [x for x in kw.get('share', '').split(',') if x]
SH = ','.join(list(own.values()) + extra)
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
HEAVY = ('c4_cegar.py', 'cadical', 'cake_lpr', 'drat-trim', 'c4_fastcube.py', 'c4_certcube.py')
def heavy():
    out = subprocess.run(['ps', '-Ao', 'args='], capture_output=True, text=True).stdout.splitlines()
    k = 0
    for a in out:
        if TAG not in a or D + '/' in a or 'c4_driver' in a: continue      # only OTHER drivers' jobs (own jobs: ACTIVE)
        exe = a.split()[0]; base = os.path.basename(exe)
        if base in ('cadical', 'cake_lpr', 'drat-trim') or ('c4_cegar.py' in a and 'python' in base):
            k += 1                                  # python wrappers of fastcube/certcube are idle while their solver runs
    return k
ACTIVE = [0]
queue = [c for c in cubes if status.get(c, {}).get('state') != 'VERIFIED']
def files_now():
    return [f for f in list(own.values()) + extra if os.path.exists(f)]
def run(args, logf):
    r = subprocess.run(args, capture_output=True, text=True)
    open(logf, 'w').write(r.stdout + r.stderr); return r
def pipeline(k, cube):
    pre = os.path.join(D, 'c_' + cube.replace('0:', '').replace(',1:', '_'))
    with lock: status[cube] = {'state': 'FAST', 'start': time.time()}; save()
    r = run([PY, os.path.join(HERE, 'c4_fastcube.py'), str(n), pre, f"fams={FAMS}", f"cube={cube}"] + files_now(), pre + '_fast.log')
    try: s1 = json.load(open(pre + '.json'))
    except Exception: s1 = {'status': 'NO_SUMMARY'}
    with lock: status[cube].update(fast=s1, state=s1.get('status')); save()
    log(f"slot {k}: {cube} fast -> {s1.get('status')} (solve {s1.get('solve')}s, check {s1.get('check')}s)")
    if s1.get('status') == 'VERIFIED': return
    if s1.get('status') == 'SAT':
        log(f"slot {k}: {cube} SAT at first solve -> CEGAR/LP fallback")
        r = run([PY, os.path.join(HERE, 'c4_cegar.py'), str(n), own[cube], f"fams={FAMS}", f"cube={cube}", f"share={SH}"], pre + '_search.log')
        res = [l for l in r.stdout.splitlines() if l.startswith('RESULT')]
        feas = os.path.exists(own[cube] + '.feasible')
        if not res or ': UNSAT' not in res[-1] or feas:
            alert(f"sub-case {cube}: fallback search {'LP-FEASIBLE MODEL' if feas else 'FAILED'}: {res[-1] if res else r.stderr[-300:]}")
            with lock: status[cube].update(state='SEARCH_PROBLEM'); save()
            return
    elif s1.get('status') != 'CERT_FAIL':
        alert(f"sub-case {cube}: fast pipeline {s1.get('status')}: {r.stdout[-300:]} {r.stderr[-300:]}")
        return
    while shutil.disk_usage(D).free < MINFREE: time.sleep(300)
    r = run([PY, os.path.join(HERE, 'c4_certcube.py'), str(n), pre + 'X', f"fams={FAMS}", f"cube={cube}"] + files_now(), pre + '_cert.log')
    try: s2 = json.load(open(pre + 'X.json'))
    except Exception: s2 = {'status': 'NO_SUMMARY'}
    with lock: status[cube].update(cert=s2, state=s2.get('status'), end=time.time()); save()
    if s2.get('status') != 'VERIFIED': alert(f"sub-case {cube}: two-round certification {s2.get('status')}")
    log(f"slot {k}: {cube} two-round -> {s2.get('status')}")
def worker(k):
    while True:
        with lock:
            if not queue: return
        while True:
            with lock:
                if not queue: return
                if ACTIVE[0] + heavy() < MAXH and shutil.disk_usage(D).free >= MINFREE and proof_bytes() < MAXPROOF:
                    cube = queue.pop(0); ACTIVE[0] += 1; break
            time.sleep(30)
        log(f"slot {k}: start {cube}")
        try: pipeline(k, cube)
        except Exception as e: alert(f"sub-case {cube}: driver exception {e!r}")
        with lock: ACTIVE[0] -= 1
log(f"start n={n} fams={FAMS} slots={SLOTS} maxheavy={MAXH} sub-cases={len(cubes)} pending={len(queue)}")
ths = []
for k in range(SLOTS):
    t = threading.Thread(target=worker, args=(k,)); t.start(); ths.append(t); time.sleep(5)   # stagger so heavy() sees starts
for t in ths: t.join()
ver = sum(1 for c in cubes if status.get(c, {}).get('state') == 'VERIFIED')
log(f"DONE: {ver}/{len(cubes)} sub-cases VERIFIED")
open(os.path.join(D, 'DONE'), 'w').write(f"{ver}/{len(cubes)} VERIFIED\n")
