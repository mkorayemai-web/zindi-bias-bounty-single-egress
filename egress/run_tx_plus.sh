#!/bin/sh
# Queued job: the missing +service/track variant for south-central-tx (needed so the pooled 'robust to map incompleteness' share is not missing the largest region).
# Waits for the latent-connection sweep (nm2.done) and the coverage-bridge rerun (cb.done), then: build_edges drvplus -> pipeline drvplus -> variants drvplus A (minload 20) -> coverage_bridge rerun for TX.
# Logs ../work/txplus_*.log ; marker ../work/txplus.done. <=4 threads (duckdb), numpy single thread.
cd "$(dirname "$0")" || exit 1
PY=${PY:-python3}
R=south-central-tx
rm -f ../work/txplus.done
while [ ! -f ../work/nm2.done ] || [ ! -f ../work/cb.done ]; do sleep 20; done
echo "$(date -u +%FT%TZ) start build_edges" >> ../work/txplus_driver.log
$PY build_edges.py $R drvplus > ../work/txplus_build.log 2>&1 || { echo "$(date -u +%FT%TZ) build FAILED" >> ../work/txplus_driver.log; exit 2; }
echo "$(date -u +%FT%TZ) start pipeline" >> ../work/txplus_driver.log
$PY pipeline.py $R drvplus --force > ../work/txplus_pipeline.log 2>&1 || { echo "$(date -u +%FT%TZ) pipeline FAILED" >> ../work/txplus_driver.log; exit 3; }
echo "$(date -u +%FT%TZ) start variants" >> ../work/txplus_driver.log
$PY variants.py $R drvplus A --minload 20 > ../work/txplus_variants.log 2>&1 || { echo "$(date -u +%FT%TZ) variants FAILED" >> ../work/txplus_driver.log; exit 4; }
$PY coverage_bridge.py $R > ../work/cb_$R.log 2>&1
echo "$(date -u +%FT%TZ) done" >> ../work/txplus_driver.log
date -u +%FT%TZ > ../work/txplus.done
