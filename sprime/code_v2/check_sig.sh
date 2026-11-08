#!/bin/bash
# Smoke test for code_v2 on the Mac: imports + re-verify the 152 cloud Sigma records with the checker.
R=$HOME/AI-workspace/Claude-Projects/Erdos/agent_runs; cd $R/sprime_cegar || exit 1
V=$R/tests_abc/venv/bin/python
(cd code_v2 && $V -c 'import cegar2, sigma, delta_rows, mpmath, scipy; print("imports ok", mpmath.__version__, scipy.__version__)') 2>&1 | tail -2
$V - <<'PY'
import json
o = open("state/sig152_check.jsonl", "w"); k = 0
for l in open("state/extra12_cloud.jsonl"):
    if json.loads(l).get("sigma"): o.write(l); k += 1
print("sigma records", k)
PY
$V code_v2/check_lambda_certs.py 12 state/sig152_check.jsonl 2>&1 | tail -2
