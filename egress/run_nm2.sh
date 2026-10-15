#!/bin/sh
# Background driver: wide-radius latent-connection sweep, all 5 regions sequentially (single-thread numpy; <= 1 thread). Logs in ../work/nm2_<region>.log; done-marker ../work/nm2.done
cd "$(dirname "$0")" || exit 1
PY=${PY:-python3}
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
rm -f ../work/nm2.done
for R in northern-ca eastern-ok eastern-wa maricopa-az south-central-tx; do
  echo "$(date -u +%FT%TZ) start $R" >> ../work/nm2_driver.log
  $PY sens_nearmiss2.py $R 50 100 250 > ../work/nm2_$R.log 2>&1
  echo "$(date -u +%FT%TZ) end $R exit=$?" >> ../work/nm2_driver.log
done
date -u +%FT%TZ > ../work/nm2.done
