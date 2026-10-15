"""Named places x stations: for each of the six single links named in the evidence table of the write-up, which MAPPED fire / EMS / police / hospital stations lie INSIDE the cluster behind the link (on the dwellings' side of it)?
Link -> cluster: the link's child node c; the cluster is topc[c] (the outermost bridge subtree containing c; work/<region>_drv_A_nodes.npz). The script asserts that the cluster's dwelling count top_eq[c] equals the link's dwelling load, i.e. that the link IS the top-level bridge of its cluster.
Facilities: tables/fac_clusters_<region>_drv_A.csv (facilities2.py; Overture categories fire_department, ambulance_and_ems_services, police_department, hospital; mapped stations only). A cluster absent from that table contains none.
usage: named_station_check.py -> tables/named_places_stations.csv"""
import sys, numpy as np, pandas as pd
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
PLACES = [("Walden Rd, Lake Conroe TX", "south-central-tx", "Walden Road", "48339694305"),
          ("Cranes Mill Rd, Canyon Lake TX", "south-central-tx", "Cranes Mill Road", "48091310608"),
          ("Queen Isabella Causeway, South Padre TX", "south-central-tx", "Queen Isabella Causeway", "48061012305"),
          ("E 310 Rd, Grand Lake OK", "eastern-ok", "East 310 Road", "40041375804"),
          ("Alpine Meadows Rd, Olympic Valley CA", "northern-ca", "Alpine Meadows Road", "06061022014"),
          ("Mountainaire Rd, Flagstaff AZ", "maricopa-az", "Mountainaire Road", "04005001500")]
rows, nodes, fac = [], {}, {}
for lab, reg, rn, tr in PLACES:
    Lk = pd.read_csv(f"{OUT}/{reg}_drv_A_links.csv", dtype={"tract": str})
    x = Lk[(Lk.rname == rn) & (Lk.tract == tr)].sort_values("load_dwell", ascending=False).iloc[0]
    z = nodes.setdefault(reg, np.load(f"{WORK}/{reg}_drv_A_nodes.npz")); F = fac.setdefault(reg, pd.read_csv(f"{OUT}/fac_clusters_{reg}_drv_A.csv").set_index("cluster"))
    c = int(x["child"]); cid = int(z["topc"][c]); size = float(z["top_eq"][c])
    assert cid >= 0 and abs(size - float(x.load_dwell)) < 1.0, (lab, cid, size, float(x.load_dwell))     # the link is the top-level bridge of its cluster
    f = F.loc[cid] if cid in F.index else None
    n = {k: (int(f[k]) if f is not None else 0) for k in ("fire", "ems", "police", "hospital")}
    rows.append(dict(place=lab, region=reg, tract=tr, road=rn, dwellings=int(round(size)), cluster=cid, **n, no_fire_ems=int(n["fire"] + n["ems"] == 0)))
D = pd.DataFrame(rows); D.to_csv(f"{OUT}/named_places_stations.csv", index=False)
pd.set_option("display.width", 220); print(D[["place", "dwellings", "fire", "ems", "police", "hospital", "no_fire_ems"]].to_string(index=False))
print(f"\n{int(D.no_fire_ems.sum())} of {len(D)} named places have no mapped fire or EMS station inside their cluster")
