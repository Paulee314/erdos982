# Cover audit output (21 Nov 2026)

Output of `code/cover_audit2.py`, which checks the run records of the certified searches against CNFs regenerated
from the published code (see the "Cover audit" section of the main README for what it checks and what it does not).
Run on the Mac Studio with Python 3.9 and python-sat 1.9.dev17, the same environment as the original runs.

| File | Command (from the repository root) |
|---|---|
| `n8.txt` | `code/cover_audit2.py n8 8 3 2 exact --recheck` and the same with `below` |
| `n10.txt` | `code/cover_audit2.py n10 10 4 6 exact --recheck --jobs 3` and the same with `below` |
| `n12_exact.txt` | `code/cover_audit2.py n12 12 5 16 exact --jobs 4` |
| `n12_below.txt` | `code/cover_audit2.py n12 12 5 16 below --jobs 4` |
| `n12_atmost.txt` | `code/cover_audit2.py n12 12 5 16 atmost --jobs 4` |

`--recheck` re-runs drat-trim and cake_lpr (through `code/chk.sh`, with `CHECKER_TOOLS` set) on every kept proof. The
n = 12 proofs are on Zenodo, not in the repository, so for n = 12 the audit checks the records and the regenerated CNFs
but does not re-run the checkers. Each run ends with `AUDIT OK` or `AUDIT FAILED` and exits with status 0 or 1.
