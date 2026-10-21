#!/bin/sh
# Eastern Washington (415 tracts, added to the scored set 2026-09-28): same configurations as finalize_m1.sh for the other regions.
# Sequential, <=4 threads; logs to work/stage_eastern-wa.log ; writes work/stage_wa.done at the end.
set -e
PY=${PY:-python3}
cd "$(dirname "$0")" || exit 1
R=eastern-wa
echo "=== $R start $(date -u +%FT%TZ)"
$PY build_edges.py $R drv && $PY buildings_prep.py $R && $PY pipeline.py $R drv --force || exit 2
$PY variants.py $R drv A --minload 20
$PY variants.py $R drv B --minload 100
$PY variants.py $R drv A --repair 25
$PY facilities2.py $R drv A
$PY build_edges.py $R drvplus && $PY pipeline.py $R drvplus --force && $PY variants.py $R drvplus A --minload 20 && $PY variants.py $R drvplus B --minload 100 && $PY facilities2.py $R drvplus A || exit 2
echo "=== $R done $(date -u +%FT%TZ)"
date -u +%FT%TZ > ../work/stage_wa.done
