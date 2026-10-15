"""Ranked 'pinhole' list: single-link clusters whose S30 status disappears when a dead-end tip is connected to the nearest UNCONNECTED road piece within r metres.
usage: pinhole_list.py REGION [r=50]    needs work/<region>_nm0_bld.parquet and work/<region>_nm<r>_bld.parquet / _pairs.parquet (sens_nearmiss2.py), work/<region>_drv_A_nodes.npz, tables/<region>_drv_A_links.csv
Per baseline choke cluster (top-level single link, id = child node): load (dwellings behind it), dwellings that stop being S30 after the repair ('relieved'), and the SHORTEST external gap
(dead-end tip inside the cluster -> piece outside the cluster) in metres. 'External' = the target piece's endpoints do not belong to the same cluster.
Output: tables/pinholes_<region>_r<r>.csv. CANDIDATES for verification, not claims of missing roads."""
import sys, numpy as np, pandas as pd
from spof import load_graph
from common import *
region = sys.argv[1]; r = int(sys.argv[2]) if len(sys.argv) > 2 else 50
T = pd.read_parquet(f"{WORK}/{region}_tracts.parquet"); HU = T.housing_units.fillna(0).values.astype("float64")
S = pd.read_parquet(f"{WORK}/{region}_drv_snap.parquet", columns=["bidx", "tract_i", "node", "cand"])
ti = S.tract_i.values.astype("int64"); cand = S.cand.values & (ti >= 0)
nc = np.bincount(ti[cand], minlength=len(T)).astype("float64"); dw = np.zeros(len(S)); dw[cand] = HU[ti[cand]] / nc[ti[cand]]
b0 = pd.read_parquet(f"{WORK}/{region}_nm0_bld.parquet"); b1 = pd.read_parquet(f"{WORK}/{region}_nm{r}_bld.parquet")
assert (b0.bidx.values == S.bidx.values).all() and (b1.bidx.values == S.bidx.values).all()
s0 = (b0.egress.values == 1) & (b0.top_load_d.values >= 30) & cand
s1 = (b1.egress.values == 1) & (b1.top_load_d.values >= 30) & cand
topc = np.load(f"{WORK}/{region}_drv_A_nodes.npz")["topc"]
node = S.node.values.astype("int64"); ok = node >= 0
cl = np.where(ok, topc[np.maximum(node, 0)], -1)
D = pd.DataFrame({"cluster": cl, "dw": dw, "s0": s0, "flip": s0 & ~s1})
D = D[D.s0 & (D.cluster >= 0)]
agg = D.groupby("cluster").apply(lambda g: pd.Series({"load_dw": g.dw.sum(), "relieved_dw": g.dw[g.flip].sum()}), include_groups=False).reset_index()
G = load_graph(region, "drv"); Pu, Pv = G["P"].u.values, G["P"].v.values
pr = pd.read_parquet(f"{WORK}/{region}_nm{r}_pairs.parquet")
pr["c_d"] = topc[pr.d.values]; pr["c_u"] = topc[Pu[pr.p.values]]; pr["c_v"] = topc[Pv[pr.p.values]]
# a repair pair joins the dead-end tip d to piece p. For a cluster C it is EXTERNAL if C is among {cluster(d), cluster(p.u), cluster(p.v)} and at least one of the three ids differs from C
# (-1 = not inside any single-link cluster); this covers both directions (tip inside C reaching out, or an outside tip reaching a piece inside C).
ids = np.stack([pr.c_d.values, pr.c_u.values, pr.c_v.values], 1); parts = []
for k in range(3):
    c = ids[:, k]; m = (c >= 0) & (ids != c[:, None]).any(axis=1)
    parts.append(pd.DataFrame({"cluster": c[m], "dist": pr.dist.values[m], "x": pr.x.values[m], "y": pr.y.values[m]}))
ext = pd.concat(parts)
g = ext.groupby("cluster").agg(min_gap_m=("dist", "min"), n_ext_pairs=("dist", "size"), gx=("x", "first"), gy=("y", "first")).reset_index()
out = agg.merge(g, on="cluster", how="left")
L = pd.read_csv(f"{OUT}/{region}_drv_A_links.csv", dtype={"tract": str})[["child", "rname", "cls", "tract", "place", "load_dwell", "load_persons", "lon", "lat"]].rename(columns={"child": "cluster"})
out = out.merge(L, on="cluster", how="inner")
out["share_relieved"] = out.relieved_dw / out.load_dw
out["region"] = region; out["radius_m"] = r
out = out.sort_values("relieved_dw", ascending=False)
out.to_csv(f"{OUT}/pinholes_{region}_r{r}.csv", index=False)
big = out[out.load_dw >= 100]
print(f"{region} r={r} m: clusters>=100 dw: {len(big)} | with >=50% relieved: {(big.share_relieved >= 0.5).sum()} ({big.relieved_dw[big.share_relieved >= 0.5].sum():,.0f} dw) | total relieved (all clusters in links table): {out.relieved_dw.sum():,.0f} of {out.load_dw.sum():,.0f}")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 28)
print(out.head(8)[["place", "rname", "tract", "load_dw", "relieved_dw", "share_relieved", "min_gap_m", "n_ext_pairs"]].round(2).to_string(index=False))
