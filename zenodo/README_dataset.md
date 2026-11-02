# Erdős Problem #982, n = 12: DRUP proofs

Companion data to https://github.com/Paulee314/erdos982 (code, manifests, algebraic certificate, write-up).

Each `n12_proofs_<dir>.tar.part*` set is one tar archive split into 4 GB parts. Reassemble with:

    cat n12_proofs_C_exact.tar.part* | tar xf -

| Archive | Contents |
|---|---|
| `C_exact`, `C_below` | exactly-5 and below-5 covers (run C); one gzipped DRUP proof per 50-piece batch |
| `C_atmost` | unified at-most-5 cover (run D) |
| `recert_*` | per-piece proofs for batches re-certified with a fresh solver |

The manifests in the GitHub repository give, for each batch or piece, the SHA-256 of its proof, the checker verdicts and
how to regenerate the CNF. `SHA256SUMS` covers the archive parts.

Checkers: drat-trim (commit 2e3b2dc), then cake_lpr (commit a4323b2) on drat-trim's LRAT output.
