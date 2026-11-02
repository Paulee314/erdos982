#!/bin/bash
# Memory guard for the n12 run: every 5 s sums RSS of processes whose command line contains e982/n12_run.
# Over 80 GB, or memory compressor over 20 GB: stop the newest such process (the runs are restart-safe). Log: guard.log
R=/Users/paullee/AI-workspace/Claude-Projects/Erdos/e982/n12_run; L=$R/guard.log; echo $$ > $R/guard.pid
echo "$(date -u +%FT%TZ) guard start (cap 80 GB RSS, compressor 20 GB)" >> $L
while true; do
  rss=$(ps -Ao rss=,args= | grep "e982/n12_run" | grep -v -E 'grep|guard.sh' | awk '{s+=$1} END {printf "%d", s/1048576}')
  comp=$(vm_stat | awk '/occupied by compressor/ {gsub(/\./,"",$5); printf "%d", $5*16384/1e9}')
  echo "$(date -u +%FT%TZ) rss ${rss} GB comp ${comp} GB" > $R/guard.last
  if [ "$rss" -gt 80 ] || [ "$comp" -gt 20 ]; then
    p=$(ps -Ao pid=,lstart=,args= | grep "e982/n12_run" | grep -v -E 'grep|guard.sh|worker.sh' | tail -1 | awk '{print $1}')
    [ -n "$p" ] && kill $p && echo "$(date -u +%FT%TZ) STOPPED pid $p: RSS ${rss} GB, compressor ${comp} GB" >> $L
  fi
  sleep 5
done
