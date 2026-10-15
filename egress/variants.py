"""Stage 2: SPOF (single point of failure) egress analysis for one configuration, using the cached snap (pipeline.py).
usage: variants.py REGION CSET SINK [--repair R] [--minload L]
   CSET: drv | drvplus     SINK: A (motorway,trunk,primary,secondary + region exits) | B (motorway,trunk + region exits)
   --repair R : snap dead ends within R metres of an unconnected road piece (piece split) before the analysis (digitising-gap repair)
Weighting schemes (all per census tract, ACS B25001 housing units HU and 2020 population POP spread over residential-candidate buildings):
   eq   : each candidate building = HU/n dwellings           (headline)
   area : candidate building = HU * footprint/sum(footprint)  (sensitivity: apartments carry more dwellings)
   str  : each candidate building = 1 structure              (no ACS)
Outputs (tag = region_cset_sink[_rR]): work/<tag>_tract.parquet, work/<tag>_nodes.npz, work/<tag>_bres.parquet, tables/<tag>_links.csv, tables/<tag>_summary.csv"""
import sys, time, numpy as np, pandas as pd, shapely, pyproj
from shapely import STRtree
from common import *
from spof import load_graph, sinks, near_miss_repair, run_graph
from graphlib import sink_rooted_loads
from placenames import name_points

region, cset, sinkv = sys.argv[1], sys.argv[2], sys.argv[3]
repair = float(sys.argv[sys.argv.index("--repair") + 1]) if "--repair" in sys.argv else None
minload = float(sys.argv[sys.argv.index("--minload") + 1]) if "--minload" in sys.argv else 100.0
tag = f"{region}_{cset}_{sinkv}" + (f"_r{int(repair)}" if repair else "")
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.0f}s]", *a, flush=True)

G = load_graph(region, cset)
P, n = G["P"], G["n"]
sink_all, art, ex, deg, tr = sinks(G, sinkv)
eu, ev = P.u.values, P.v.values
rep_info = {}
if repair:
    eu, ev, rep_info, _ = near_miss_repair(G, sink_all, deg, repair)
    log("repair", rep_info)
res, eu_all, ev_all = run_graph(G, sink_all, eu, ev)
n_real = len(eu)
res["is_bridge"][n_real:] = False          # virtual sink edges are not roads
reached = res["disc"] >= 0
log("DFS reached", int(reached.sum()) - 1, "of", n, "| real bridges", int(res["is_bridge"][:n_real].sum()))

T = pd.read_parquet(f"{WORK}/{region}_tracts.parquet")
S = pd.read_parquet(f"{WORK}/{region}_{cset}_snap.parquet")
nT = len(T); N = len(S)
HU = T.housing_units.fillna(0).values.astype("float64"); POP_RAW = T.pop_total.fillna(0).values.astype("float64")
GQ = (HU <= 0) | (POP_RAW > 6 * HU)                 # group-quarters-dominated tracts (prisons, dorms, bases): excluded from PERSON weights only
POP = np.where(GQ, 0.0, POP_RAW)
ti = S.tract_i.values.astype("int64"); ok_t = ti >= 0
cand = S.cand.values & ok_t
near = cand & (S.node.values >= 0) & (S.dist_m.values <= 500)
nc = np.bincount(ti[cand], minlength=nT).astype("float64")
asum = np.bincount(ti[cand], weights=S.area_m2.values[cand].astype("float64"), minlength=nT)
tic = ti[cand]
a_eq = np.zeros(N); a_eq[cand] = 1.0 / nc[tic]
a_ar = np.zeros(N); a_ar[cand] = S.area_m2.values[cand] / asum[tic]
dw_eq = HU[np.maximum(ti, 0)] * a_eq; dw_ar = HU[np.maximum(ti, 0)] * a_ar; pe_eq = POP[np.maximum(ti, 0)] * a_eq; pe_ar = POP[np.maximum(ti, 0)] * a_ar
st_one = cand.astype("float64")
nodes = S.node.values.astype("int64")
nn = nodes[near]
W = [np.bincount(nn, weights=w[near], minlength=n + 1) for w in (dw_eq, dw_ar, st_one, pe_eq)]
top, nb, topc, sub = sink_rooted_loads(n + 1, res, W)
log("loads done")
# single-route run length (m of bridging edges on the path to the first 2-edge-connected node) and number of physical bridge STRUCTURES that are single points of failure
orderl = res["order"].tolist(); parl = res["parent"].tolist(); pel = res["parent_edge"].tolist(); isb = res["is_bridge"]
lenm = P.len_m.values; sbr = P.is_bridge.fillna(False).values.astype(bool)
run_m = np.zeros(n + 1, dtype="float32"); nbs = np.zeros(n + 1, dtype="int16")
for u in (orderl[1:] if not repair else []):     # (edge arrays are rebuilt in repair mode, so edge attributes cannot be indexed)
    p = parl[u]; e = pel[u]
    if e < n_real and isb[e]:
        run_m[u] = run_m[p] + lenm[e]; nbs[u] = nbs[p] + (1 if sbr[e] else 0)
    else:
        run_m[u] = run_m[p]; nbs[u] = nbs[p]
