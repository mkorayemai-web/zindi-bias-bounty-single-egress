#!/bin/sh
# CLEAN-ROOM PRE-FLIGHT FOR THE ROBUSTNESS CHAIN of one region (service/track roads, 25 m digitising-gap repair, latent-connection sweeps, coverage bridge), in a scratch COPY of the lane.
# It takes the region's main-graph files (work/<R>_tracts, _bldg, _drv_snap, _drv_A_bres ...; egress/preflight.sh rebuilds those) as given, DELETES the region's
# +service/track files (work/<R>_drvplus*, tables/*<R>*drvplus*), repair-25 files (work/<R>_drv_A_r25*, tables/<R>_drv_A_r25*), latent-connection sweep files (work/<R>_nm*,
# tables/sens_nearmiss2_<R>.csv) and coverage-bridge files (work/cb_<R>_*), rebuilds them (build_edges drvplus -> pipeline drvplus -> variants drvplus A (and B) -> facilities2 drvplus A ->
# variants drv A --repair 25 -> coverage_bridge -> sens_nearmiss2 50 100 250) and compares every re-written file with the shipped one. The lane itself is never written (every script derives its paths from its own location, so the copy works on the copy).
#   usage:  PY=/path/to/python sh egress/preflight_bridge.sh [REGION]     scratch dir: $PREFLIGHT_DIR or $TMPDIR/preflight_bridge_<REGION>
#   Needs the region's main-graph files (so: the lane host, not a published clone: the repository ships no building or snap files) and the challenge package.
#   Prints "BRIDGE-PREFLIGHT PASS" only if (i) every command exited 0, (ii) every file of the core list was DELETED first and RE-WRITTEN by the run, (iii) all re-written
#   csv/txt files are byte-identical and parquet/npz contents are equal. Texas has no drvplus B or drvplus facility tables (as in the shipped set), so it skips those two steps.
set -u
REGION=${1:-eastern-wa}
LANE=$(cd "$(dirname "$0")/.." && pwd)
PY=${PY:-python3}
SCR=${PREFLIGHT_DIR:-${TMPDIR:-/tmp}/preflight_bridge_$REGION}
rm -rf "$SCR"; mkdir -p "$SCR" "$SCR/figs"
for d in egress validation ext work tables; do cp -c -R "$LANE/$d" "$SCR/$d" 2>/dev/null || cp -R "$LANE/$d" "$SCR/$d" || { echo "BRIDGE-PREFLIGHT FAIL: cannot copy $d"; exit 3; }; done
# 1. the copied scripts derive every path from their own location (nothing to patch); the challenge data stays where it is
BIAS_BOUNTY_ROOT=${BIAS_BOUNTY_ROOT:-$(PYTHONDONTWRITEBYTECODE=1 "$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); import common; print(common.ROOT)' "$LANE/egress")} || { echo "BRIDGE-PREFLIGHT FAIL: cannot locate the data root"; exit 3; }
export BIAS_BOUNTY_ROOT   # the copy derives its own repository root from its location; only the (unchanged) challenge data root is passed on
find "$SCR/egress" "$SCR/validation" -name __pycache__ -type d -prune -exec rm -rf {} +
LEFT=$(grep -rl "$LANE" "$SCR/egress" "$SCR/validation" 2>/dev/null | wc -l | tr -d ' '); echo "scripts in the copy that still point at the real lane: $LEFT"; [ "$LEFT" = "0" ] || { echo "BRIDGE-PREFLIGHT FAIL: path patch incomplete"; exit 3; }
# 2. clean slate: delete the region's +service/track, repair-25, latent-connection-sweep and coverage-bridge files
( cd "$SCR" && ls -1 work/"$REGION"_drvplus* work/"$REGION"_drv_A_r25* work/"$REGION"_nm* work/cb_"$REGION"_* tables/*"$REGION"*drvplus* tables/"$REGION"_drv_A_r25* tables/sens_nearmiss2_"$REGION".csv 2>/dev/null ) | sort -u > "$SCR/deleted.txt"
rm -f "$SCR"/work/"$REGION"_drvplus* "$SCR"/work/"$REGION"_drv_A_r25* "$SCR"/work/"$REGION"_nm* "$SCR"/work/cb_"$REGION"_* "$SCR"/tables/*"$REGION"*drvplus* "$SCR"/tables/"$REGION"_drv_A_r25* "$SCR"/tables/sens_nearmiss2_"$REGION".csv
echo "files deleted: $(wc -l < "$SCR/deleted.txt" | tr -d ' '); left of them: $(ls "$SCR/work" "$SCR/tables" | grep -c -E "${REGION}_drvplus|${REGION}_drv_A_r25|${REGION}_nm|^cb_${REGION}_|${REGION}.*drvplus|^sens_nearmiss2_${REGION}")"
# 3. run the chain; stop at the first failing command
RC=0; T0=$(date +%s)
cd "$SCR/egress" || exit 3
run() { echo "--- python $*  [$(date -u +%T)]"; $PY "$@" > "$SCR/step.log" 2>&1 || { echo "FAILED: $*"; tail -5 "$SCR/step.log"; RC=2; return 1; }; }
run build_edges.py $REGION drvplus && run pipeline.py $REGION drvplus --force && run variants.py $REGION drvplus A --minload 20 \
  && { [ "$REGION" = "south-central-tx" ] || { run variants.py $REGION drvplus B --minload 100 && run facilities2.py $REGION drvplus A; }; } \
  && run variants.py $REGION drv A --repair 25 && run coverage_bridge.py $REGION && run sens_nearmiss2.py $REGION 50 100 250
echo "robustness chain: $(( $(date +%s) - T0 )) s"
# 4. compare with the shipped files
LANE="$LANE" SCR="$SCR" REGION="$REGION" RC="$RC" "$PY" - <<'EOF'
import os, sys, hashlib, numpy as np, pandas as pd
L, S, R, RC = os.environ["LANE"], os.environ["SCR"], os.environ["REGION"], int(os.environ["RC"])
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
deleted = [l.strip() for l in open(f"{S}/deleted.txt") if l.strip()]
core = {w for w in (f"work/{R}_drvplus_snap.parquet", f"work/{R}_drvplus_A_bres.parquet", f"work/{R}_drvplus_A_tract.parquet", f"work/{R}_drvplus_A_nodes.npz",
                    f"tables/{R}_drvplus_A_summary.csv", f"tables/{R}_drvplus_A_links.csv", f"work/{R}_drv_A_r25_bres.parquet", f"work/{R}_drv_A_r25_tract.parquet",
                    f"tables/{R}_drv_A_r25_summary.csv", f"work/cb_{R}_conc.csv", f"work/cb_{R}_prov.parquet", f"work/cb_{R}_link.parquet",
                    f"tables/sens_nearmiss2_{R}.csv", f"work/{R}_nm0_bld.parquet", f"work/{R}_nm50_bld.parquet", f"work/{R}_nm50_pairs.parquet", f"work/{R}_nm100_bld.parquet",
                    f"work/{R}_nm100_pairs.parquet", f"work/{R}_nm250_bld.parquet", f"work/{R}_nm250_pairs.parquet") if os.path.exists(f"{L}/{w}")}
bad, same, later = 0, 0, []
for rel in sorted(core - set(deleted)): print(f"  {rel:58s} was not deleted (required file missing)"); bad += 1
for rel in deleted:
    a, b = f"{L}/{rel}", f"{S}/{rel}"
    if not os.path.exists(b):
        if rel in core: print(f"  {rel:58s} NOT RE-WRITTEN by the run (required)"); bad += 1
        else: later.append(rel)
        continue
    if rel.endswith(".parquet"): A, B = pd.read_parquet(a), pd.read_parquet(b); ok = A.shape == B.shape and A.equals(B)
    elif rel.endswith(".npz"): za, zb = np.load(a), np.load(b); ok = za.files == zb.files and all(np.array_equal(za[k], zb[k], equal_nan=True) for k in za.files)
    else: ok = sha(a) == sha(b)
    print(f"  {rel:58s} {'identical' if ok else 'DIFFERENT'}"); bad += (not ok); same += ok
print(f"deleted before the run: {len(deleted)}; re-written and compared: {same + bad}; identical: {same}; problems: {bad}; command failures: {'yes' if RC else 'none'}")
print(f"not re-written by this chain, not compared ({len(later)}): " + ", ".join(os.path.basename(x) for x in later[:12]) + (" ..." if len(later) > 12 else ""))
print("BRIDGE-PREFLIGHT PASS" if (bad == 0 and RC == 0 and same >= len(core)) else "BRIDGE-PREFLIGHT FAIL"); sys.exit(0 if (bad == 0 and RC == 0 and same >= len(core)) else 1)
EOF
