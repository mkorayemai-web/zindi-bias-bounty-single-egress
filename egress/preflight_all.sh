#!/bin/sh
# Full-entry two-tier check; expensive, serial. See REPRODUCE.md.
# PY=/path/to/python sh egress/preflight_all.sh
# PY=/path/to/python sh egress/preflight_all.sh --existing-rebuild /absolute/completed/scratch
set -eu
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 ARROW_IO_THREADS=1
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY=${PY:-python3}
exec "$PY" "$REPO_ROOT/egress/full_preflight.py" "$@"