nd = np.where(near, nodes, 0)
egress = np.full(N, -1, dtype="int8")
r = reached[nd]
egress[near & ~r] = 0
egress[near & r & (nb[nd] >= 1)] = 1
egress[near & r & (nb[nd] == 0)] = 2
tl = [np.where(near, t[nd], 0.0).astype("float32") for t in top]
pd.DataFrame({"bidx": S.bidx.values, "tract_i": S.tract_i.values, "egress": egress, "nb": np.where(near, nb[nd], -1).astype("int16"),
              "top_eq": tl[0], "top_ar": tl[1], "top_str": tl[2]}).to_parquet(f"{WORK}/{tag}_bres.parquet")
np.savez_compressed(f"{WORK}/{tag}_nodes.npz", nb=nb.astype("int16"), reached=reached, topc=topc, top_eq=top[0].astype("float32"), top_ar=top[1].astype("float32"),
                    top_str=top[2].astype("float32"), sub_eq=sub[0].astype("float32"), top_pers=top[3].astype("float32"), sub_pers=sub[3].astype("float32"), run_m=run_m, nbs=nbs)

# ---------------- tract table ------------------------------------------------------------------------------------------------------------
def bc(mask, w):
    return np.bincount(ti[mask], weights=w[mask], minlength=nT)
out = pd.DataFrame(index=T.GEOID.values)
out["HU"] = HU; out["POP"] = POP_RAW; out["POP_eff"] = POP; out["gq"] = GQ; out["n_cand"] = nc
dist = S.dist_m.values
for d in (100, 250, 500):
    out[f"off{d}"] = bc(cand & ~(dist <= d), dw_eq) / np.maximum(bc(cand, dw_eq), 1e-9)
