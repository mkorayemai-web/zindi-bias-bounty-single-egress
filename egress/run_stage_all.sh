#!/bin/sh
# Sequential batch over regions (memory-friendly: one region at a time). Smaller regions first; TX drvplus skipped (memory).
cd "$(dirname "$0")" || exit 1
for R in northern-ca eastern-ok maricopa-az; do
  sh ./run_stage.sh $R > ../work/stage_$R.log 2>&1
done
sh ./run_stage.sh south-central-tx skip_plus > ../work/stage_south-central-tx.log 2>&1
echo "ALL DONE $(date -u +%FT%TZ)" > ../work/stage_all.done
