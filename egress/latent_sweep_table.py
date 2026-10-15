"""Collect the latent-connection sweep into one table. usage: latent_sweep_table.py -> tables/latent_connection_sweep.csv
Inputs: tables/sens_nearmiss2_<region>.csv (sens_nearmiss2.py: radii 50/100/250 m, scored classes, sink A), tables/<region>_drv_A_r25_summary.csv (variants.py --repair 25).
Columns: S30 share (dwellings) at baseline and after snapping dead-end tips to the nearest unconnected road piece within r; cut_<r>m_pct = relative reduction of the S30 share. UPPER BOUND for r > 25 m."""
import os, pandas as pd, sys
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
rows = []
for r in ALLREG:
    f = f"{OUT}/sens_nearmiss2_{r}.csv"
    if not os.path.exists(f): print(r, "pending"); continue
    d = pd.read_csv(f).set_index("label"); b = d.loc["baseline"]; base30 = b.spof30
    r25 = pd.read_csv(f"{OUT}/{r}_drv_A_r25_summary.csv"); r25s30 = float(r25[r25.scheme == "eq"]["s30"].iloc[0])
    row = dict(region=r, S30_base=base30, S30_r25=r25s30, cut_25m_pct=100 * (1 - r25s30 / base30), dead_ends=d.loc["repair_50m", "dead_ends"])
    for k in (50, 100, 250):
        row[f"S30_{k}m"] = d.loc[f"repair_{k}m", "spof30"]; row[f"cut_{k}m_pct"] = 100 * (1 - row[f"S30_{k}m"] / base30)
        row[f"repairs_{k}m"] = d.loc[f"repair_{k}m", "repaired"]; row[f"median_repair_dist_{k}m"] = d.loc[f"repair_{k}m", "median_repair_dist_m"]
    rows.append(row)
R = pd.DataFrame(rows); R.to_csv(f"{OUT}/latent_connection_sweep.csv", index=False)
pd.set_option("display.width", 250); print(R.round(3).T.to_string())
