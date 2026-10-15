"""'Stranded' share: how many single-link dwellings have NO mapped fire / EMS station inside their cluster (i.e. on their side of the single link)?
Definition: top-level cluster = the outermost bridge subtree behind which a dwelling sits (work/<region>_drv_A_nodes.npz: topc = cluster id of each node, top_eq = dwellings in that cluster; ACS-weighted 'eq' scheme).
S30 dwellings = dwellings in top-level clusters of >= 30 dwellings (the sum reproduces the region's S30 dwelling total exactly: checked below). Facilities per cluster: tables/fac_clusters_<region>_drv_A.csv (written by facilities2.py; clusters absent from it hold none).
fire = Overture category fire_department, ems = ambulance_and_ems_services, police = police_department, hospital = hospital (mapped stations only; stations filed under other categories are not seen: see response_time.py --broad).
usage: stranded.py -> tables/stranded.csv (one row per region + pooled)"""
import sys, numpy as np, pandas as pd
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
B = pd.read_csv(f"{OUT}/stats_burden_drv_A.csv").set_index("group"); rows = []
for r in ALLREG:
    z = np.load(f"{WORK}/{r}_drv_A_nodes.npz"); topc, top_eq = z["topc"], z["top_eq"]; m = topc >= 0
    C = pd.DataFrame({"cluster": topc[m], "load": top_eq[m].astype(float)}).groupby("cluster").load.agg(["first", "min", "max"])
    assert (C["min"] == C["max"]).all(), "cluster load must be constant within a cluster"
    F = pd.read_csv(f"{OUT}/fac_clusters_{r}_drv_A.csv").set_index("cluster"); C = C.join(F[["fire", "ems", "police", "hospital"]], how="left").fillna(0)
    big = C[C["first"] >= 30]; assert abs(big["first"].sum() - B.loc[r, "dwell_S30"]) < 1.0, (r, big["first"].sum(), B.loc[r, "dwell_S30"])
    nofe = (big.fire + big.ems) == 0; noall = (big.fire + big.ems + big.police + big.hospital) == 0; b3 = big[big["first"] >= 300]
    rows.append(dict(region=r, clusters_ge30=len(big), s30_dwellings=big["first"].sum(), dwellings_no_fire_ems=big["first"][nofe].sum(), dwellings_no_fire_ems_police_hospital=big["first"][noall].sum(),
                     clusters_ge300=len(b3), clusters_ge300_no_fire_ems=int(((b3.fire + b3.ems) == 0).sum())))
D = pd.DataFrame(rows); P = D.drop(columns="region").sum(); P["region"] = "pooled"; D = pd.concat([D, P.to_frame().T], ignore_index=True)
D["share_no_fire_ems"] = D.dwellings_no_fire_ems / D.s30_dwellings; D["share_no_fire_ems_police_hospital"] = D.dwellings_no_fire_ems_police_hospital / D.s30_dwellings
D.to_csv(f"{OUT}/stranded.csv", index=False); pd.set_option("display.width", 220)
print(D[["region", "clusters_ge30", "s30_dwellings", "share_no_fire_ems", "share_no_fire_ems_police_hospital", "clusters_ge300", "clusters_ge300_no_fire_ems"]].round(4).to_string(index=False))
