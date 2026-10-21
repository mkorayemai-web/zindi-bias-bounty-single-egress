#!/bin/sh
# Two-tier, one-region clean-room check. Rebuilds the configurations printed in
# that region's sensitivity table; pooled findings need preflight_all.sh.
# Exit status follows the printed-number ledger ONLY. The unchanged strict
# comparator is informational, with every difference retained in its own log.
# Usage: PY=/path/to/python PREFLIGHT_DIR=/absolute/scratch sh egress/preflight.sh eastern-wa
set -eu
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 ARROW_IO_THREADS=1
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY=${PY:-python3}
exec "$PY" "$REPO_ROOT/egress/quick_preflight.py" "$@"
