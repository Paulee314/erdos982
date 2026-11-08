#!/usr/bin/env python3
"""summary of C4 n=11 STATUS files given on the command line"""
import json, sys, collections
for f in sys.argv[1:]:
    try: s = json.load(open(f))
    except Exception as e: print(f, 'unreadable', e); continue
    c = collections.Counter(v.get('state') for v in s.values())
    run = [k for k, v in s.items() if v.get('state') not in ('VERIFIED',)]
    print(f.split('/')[-2], dict(c), 'not-verified:', ' '.join(sorted(run)))
