#!/bin/sh
# Stage runner: build -> snap cache -> variants for one region. usage: run_stage.sh REGION [skip_plus]
# Sequential, <=4 threads; logs to work/stage_<region>.log
PY=${PY:-python3}
cd "$(dirname "$0")" || exit 1
R=$1
echo "=== $R start $(date -u +%FT%TZ)"
$PY build_edges.py $R drv && $PY buildings_prep.py $R && $PY pipeline.py $R drv --force || exit 2
$PY variants.py $R drv A --minload 100
$PY variants.py $R drv B --minload 100
$PY variants.py $R drv A --repair 25
if [ "$2" != "skip_plus" ]; then
  $PY build_edges.py $R drvplus && $PY pipeline.py $R drvplus --force && $PY variants.py $R drvplus A --minload 100 && $PY variants.py $R drvplus B --minload 100
fi
echo "=== $R done $(date -u +%FT%TZ)"
