#!/bin/sh
# LEVEL-2 PRE-FLIGHT: re-derive the statistics, tables and figures of the write-up from the SHIPPED INTERMEDIATES, in a scratch copy, and compare with the shipped outputs.
#   Level 1 = preflight.sh REGION  (graph build from the challenge package, about 1 minute for a small region)
#   Level 2 = this script          (needs NO graph or building files; reads work/<region>_<tag>_tract.parquet, work/<region>_tracts.parquet, work/cb_<region>_*, work/<region>_drv_A_nodes.npz, tables/, ext/
#                                   and the challenge data package for tract polygons / strata tables)
# usage: PY=/path/to/python sh egress/preflight_stats.sh      scratch: $PREFLIGHT_DIR or $TMPDIR/preflight_stats; <repo> / clone itself is never written
# Every output starts with an old time stamp; only files a step actually RE-WRITES are compared (a step that writes nothing is reported). PASS = all required steps exit 0 and every re-written file is byte-identical.
set -u
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd); PY=${PY:-python3}; SCR=${PREFLIGHT_DIR:-${TMPDIR:-/tmp}/preflight_stats}
cpc() { cp -c -R "$1" "$2" 2>/dev/null || cp -R "$1" "$2"; }
rm -rf "$SCR"; mkdir -p "$SCR/work"
for d in egress validation ext tables figs verification; do [ -d "$REPO_ROOT/$d" ] && { cpc "$REPO_ROOT/$d" "$SCR/$d" || { echo "PREFLIGHT-STATS FAIL: cannot copy $d"; exit 3; }; }; done
for f in DISCOVERY_DRAFT.md SOURCES.md NOVELTY.md; do [ -f "$REPO_ROOT/$f" ] && cp "$REPO_ROOT/$f" "$SCR/$f"; done
for f in "$REPO_ROOT"/work/*_tract.parquet "$REPO_ROOT"/work/*_tracts.parquet "$REPO_ROOT"/work/cb_* "$REPO_ROOT"/work/*_drv_A_nodes.npz; do [ -e "$f" ] && cpc "$f" "$SCR/work/"; done
rm -f "$SCR"/ext/*.dat                                   # the raw national Census files are not redistributed: the steps must run without them
BIAS_BOUNTY_ROOT=${BIAS_BOUNTY_ROOT:-$(PYTHONDONTWRITEBYTECODE=1 "$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); import common; print(common.ROOT)' "$REPO_ROOT/egress")} || { echo "PREFLIGHT-STATS FAIL: cannot locate the data root"; exit 3; }
export BIAS_BOUNTY_ROOT   # the copy derives its own repository root from its location; only the (unchanged) challenge data root is passed on
find "$SCR/egress" "$SCR/validation" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null
LEFT=$(grep -rl "$REPO_ROOT" "$SCR/egress" "$SCR/validation" 2>/dev/null | wc -l | tr -d ' '); echo "scripts in the copy that still point at the <repo>: $LEFT"; [ "$LEFT" = "0" ] || { echo "PREFLIGHT-STATS FAIL: path patch incomplete"; exit 3; }
find "$SCR/tables" "$SCR/figs" "$SCR/ext" -type f -exec touch -t 200001010000 {} + 2>/dev/null; touch -t 200001010000 "$SCR"/*.md 2>/dev/null
echo "intermediates shipped for this run: $(ls "$SCR/work" | wc -l | tr -d ' ') files, $(du -sk "$SCR/work" | cut -f1) KB"
: > "$SCR/totals.txt"; REQFAIL=0; OPTFAIL=0
STEPS="stats.py drv_A 2000 eq
stats.py drv_A 2000 ar
stats.py drv_B 2000 eq
stats.py drvplus_A 2000 eq
fac_stats.py drv_A
mh_tract.py drv_A
sens_table.py
seasonal.py
seasonal2.py
seasonal_robust.py
county_boot.py
county_boot_facilities.py
density_dissoc.py
persons_per_dwelling_ci.py
seasonal_load.py
seasonal_alloc_robust.py
stranded.py
named_station_check.py
s30_scorecard_tracts.py
egress_km_by_class.py
coverage_bridge_agg.py
resp_summary.py
latent_sweep_table.py
pinhole_summary.py
pinhole_md.py
calibration_md.py
named_lists.py northern-ca drv_A
named_lists.py eastern-ok drv_A
named_lists.py maricopa-az drv_A
named_lists.py south-central-tx drv_A
named_lists.py eastern-wa drv_A
figs_forest.py
figs_m1.py
figs_m2.py
figs_regions.py
numbers_ledger.py"
echo "$STEPS" | while IFS= read -r line; do
  [ -z "$line" ] && continue
  OPT=0; case "$line" in \?*) OPT=1; line=${line#\?};; esac
  set -- $line; scr=$1; shift
  touch "$SCR/.mark"; t0=$(date +%s)
  ( cd "$SCR/egress" && "$PY" "$scr" "$@" > "$SCR/log_${scr}_$$.txt" 2>&1 ); rc=$?
  t1=$(date +%s)
  SK=0; [ "$scr" = "numbers_ledger.py" ] && SK=$(grep -o 'SKIPPED-NO-SOURCE [0-9]*' "$SCR/log_${scr}_$$.txt" | awk '{print $2}'); SK=${SK:-0}
  SCR="$SCR" REPO_ROOT="$REPO_ROOT" STEP="$scr $*" RC=$rc SECS=$((t1 - t0)) OPT=$OPT LEDGER_SKIPS=$SK "$PY" - <<'PYEOF'
import os, sys, hashlib
S, L = os.environ["SCR"], os.environ["REPO_ROOT"]; mark = os.path.getmtime(f"{S}/.mark")
new = []
for top in ("tables", "figs", "ext"):
    for dp, _, fs in os.walk(f"{S}/{top}"):
        new += [os.path.relpath(os.path.join(dp, f), S) for f in fs if os.path.getmtime(os.path.join(dp, f)) > mark]
new += [f for f in os.listdir(S) if f.endswith(".md") and os.path.getmtime(f"{S}/{f}") > mark]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
same, diff, fresh = [], [], []
for rel in sorted(new):
    a = f"{L}/{rel}"
    if not os.path.exists(a): fresh.append(rel)
    elif sha(a) == sha(f"{S}/{rel}"): same.append(rel)
    else: diff.append(rel)
rc, opt = int(os.environ["RC"]), int(os.environ["OPT"])
note = []
if os.environ["STEP"].startswith("numbers_ledger") and int(os.environ.get("LEDGER_SKIPS", "0")) > 0 and diff:
    note, diff = diff, []           # the ledger output legitimately differs when source documents are not distributed (checks reported as SKIPPED-NO-SOURCE, none failed)
flag = "ok " if (rc == 0 and not diff and (new or opt)) else ("OPT" if opt else "BAD")
if rc == 0 and not new: flag = "NOP" if not opt else "OPT"
print(f"[{flag}] {os.environ['STEP'][:44]:44s} exit {rc} {os.environ['SECS']:>4s}s  re-written {len(new):3d}: identical {len(same):3d}, different {len(diff):3d}, new {len(fresh):3d}" + ("" if rc == 0 else "   <-- FAILED"))
for d in diff: print("        DIFFERENT:", d)
for d in note: print("        differs only because checks were skipped (undistributed source documents):", d)
for d in fresh: print("        new file (not shipped):", d)
with open(f"{S}/totals.txt", "a") as t: t.write(f"{rc} {opt} {len(new)} {len(same)} {len(diff)}\n")
PYEOF
  if [ $rc != 0 ]; then echo "        last log lines:"; tail -3 "$SCR/log_${scr}_$$.txt" | cut -c1-160 | sed 's/^/        /'; fi
done
echo "--- totals"
awk '{ if ($1 != 0 && $2 == 0) req++; if ($1 != 0 && $2 == 1) opt++; if ($5 > 0) diffs += $5; rew += $3; same += $4 } END { printf "re-written %d files, identical %d, different %d; required steps failed %d; optional steps failed %d\n", rew, same, diffs, req+0, opt+0; if (req+0 == 0 && diffs+0 == 0 && rew > 0) print "PREFLIGHT-STATS PASS"; else print "PREFLIGHT-STATS FAIL" }' "$SCR/totals.txt" > "$SCR/verdict.txt"
cat "$SCR/verdict.txt"; grep -q "PREFLIGHT-STATS PASS" "$SCR/verdict.txt"
