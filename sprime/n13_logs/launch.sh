#!/bin/bash
# Restart-safe launcher for the S' CEGAR workers (3 per size). State = state/w<n>_<k>.jsonl (appended + flushed every
# iteration by cegar2.py). Relaunching preloads pre<n>, the seed file and every worker file, so nothing is lost.
# Usage (from anywhere): sprime_cegar/launch.sh <n>
R=$HOME/AI-workspace/Claude-Projects/Erdos/agent_runs; cd $R/sprime_cegar || exit 1
PY=$R/tests_abc/venv/bin/python; n=$1; CD=code; FX=""; [ "$n" = 12 ] && { CD=code_v2; FX="delta=1 sigma=1"; }; C=$R/sprime_cegar/$CD/cegar2.py
pre=state/pre$n.jsonl; [ -f state/m${n}_seed.jsonl ] && pre=$pre,state/m${n}_seed.jsonl
LIFTS="state/lift${n}*.jsonl"; [ "$NOLIFT" = 1 ] && LIFTS=""
for L in $LIFTS state/extra${n}*.jsonl; do [ -s "$L" ] && pre=$pre,$L; done
for k in A B C; do [ -s state/w${n}_$k.jsonl ] && pre=$pre,state/w${n}_$k.jsonl; done
for k in A B C; do
  case $k in A) X="maxcores=8 maxcores2=16";; B) X="shrink=1 maxcores=4 maxcores2=4";; C) X="maxcores=12 maxcores2=0";; esac
  sh=""; for j in A B C; do [ $j != $k ] && sh=$sh${sh:+,}state/w${n}_$j.jsonl; done
  cd $R && ./run.sh sprime_cegar w${n}_$k $PY $C $n state/w${n}_$k.jsonl preload=$pre share=$sh circ=1 bis=1 hinge=1 $FX timelimit=1000000 $X
done
