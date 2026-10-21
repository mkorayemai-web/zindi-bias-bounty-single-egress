#!/bin/sh
# Re-run every configuration with the final code, then all statistics/tables for M1. Waits for the heavy stage batch (work/stage_all.done).
set -e
PY=${PY:-python3}
cd "$(dirname "$0")" || exit 1
n=0
while [ ! -f ../work/stage_all.done ] && [ $n -lt 240 ]; do sleep 30; n=$((n+1)); done
echo "=== finalize start $(date -u +%FT%TZ) (waited $n x 30s)"
for R in northern-ca eastern-ok maricopa-az south-central-tx; do
  $PY variants.py $R drv A --minload 20
  $PY variants.py $R drv B --minload 100
  $PY variants.py $R drv A --repair 25
  $PY facilities2.py $R drv A
done
for R in northern-ca eastern-ok maricopa-az; do
  $PY variants.py $R drvplus A --minload 20
  $PY variants.py $R drvplus B --minload 100
  $PY facilities2.py $R drvplus A
done
$PY stats.py drv_A 2000 eq > ../tables/stats_drv_A_eq.log 2>&1
$PY stats.py drv_A 2000 ar > ../tables/stats_drv_A_ar.log 2>&1
$PY stats.py drvplus_A 2000 eq > ../tables/stats_drvplus_A_eq.log 2>&1
$PY stats.py drv_B 2000 eq > ../tables/stats_drv_B_eq.log 2>&1
$PY fac_stats.py drv_A 2000 > ../tables/fac_stats_drv_A.log 2>&1
$PY fac_stats.py drvplus_A 2000 > ../tables/fac_stats_drvplus_A.log 2>&1
$PY mh_tract.py drv_A 2000 > ../tables/mh_tract_drv_A.log 2>&1
$PY sens_table.py > ../tables/sens_grid.log 2>&1
for R in northern-ca eastern-ok maricopa-az south-central-tx; do $PY named_lists.py $R drv_A > /dev/null 2>&1; done
echo "=== finalize done $(date -u +%FT%TZ)" > ../work/finalize.done