out["eq_r1k"] = bc(near & (egress == 1) & (run_m[nd] >= 1000), dw_eq) / np.maximum(bc(near, dw_eq), 1e-9)
out["eq_r5k"] = bc(near & (egress == 1) & (run_m[nd] >= 5000), dw_eq) / np.maximum(bc(near, dw_eq), 1e-9)
out["eq_bridge"] = bc(near & (egress == 1) & (nbs[nd] >= 1), dw_eq) / np.maximum(bc(near, dw_eq), 1e-9)
out["eq_s30_bridge"] = bc(near & (egress == 1) & (nbs[nd] >= 1) & (tl[0] >= 30), dw_eq) / np.maximum(bc(near, dw_eq), 1e-9)
out["off250_str"] = bc(cand & ~(dist <= 250), st_one) / np.maximum(bc(cand, st_one), 1e-9)
THR = (10, 30, 60, 100, 300, 1000)
for sch, w_d, w_p, tload in [("eq", dw_eq, pe_eq, tl[0]), ("ar", dw_ar, pe_ar, tl[1]), ("str", st_one, None, tl[2])]:
    den = bc(near, w_d)
    out[f"{sch}_den"] = den
    out[f"{sch}_isl"] = bc(near & (egress == 0), w_d) / np.maximum(den, 1e-9)
    out[f"{sch}_spof"] = bc(near & (egress == 1), w_d) / np.maximum(den, 1e-9)
    for t in THR:
        out[f"{sch}_s{t}"] = bc(near & (egress == 1) & (tload >= t), w_d) / np.maximum(den, 1e-9)
    if w_p is not None:
        denp = bc(near, w_p)
        out[f"{sch}_pden"] = denp
        out[f"{sch}_pspof"] = bc(near & (egress == 1), w_p) / np.maximum(denp, 1e-9)
        for t in THR:
            out[f"{sch}_ps{t}"] = bc(near & (egress == 1) & (tload >= t), w_p) / np.maximum(denp, 1e-9)
            out[f"{sch}_nps{t}"] = bc(near & (egress == 1) & (tload >= t), w_p)    # persons (absolute)
            out[f"{sch}_nds{t}"] = bc(near & (egress == 1) & (tload >= t), w_d)    # dwellings (absolute)
out.to_parquet(f"{WORK}/{tag}_tract.parquet")

# ---------------- region summary ---------------------------------------------------------------------------------------------------------
rows = []
for sch in ("eq", "ar", "str"):
    den = out[f"{sch}_den"].sum()
    row = dict(tag=tag, scheme=sch, den=den, isl=(out[f"{sch}_isl"] * out[f"{sch}_den"]).sum() / den, spof=(out[f"{sch}_spof"] * out[f"{sch}_den"]).sum() / den)
    for t in THR:
        row[f"s{t}"] = (out[f"{sch}_s{t}"] * out[f"{sch}_den"]).sum() / den
        if sch != "str":
            row[f"persons_s{t}"] = out[f"{sch}_nps{t}"].sum(); row[f"dwell_s{t}"] = out[f"{sch}_nds{t}"].sum()
    row.update({f"rep_{k}": v for k, v in rep_info.items()})
    rows.append(row)
SM = pd.DataFrame(rows); SM.to_csv(f"{OUT}/{tag}_summary.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(SM.round(4).to_string())

# ---------------- named choke links (top-level bridges only) --------------------------------------------------------------------------------
pe = res["parent_edge"]
cc = np.where((topc >= 0) & (topc == np.arange(n + 1)))[0]
cc = cc[(pe[cc] >= 0) & (pe[cc] < len(P))]
cc = cc[sub[0][cc] >= minload]
if repair:
    cc = cc[pe[cc] < len(P)]
L = pd.DataFrame({"child": cc, "edge": pe[cc], "load_dwell": sub[0][cc], "load_struct": sub[2][cc], "load_persons": sub[3][cc]})
# note: with --repair the piece array is rebuilt, so only the unrepaired run produces the name table
if not repair:
    L["cls"] = P.cls.values[L.edge]; L["rname"] = P.rname.values[L.edge]; L["rref"] = P.rref.values[L.edge]; L["len_m"] = P.len_m.values[L.edge]
    L["named"] = P.named.values[L.edge]; L["upd_year"] = P.upd_year.values[L.edge]
    x, y = G["nx"][L.child.values], G["ny"][L.child.values]
    tf = pyproj.Transformer.from_crs(CRS_M, "EPSG:4326", always_xy=True)
    L["lon"], L["lat"] = tf.transform(x, y)
    a, b = STRtree(tr.geometry.values).query(shapely.points(x, y), predicate="intersects")
    tmp = pd.DataFrame({"i": a, "t": b}).drop_duplicates("i"); L["tract"] = None; L.loc[tmp.i.values, "tract"] = tr.GEOID.values[tmp.t.values]
    L["place"] = name_points(region, x, y, radius=2000) if len(L) else []
    L = L.sort_values("load_dwell", ascending=False)
    L.to_csv(f"{OUT}/{tag}_links.csv", index=False)
    log("links", len(L))
log("done")
