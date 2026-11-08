#!/bin/bash
cd /Users/paullee/AI-workspace/Claude-Projects/Erdos/agent_runs/theory2
PY=/Users/paullee/AI-workspace/Claude-Projects/Erdos/e982/venv/bin/python
export SINGULAR=/opt/homebrew/bin/Singular
$PY certify.py ap12_L7 5 0 1
$PY certify.py ap12_L7 6 0 1
/Users/paullee/AI-workspace/Claude-Projects/Erdos/agent_runs/tests_abc/venv/bin/python check_run_v7.py 12 ap12_L7_v2 7 --v1dir ap12_L7 --piecelist ap12_L7_v2/pieces_todo.txt > ap12_L7_v2/final_check2.log 2>&1
echo DONE > ap12_L7_v2/v1_algpass/run_cert.done
