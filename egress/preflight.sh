#!/bin/sh
# CLEAN-ROOM PRE-FLIGHT: re-runs REPRODUCE.md step 1 (one region, default eastern-wa) and the four validation scripts in a scratch COPY of the lane,
# then compares every regenerated output with the shipped one. The lane itself is never written (every script derives its paths from its own location, so the copy works on the copy).
#   usage:  PY=/path/to/python sh egress/preflight.sh [REGION]        scratch dir: $PREFLIGHT_DIR or $TMPDIR/preflight_<REGION>
#   Needs the same inputs as step 1 (the competition data package reachable by common.py) and ~1 min (eastern-wa) + ~1.5 min (validations).
#   Prints "PREFLIGHT PASS" only if (i) every command exited 0, (ii) every artifact of the region and every validation table was DELETED first and
#   RE-WRITTEN by the run (so a silent no-op cannot pass), (iii) all regenerated csv/txt files are byte-identical and parquet/npz contents are equal.
set -u
REGION=${1:-eastern-wa}
LANE=$(cd "$(dirname "$0")/.." && pwd)
PY=${PY:-python3}
SCR=${PREFLIGHT_DIR:-${TMPDIR:-/tmp}/preflight_$REGION}
rm -rf "$SCR"; mkdir -p "$SCR" "$SCR/figs"
for d in egress validation ext work tables; do cp -c -R "$LANE/$d" "$SCR/$d" 2>/dev/null || cp -R "$LANE/$d" "$SCR/$d" || { echo "PREFLIGHT FAIL: cannot copy $d"; exit 3; }; done
# 1. the copied scripts derive every path from their own location (nothing to patch); the challenge data stays where it is
BIAS_BOUNTY_ROOT=${BIAS_BOUNTY_ROOT:-$(PYTHONDONTWRITEBYTECODE=1 "$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); import common; print(common.ROOT)' "$LANE/egress")} || { echo "PREFLIGHT FAIL: cannot locate the data root"; exit 3; }
export BIAS_BOUNTY_ROOT   # the copy derives its own repository root from its location; only the (unchanged) challenge data root is passed on
find "$SCR/egress" "$SCR/validation" -name __pycache__ -type d -prune -exec rm -rf {} +
LEFT=$(grep -rl "$LANE" "$SCR/egress" "$SCR/validation" 2>/dev/null | wc -l | tr -d ' '); echo "scripts in the copy that still point at the real lane: $LEFT"; [ "$LEFT" = "0" ] || { echo "PREFLIGHT FAIL: path patch incomplete"; exit 3; }
# 2. clean slate: delete every artifact of the region and every validation table
( cd "$SCR" && ls -1 work/*"$REGION"* tables/*"$REGION"* tables/validation_* 2>/dev/null ) | sort -u > "$SCR/deleted.txt"
rm -f "$SCR"/work/*"$REGION"* "$SCR"/tables/*"$REGION"* "$SCR"/tables/validation_*
echo "region artifacts left: $(ls "$SCR/work" "$SCR/tables" | grep -c "$REGION"); validation tables left: $(ls "$SCR/tables" | grep -c '^validation_')"
# 3. run the chain (REPRODUCE.md step 1) and the validations; stop at the first failing command
RC=0; T0=$(date +%s)
cd "$SCR/egress" || exit 3
for step in "build_edges.py $REGION drv" "buildings_prep.py $REGION" "pipeline.py $REGION drv --force" "variants.py $REGION drv A --minload 20" "facilities2.py $REGION drv A"; do
  echo "--- python $step  [$(date -u +%T)]"; $PY $step > "$SCR/step.log" 2>&1 || { echo "FAILED: $step"; tail -5 "$SCR/step.log"; RC=2; break; }
done
# the Hays repair validation (validate_hays_repair.py) reads south-central-tx's repair-25 and 50/100/250 m latent-connection variants, which the five commands above do not make:
# when this region is the one under test (its work/ files were deleted above), rebuild them as well; their outputs are compared like everything else
if [ $RC = 0 ] && [ "$REGION" = "south-central-tx" ]; then for step in "variants.py $REGION drv A --repair 25" "sens_nearmiss2.py $REGION 50 100 250"; do
  echo "--- python $step  [$(date -u +%T)]"; $PY $step > "$SCR/step.log" 2>&1 || { echo "FAILED: $step"; tail -5 "$SCR/step.log"; RC=2; break; }
done; fi
T1=$(date +%s); echo "region chain: $((T1 - T0)) s"
cd "$SCR/validation" || exit 3
VAL=0; [ -f "$SCR/work/northern-ca_bldg.parquet" ] && [ -f "$SCR/work/south-central-tx_bldg.parquet" ] && [ -f "$SCR/work/northern-ca_drv_A_bres.parquet" ] && [ -f "$SCR/work/south-central-tx_drv_A_bres.parquet" ] && VAL=1   # the validators read the (unshipped) building / residual files of both regions
if [ $RC = 0 ] && [ $VAL = 1 ]; then for s in validate_tehama.py validate_hays.py validate_hays_repair.py validate_tehama_repair.py; do
  echo "--- $s  [$(date -u +%T)]"; $PY $s > "$SCR/step.log" 2>&1 || { echo "FAILED: $s"; tail -5 "$SCR/step.log"; RC=2; break; }
done; fi
[ $VAL = 0 ] && echo "validations skipped (northern-ca / south-central-tx not built)"
echo "validations: $(( $(date +%s) - T1 )) s"
# 4. compare with the shipped files
VAL="$VAL" LANE="$LANE" SCR="$SCR" REGION="$REGION" RC="$RC" "$PY" - <<'EOF'
import os, sys, hashlib, glob, numpy as np, pandas as pd
L, S, R, RC = os.environ["LANE"], os.environ["SCR"], os.environ["REGION"], int(os.environ["RC"])
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
deleted = [l.strip() for l in open(f"{S}/deleted.txt") if l.strip()]          # every region artifact + validation table removed before the run
core = {f"tables/{R}_drv_A_summary.csv", f"tables/{R}_drv_A_links.csv", f"tables/fac_{R}_drv_A.csv", f"tables/fac_clusters_{R}_drv_A.csv"} | {w for w in (f"work/{R}_drv_snap.parquet", f"work/{R}_drv_A_tract.parquet", f"work/{R}_drv_A_nodes.npz") if os.path.exists(f"{L}/{w}")}   # work/ files are compared only where the lane ships them (a published clone has no work/)
if R == "south-central-tx": core |= {w for w in (f"work/{R}_drv_A_r25_bres.parquet", f"work/{R}_nm50_bld.parquet", f"work/{R}_nm100_bld.parquet", f"work/{R}_nm250_bld.parquet") if os.path.exists(f"{L}/{w}")}   # rebuilt by the extra steps above
if os.environ.get("VAL") == "1": core |= {d for d in deleted if os.path.basename(d).startswith("validation_")}
else: print("validations skipped: northern-ca and south-central-tx are not built here (REPRODUCE.md sections 1-3); only the region chain is compared")
bad, same, later = 0, 0, []
for rel in sorted(core - set(deleted)): print(f"  {rel:58s} was not in the shipped lane: nothing to compare (required file missing)"); bad += 1
for rel in deleted:
    a, b = f"{L}/{rel}", f"{S}/{rel}"
    if not os.path.exists(b):
        if rel in core: print(f"  {rel:58s} NOT RE-WRITTEN by the run (required)"); bad += 1
        else: later.append(rel)                                                    # written by a later pipeline stage that this chain does not run
        continue
    if rel.endswith(".parquet"): A, B = pd.read_parquet(a), pd.read_parquet(b); ok = A.shape == B.shape and A.equals(B)
    elif rel.endswith(".npz"): za, zb = np.load(a), np.load(b); ok = za.files == zb.files and all(np.array_equal(za[k], zb[k], equal_nan=True) for k in za.files)
    else: ok = sha(a) == sha(b)
    print(f"  {rel:58s} {'identical' if ok else 'DIFFERENT'}"); bad += (not ok); same += ok
print(f"deleted before the run: {len(deleted)}; re-written and compared: {same + bad}; identical: {same}; problems: {bad}; command failures: {'yes' if RC else 'none'}")
print(f"not produced by this chain (later pipeline stages: drvplus variants, named lists, pinholes, response times ...), not compared: {len(later)}")
print("PREFLIGHT PASS" if (bad == 0 and RC == 0 and same >= len(core)) else "PREFLIGHT FAIL"); sys.exit(0 if (bad == 0 and RC == 0 and same >= len(core)) else 1)
EOF
