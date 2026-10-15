"""Summaries for the pinhole candidates. usage: pinhole_summary.py -> tables/pinholes_summary.csv, tables/pinholes_top_candidates.csv
Inputs tables/pinholes_<region>_r50.csv (pinhole_list.py). Clusters with >= 100 dwellings. dw_relieved_gap<=Xm = relieved dwellings in clusters whose shortest external gap is <= X m."""
import pandas as pd, sys, os
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
R = [r for r in ALLREG if os.path.exists(f"{OUT}/pinholes_{r}_r50.csv")]
A = pd.concat([pd.read_csv(f"{OUT}/pinholes_{r}_r50.csv", dtype={"tract": str}) for r in R], ignore_index=True)
big = A[A.load_dw >= 100].copy(); rows = []
for name, sub in [(r, big[big.region == r]) for r in R] + [(f"pooled({len(R)})", big)]:
    row = dict(region=name, clusters_ge100=len(sub), dw_in_clusters=sub.load_dw.sum())
    for g in (10, 25, 50):
        m = (sub.share_relieved >= 0.5) & (sub.min_gap_m <= g)
        row[f"clusters_relieved50pct_gap<={g}m"] = int(m.sum()); row[f"dw_relieved_gap<={g}m"] = sub.relieved_dw[(sub.min_gap_m <= g)].sum()
    rows.append(row)
S = pd.DataFrame(rows); S.to_csv(f"{OUT}/pinholes_summary.csv", index=False); print(S.round(0).T.to_string())
top = big[(big.share_relieved >= 0.5) & (big.min_gap_m <= 25)].sort_values("relieved_dw", ascending=False); top.to_csv(f"{OUT}/pinholes_top_candidates.csv", index=False)
print(len(top), "top candidates")
