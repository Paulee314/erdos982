#!/usr/bin/env python3
"""Combine the C4 n=11 STATUS files of all four drivers into one record.
Usage: c4_combine.py OUTDIR name1=STATUS1.json name2=STATUS2.json ...   (keys normalised to 'a,b')"""
import json, sys, os
out = sys.argv[1]; srcs = dict(a.split('=', 1) for a in sys.argv[2:])
def norm(k): return k.replace('0:', '').replace(',1:', ',') if k.startswith('0:') else k
rec = {f"{a},{b}": [] for a in range(1, 11) for b in range(1, 11)}
for name, f in srcs.items():
    for k, v in json.load(open(f)).items():
        kk = norm(k); s = v.get('fast') if v.get('fast', {}).get('status') == 'VERIFIED' else (v.get('cert') or v.get('fast') or {})
        rec[kk].append({'source': name, 'state': v.get('state'), 'pipeline': s.get('pipeline', 'two-round-drat'),
                        'search_s': v.get('search'), 'solve_s': s.get('solve') or (s.get('r1') or {}).get('solve'),
                        'check_s': s.get('check') or (s.get('r1') or {}).get('drat'),
                        'proof_bytes': s.get('proof_bytes') or (s.get('r1') or {}).get('proof_bytes'),
                        'proof_sha256': s.get('proof_sha256') or (s.get('r1') or {}).get('proof_sha256'),
                        'cnf_sha256': s.get('cnf_sha256') or (s.get('r1') or {}).get('cnf_sha256'),
                        'core_learned': s.get('core_learned'), 'fams': s.get('fams'), 'ver': s.get('ver'),
                        'checker': s.get('checker_out') or s.get('checker', 'drat-trim'), 'status': s.get('status')})
summary = {'verified': sorted(k for k, v in rec.items() if any(x['state'] == 'VERIFIED' for x in v)),
           'missing': sorted(k for k, v in rec.items() if not any(x['state'] == 'VERIFIED' for x in v))}
json.dump({'n': 11, 'bound': 54, 'subcases': rec, 'summary': summary}, open(os.path.join(out, 'COMBINED_n11.json'), 'w'), indent=1)
tot_lp = sum((x['core_learned'] or 0) for v in rec.values() for x in v if x['state'] == 'VERIFIED')
cnfmis = [k for k, v in rec.items() if len({x['cnf_sha256'] for x in v if x['state'] == 'VERIFIED' and x['cnf_sha256']}) > 1]
print(f"verified {len(summary['verified'])}/100; missing {summary['missing']}; LP clauses used in verified proofs: {tot_lp}; "
      f"sub-cases verified twice: {sum(1 for v in rec.values() if sum(x['state']=='VERIFIED' for x in v) > 1)}; cnf mismatches: {cnfmis}")
