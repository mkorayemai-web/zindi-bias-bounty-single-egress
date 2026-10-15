#!/bin/sh
# Background driver: coverage_bridge.py for all 5 regions sequentially (small regions first). Logs ../work/cb_<region>.log, marker ../work/cb.done
cd "$(dirname "$0")" || exit 1
PY=${PY:-python3}
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
rm -f ../work/cb.done
for R in eastern-ok eastern-wa northern-ca maricopa-az south-central-tx; do
  echo "$(date -u +%FT%TZ) start $R" >> ../work/cb_driver.log
  $PY coverage_bridge.py $R > ../work/cb_$R.log 2>&1
  echo "$(date -u +%FT%TZ) end $R exit=$?" >> ../work/cb_driver.log
done
date -u +%FT%TZ > ../work/cb.done
