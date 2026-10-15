"""Stage 1 (heavy, cached): snap every Overture building centroid to the nearest drivable road piece and to a census tract.
usage: pipeline.py REGION CSET [--force]       CSET in {drv, drvplus}
Reads  work/<region>_<cset>_pieces.parquet (build_edges.py) and work/<region>_bldg.parquet (buildings_prep.py)
Writes work/<region>_<cset>_snap.parquet : bidx, piece, node, dist_m, ncls (class code of the nearest piece), tract_i, cand, area_m2
        work/<region>_tracts.parquet     : tract index -> GEOID, HU (ACS B25001), pop_total (2020 DHC)
Chunked so that the 11.5 M-building Texas region fits in a few GB. Seeded/deterministic (no randomness)."""
import sys, os, time, numpy as np, pandas as pd, shapely, geopandas as gpd
from shapely import STRtree
from common import *
from spof import load_graph, NONRES_SUB, NONRES_CLS

region, cset = sys.argv[1], sys.argv[2]
force = "--force" in sys.argv
out = f"{WORK}/{region}_{cset}_snap.parquet"
if os.path.exists(out) and not force:
    print("exists", out); sys.exit(0)
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.0f}s]", *a, flush=True)

G = load_graph(region, cset)
P, geoms, nx, ny = G["P"], G["geoms"], G["nx"], G["ny"]
CLS = {c: i for i, c in enumerate(["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "unclassified", "living_street", "service", "track"])}
pcls = P.cls.map(CLS).fillna(-1).astype("int8").values
pu, pv = P.u.values, P.v.values
log("graph loaded", len(P), "pieces")
tr = gpd.read_parquet(strata(region, "census-tracts")).to_crs(CRS_M)
geoid = tr.GEOID.values
st = pd.read_parquet(strata(region), columns=["GEOID", "pop_total"]).set_index("GEOID")
acs = pd.read_parquet(ref(region, "census-acs-housing"), columns=["GEOID", "housing_units"]).set_index("GEOID")
T = pd.DataFrame({"GEOID": geoid}).join(acs, on="GEOID").join(st, on="GEOID")
T.to_parquet(f"{WORK}/{region}_tracts.parquet")
ttree = STRtree(tr.geometry.values)
B = pd.read_parquet(f"{WORK}/{region}_bldg.parquet", columns=["bidx", "x", "y", "area_m2", "subtype", "class"])
N = len(B)
log("buildings", N)
x = B.x.values; y = B.y.values
tree = STRtree(geoms)
piece = np.full(N, -1, dtype=np.int32); dist = np.full(N, np.nan, dtype=np.float32); tract_i = np.full(N, -1, dtype=np.int16)
CH = 1_000_000
for s in range(0, N, CH):
    e = min(N, s + CH)
    pts = shapely.points(x[s:e], y[s:e])
    ii, dd = tree.query_nearest(pts, max_distance=1500, return_distance=True, all_matches=False)
    piece[s + ii[0]] = ii[1]; dist[s + ii[0]] = dd
    a, b = ttree.query(pts, predicate="intersects")
    d = pd.DataFrame({"i": a, "t": b}).drop_duplicates("i")
    tract_i[s + d.i.values] = d.t.values
    log(f"chunk {s}-{e}")
ok = piece >= 0
node = np.full(N, -1, dtype=np.int32)
p_ok = piece[ok]
du = (nx[pu[p_ok]] - x[ok]) ** 2 + (ny[pu[p_ok]] - y[ok]) ** 2
dv = (nx[pv[p_ok]] - x[ok]) ** 2 + (ny[pv[p_ok]] - y[ok]) ** 2
node[ok] = np.where(du <= dv, pu[p_ok], pv[p_ok])
ncls = np.full(N, -1, dtype=np.int8); ncls[ok] = pcls[p_ok]
cand = ((B.area_m2.values >= 35) & ~B.subtype.isin(NONRES_SUB).values & ~B["class"].isin(NONRES_CLS).values)
pd.DataFrame({"bidx": B.bidx.values.astype("int32"), "piece": piece, "node": node, "dist_m": dist, "ncls": ncls, "tract_i": tract_i,
              "cand": cand, "area_m2": B.area_m2.values.astype("float32")}).to_parquet(out)
log("wrote", out, "snapped", int(ok.sum()), "of", N, "| in tract", int((tract_i >= 0).sum()), "| cand", int(cand.sum()))
