"""Facility-level lookups on a finished SPOF run (needs work/<tag>_nodes.npz from variants.py).
usage: facilities2.py REGION CSET SINK
Snaps selected Overture POIs (mobile-home parks, senior care, schools, fire/EMS ... ) to the drivable graph and reads off, for each facility,
the egress class (0 none, 1 single route, 2 >=2 routes), the dwellings/persons behind its worst single link and the cluster id (top-bridge child node).
Outputs tables/fac_<tag>.csv (one row per facility) and tables/fac_clusters_<tag>.csv (per top-level cluster: facilities inside)."""
import sys, time, numpy as np, pandas as pd, shapely
from shapely import STRtree
from common import *
from spof import load_graph

region, cset, sinkv = sys.argv[1], sys.argv[2], sys.argv[3]
tag = f"{region}_{cset}_{sinkv}"
t0 = time.time()
KINDS = {
 "mobile_home_park": ["mobile_home_park"],
 "senior_care": ["skilled_nursing", "assisted_living_facility", "retirement_home", "hospice", "senior_citizen_services"],
 "dialysis": ["dialysis_clinic"],
 "childcare": ["day_care_preschool", "child_care_and_day_care", "preschool"],
 "school": ["elementary_school", "middle_school", "high_school", "school", "private_school", "public_school"],
 "hospital": ["hospital"], "fire": ["fire_department"], "ems": ["ambulance_and_ems_services"], "police": ["police_department"],
 "campground_rv": ["campground", "rv_park"], "shelter_housing": ["homeless_shelter", "housing_authorities", "community_center"],
}
inv = {c_: k for k, v in KINDS.items() for c_ in v}
cl = ",".join(f"'{c}'" for c in inv)
c = con(threads=2)
F = c.sql(f"""
SELECT id, categories.primary AS cat, names.primary AS name, operating_status, confidence,
       ST_X(geometry) AS lon, ST_Y(geometry) AS lat,
       ST_X(ST_Transform(geometry,'EPSG:4326','{CRS_M}',always_xy:=true)) AS x, ST_Y(ST_Transform(geometry,'EPSG:4326','{CRS_M}',always_xy:=true)) AS y,
       addresses[1].locality AS locality, addresses[1].postcode AS postcode
FROM '{ref(region,'overture-pois')}' WHERE categories.primary IN ({cl}) ORDER BY id""").fetchdf()
F["kind"] = F.cat.map(inv)
G = load_graph(region, cset)
P, nx, ny = G["P"], G["nx"], G["ny"]
Z = np.load(f"{WORK}/{tag}_nodes.npz")
nb, reached, topc, top_eq, top_pers = Z["nb"], Z["reached"], Z["topc"], Z["top_eq"], Z["top_pers"]
fp = shapely.points(F.x.values, F.y.values)
ii, dd = STRtree(G["geoms"]).query_nearest(fp, max_distance=3000, return_distance=True, all_matches=False)
F["piece"] = -1; F["dist_m"] = np.nan
F.loc[ii[0], "piece"] = ii[1]; F.loc[ii[0], "dist_m"] = dd
ok = F.piece.values >= 0
pu = P.u.values[F.piece.values[ok]]; pv = P.v.values[F.piece.values[ok]]
du = (nx[pu] - F.x.values[ok]) ** 2 + (ny[pu] - F.y.values[ok]) ** 2; dv = (nx[pv] - F.x.values[ok]) ** 2 + (ny[pv] - F.y.values[ok]) ** 2
node = np.where(du <= dv, pu, pv)
F["node"] = -1; F.loc[ok, "node"] = node
nd = np.maximum(F.node.values, 0)
eg = np.full(len(F), -1)
r = reached[nd] & ok
eg[ok & ~r] = 0
eg[ok & r & (nb[nd] >= 1)] = 1
eg[ok & r & (nb[nd] == 0)] = 2
F["egress"] = eg
F["cluster"] = np.where(ok & r & (nb[nd] >= 1), topc[nd], -1)
F["load_dwell"] = np.where(F.cluster.values >= 0, top_eq[nd], 0.0)
F["load_persons"] = np.where(F.cluster.values >= 0, top_pers[nd], 0.0)
tr = __import__("geopandas").read_parquet(strata(region, "census-tracts")).to_crs(CRS_M)
a, b = STRtree(tr.geometry.values).query(fp, predicate="intersects")
tmp = pd.DataFrame({"i": a, "t": b}).drop_duplicates("i"); F["tract"] = None
F.loc[tmp.i.values, "tract"] = tr.GEOID.values[tmp.t.values]
F.drop(columns=["x", "y", "piece", "node"]).to_csv(f"{OUT}/fac_{tag}.csv", index=False)
# facilities per cluster
Fc = F[(F.cluster >= 0) & (F.dist_m <= 500)]
CL = Fc.pivot_table(index="cluster", columns="kind", values="id", aggfunc="count", fill_value=0).reset_index()
CL.to_csv(f"{OUT}/fac_clusters_{tag}.csv", index=False)
print(tag, "facilities", len(F), "within 500 m of graph", int((F.dist_m <= 500).sum()), f"{time.time()-t0:.0f}s")
g = F[F.dist_m <= 500].groupby("kind").apply(lambda d: pd.Series({"n": len(d), "single": (d.egress == 1).mean(), "s30": ((d.egress == 1) & (d.load_dwell >= 30)).mean(),
        "s100": ((d.egress == 1) & (d.load_dwell >= 100)).mean(), "none": (d.egress == 0).mean()}))
print(g.round(3))
