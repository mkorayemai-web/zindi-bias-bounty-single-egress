"""Runner-up candidate: 'hard to reach AND hard to leave' = modelled drive time from the nearest MAPPED fire station (Overture pois, categories.primary = fire_department)
over the same Overture drivable graph, crossed with single-link egress status (S30) from variants.py.
usage: response_time.py REGION [--speedscale F]      -> work/<region>_resp.parquet (per building: minutes), tables/resp_<region>.csv (summary)
Travel time per piece = length / free-flow speed by class (assumption, documented): motorway 29 m/s, trunk 24, primary 20, secondary 16, tertiary 13, unclassified 11,
residential 9, living_street 4.5 (65/55/45/35/30/25/20/10 mph); off-road approach 8 m/s from the building centroid to the snapped piece. Emergency-vehicle speed factor via --speedscale
(1.0 = free flow; 1.25 = lights-and-sirens). Multi-source Dijkstra (scipy csgraph, min_only). Stations are snapped to the nearest piece within 300 m; unsnapped stations are dropped and counted."""
import sys, time, numpy as np, pandas as pd, shapely
from shapely import STRtree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from common import *
from spof import load_graph

region = sys.argv[1]
scale = float(sys.argv[sys.argv.index("--speedscale") + 1]) if "--speedscale" in sys.argv else 1.0
broad = "--broad" in sys.argv
TAGX = ("_broad" if broad else "") + (f"_x{scale:g}" if scale != 1.0 else "")
FIRE_RX = r"(fire (dept|department|station|district|protection|rescue|house|authority)|\bvfd\b|volunteer fire|fire and rescue|fire & rescue|\bfd\b)"
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.0f}s]", *a, flush=True)
SPEED = {"motorway": 29.0, "trunk": 24.0, "primary": 20.0, "secondary": 16.0, "tertiary": 13.0, "unclassified": 11.0, "residential": 9.0, "living_street": 4.5}
G = load_graph(region, "drv")
P, geoms, n, nx, ny = G["P"], G["geoms"], G["n"], G["nx"], G["ny"]
spd = P.cls.map(SPEED).fillna(9.0).values * scale
w = P.len_m.values / spd
df = pd.DataFrame({"u": P.u.values, "v": P.v.values, "w": w})
df["a"] = np.minimum(df.u, df.v); df["b"] = np.maximum(df.u, df.v)
df = df[df.a != df.b].groupby(["a", "b"], as_index=False).w.min()          # parallel pieces: keep the fastest (csr would otherwise SUM duplicates)
A = coo_matrix((np.concatenate([df.w.values, df.w.values]), (np.concatenate([df.a.values, df.b.values]), np.concatenate([df.b.values, df.a.values]))), shape=(n, n)).tocsr()
log("graph", n, "nodes", len(df), "undirected edges")
c = con(threads=2)
where = "categories.primary = 'fire_department'" + (f" OR regexp_matches(lower(coalesce(names.primary,'')), '{FIRE_RX}')" if broad else "")
qry = (f"SELECT id, names.primary AS name, ST_X(ST_Transform(geometry,'EPSG:4326','{CRS_M}',always_xy:=true)) AS x, "
       f"ST_Y(ST_Transform(geometry,'EPSG:4326','{CRS_M}',always_xy:=true)) AS y FROM '{ref(region,'overture-pois')}' WHERE {where} ORDER BY id")
F = c.sql(qry).fetchdf()
fp = shapely.points(F.x.values, F.y.values)
ii, dd = STRtree(geoms).query_nearest(fp, max_distance=300, return_distance=True, all_matches=False)
ok = np.zeros(len(F), bool); ok[ii[0]] = True
pu, pv = P.u.values[ii[1]], P.v.values[ii[1]]
du = (nx[pu] - F.x.values[ii[0]]) ** 2 + (ny[pu] - F.y.values[ii[0]]) ** 2; dv = (nx[pv] - F.x.values[ii[0]]) ** 2 + (ny[pv] - F.y.values[ii[0]]) ** 2
snode = np.unique(np.where(du <= dv, pu, pv))
log("fire stations", len(F), "snapped", int(ok.sum()), "unique nodes", len(snode))
dist = dijkstra(A, directed=False, indices=snode, min_only=True)
tmin = dist / 60.0
log("dijkstra done; reached", int(np.isfinite(tmin).sum()), "of", n)
S = pd.read_parquet(f"{WORK}/{region}_drv_snap.parquet", columns=["bidx", "node", "dist_m", "cand", "tract_i"])
R = pd.read_parquet(f"{WORK}/{region}_drv_A_bres.parquet", columns=["bidx", "egress", "top_eq"])
D = S.merge(R, on="bidx")
nd = np.where(D.node.values >= 0, D.node.values, 0)
D["resp_min"] = np.where((D.node.values >= 0) & (D.dist_m.values <= 500), tmin[nd] + D.dist_m.values / 8.0 / 60.0, np.nan)
D[["bidx", "resp_min"]].to_parquet(f"{WORK}/{region}_resp{TAGX}.parquet")
T = pd.read_parquet(f"{WORK}/{region}_tracts.parquet")
HU = T.housing_units.fillna(0).values.astype("float64")
D = D[D.cand & (D.tract_i >= 0) & (D.egress >= 0)].copy()
ti = D.tract_i.values.astype(int)
nc = np.bincount(ti, minlength=len(T)).astype(float)
D["dw"] = HU[ti] / np.maximum(nc[ti], 1)
D["s30"] = (D.egress.values == 1) & (D.top_eq.values >= 30)
D["unreach"] = ~np.isfinite(D.resp_min.values)
print("stations snapped:", int(ok.sum()), "/", len(F), "| share of dwellings with NO route to any station:", round(float((D.dw * D.unreach).sum() / D.dw.sum()), 4))
for thr in (5, 10, 15, 20):
    far = (D.resp_min.values > thr) | D.unreach.values
    both = far & D.s30.values
    print(f"T>{thr:>2} min: dwellings {float((D.dw*far).sum()):>12,.0f} ({float((D.dw*far).sum()/D.dw.sum()):.3f}) | of them S30 {float((D.dw*both).sum()):>10,.0f} ({float((D.dw*both).sum()/max((D.dw*far).sum(),1)):.3f}) "
          f"| P(S30 | near) {float((D.dw*(D.s30 & ~far)).sum()/max((D.dw*~far).sum(),1)):.3f}")
D["tract"] = T.GEOID.values[ti]
g = D.groupby("tract").apply(lambda x: pd.Series({"dw": x.dw.sum(), "far10": (x.dw * ((x.resp_min > 10) | x.unreach)).sum() / x.dw.sum(), "far15": (x.dw * ((x.resp_min > 15) | x.unreach)).sum() / x.dw.sum(),
                                                  "s30": (x.dw * x.s30).sum() / x.dw.sum(), "both10": (x.dw * (x.s30 & ((x.resp_min > 10) | x.unreach))).sum(), "both15": (x.dw * (x.s30 & ((x.resp_min > 15) | x.unreach))).sum(),
                                                  "med_resp": np.nanmedian(x.resp_min)}), include_groups=False)
g.to_csv(f"{OUT}/resp_{region}{TAGX}.csv"); log("wrote", f"{OUT}/resp_{region}{TAGX}.csv")
