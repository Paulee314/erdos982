#!/bin/bash
# DRUP check for one batch, two checkers in series (Paul approved installing them, 1 Nov 2026 22:22 CT):
#   1. drat-trim (Heule; commit 2e3b2dc) verifies the DRUP proof and writes an LRAT proof (every step with its hints);
#   2. cake_lpr (formally verified in HOL4/CakeML; commit a4323b2, release checksums OK) checks that LRAT proof.
# Prints ACCEPT and exits 0 only if both say VERIFIED. Usage: chk.sh batch.cnf batch.drup
T=${CHECKER_TOOLS:-/Users/paullee/AI-workspace/Claude-Projects/Erdos/tools}   # folder holding drat-trim/ and cake_lpr/
cnf=$1; proof=$2; lrat=${proof%.drup}.lrat; log=${proof%.drup}.chk.log
"$T/drat-trim/drat-trim" "$cnf" "$proof" -L "$lrat" -t 50000 2>&1 | tr '\r' '\n' | grep -v -e 'WARNING: backward mode ignores deletion' -e '^[[:space:]]*$' > "$log"
if ! grep -qE '^s VERIFIED[[:space:]]*$' "$log"; then rm -f "$lrat"; echo "REJECT drat-trim"; exit 1; fi
for h in 2000 12000; do
  out=$(CML_HEAP_SIZE=$h CML_STACK_SIZE=1000 "$T/cake_lpr/cake_lpr" "$cnf" "$lrat" 2>&1)
  echo "cake_lpr heap $h MB: $out" >> "$log"
  if echo "$out" | grep -qE '^s VERIFIED UNSAT[[:space:]]*$'; then rm -f "$lrat"; echo ACCEPT; exit 0; fi
  echo "$out" | grep -qi 'heap\|stack' || break
done
rm -f "$lrat"; echo "REJECT cake_lpr"; exit 1
