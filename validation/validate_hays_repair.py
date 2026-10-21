"""Independent calibration of the 'latent connection' repairs with the Hays County study (Ramos & Yuan 2024, Table 1; published adjusted exits per neighbourhood).
For each repair radius r (0 = baseline, 25, 50, 100, 250 m) the SAME buildings (K nearest baseline candidates to the published centroid, K = house count) are re-read under the repaired graph.
If repairs only fix genuine digitising gaps, documented MULTI-exit neighbourhoods that were flagged single-route should become multi-route (false positives fall) while documented ONE-exit neighbourhoods should stay flagged (true positives kept).
If true positives collapse as r grows, the extra connections are mostly not real exits (fences, private drives, cul-de-sacs). usage: validate_hays_repair.py -> tables/validation_hays_repair.csv, tables/validation_hays_repair_summary.txt"""
import sys, numpy as np, pandas as pd, pyproj
from scipy.spatial import cKDTree
from scipy.stats import mannwhitneyu, fisher_exact
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "egress"))
from common import *
region = "south-central-tx"
H = pd.read_csv(f"{REPO_ROOT}/ext/hays_table1.csv"); H.columns = ["rank", "name", "houses", "exits", "ratio", "fire_level", "lon", "lat"]
H["lon"] = H.lon.astype(str).str.replace("\u2212", "-").astype(float); H["lat"] = H.lat.astype(float)
tf = pyproj.Transformer.from_crs("EPSG:4326", CRS_M, always_xy=True); H["x"], H["y"] = tf.transform(H.lon.values, H.lat.values)
pad = 6000; x0, x1, y0, y1 = H.x.min() - pad, H.x.max() + pad, H.y.min() - pad, H.y.max() + pad
B = pd.read_parquet(f"{WORK}/{region}_bldg.parquet", columns=["bidx", "x", "y"], filters=[("x", ">=", x0), ("x", "<=", x1), ("y", ">=", y0), ("y", "<=", y1)])
S = pd.read_parquet(f"{WORK}/{region}_drv_snap.parquet", columns=["bidx", "cand"])
R0 = pd.read_parquet(f"{WORK}/{region}_drv_A_bres.parquet", columns=["bidx", "egress"]).rename(columns={"egress": "eg_0"})
D = B.merge(S, on="bidx").merge(R0, on="bidx")
variants = {25: pd.read_parquet(f"{WORK}/{region}_drv_A_r25_bres.parquet", columns=["bidx", "egress"])}
for r in (50, 100, 250): variants[r] = pd.read_parquet(f"{WORK}/{region}_nm{r}_bld.parquet", columns=["bidx", "egress"])
for r, v in variants.items(): D = D.merge(v.rename(columns={"egress": f"eg_{r}"}), on="bidx", how="left")
D = D[D.cand & (D.eg_0 >= 0)].reset_index(drop=True)
tree = cKDTree(D[["x", "y"]].values); radii = [0, 25, 50, 100, 250]
rows = []
for _, h in H.iterrows():
    K = int(min(h.houses, len(D))); d, ix = tree.query([h.x, h.y], k=K); ix = np.atleast_1d(ix)
    row = dict(name=h["name"], houses=h.houses, exits=h.exits)
    for r in radii: row[f"share_single_{r}"] = float((D[f"eg_{r}"].values[ix] == 1).mean())
    rows.append(row)
V = pd.DataFrame(rows); V["one_exit"] = V.exits == 1; V.to_csv(f"{OUT}/validation_hays_repair.csv", index=False)
out = []
def line(s): print(s); out.append(s)
line(f"Hays calibration of the latent-connection repairs: {len(V)} neighbourhoods ({int(V.one_exit.sum())} published one-exit, {int((~V.one_exit).sum())} multi-exit); flag = share of the neighbourhood's buildings with a single route >= 0.5")
MET = []
line("repair radius | one-exit flagged (true positives) | multi-exit flagged (false positives) | AUC (share_single vs published one-exit) | mean share_single one-exit / multi-exit")
for r in radii:
    c = f"share_single_{r}"; fl = V[c] >= 0.5; tp = int((V.one_exit & fl).sum()); fp = int((~V.one_exit & fl).sum())
    u = mannwhitneyu(V[c][V.one_exit], V[c][~V.one_exit], alternative="greater"); auc = u.statistic / (V.one_exit.sum() * (~V.one_exit).sum())
    MET.append(dict(radius_m=r, true_positives=tp, n_one_exit=int(V.one_exit.sum()), false_positives=fp, n_multi_exit=int((~V.one_exit).sum()), auc=auc))
    line(f"  r={r:>3} m | {tp}/{int(V.one_exit.sum())} | {fp}/{int((~V.one_exit).sum())} | AUC {auc:.3f} (p={u.pvalue:.1e}) | {V[c][V.one_exit].mean():.3f} / {V[c][~V.one_exit].mean():.3f}")
g = V[V.name.str.upper() == "GOLDENWOOD"]
if len(g): line("GOLDENWOOD (published 3 exits): share single-route by radius " + ", ".join(f"r{r}={g[f'share_single_{r}'].iloc[0]:.2f}" for r in radii))
fp0 = V[(~V.one_exit) & (V.share_single_0 >= 0.5)]
for _, f in fp0.iterrows(): line(f"  baseline false positive {f['name']} (exits {int(f.exits)}): " + ", ".join(f"r{r}={f[f'share_single_{r}']:.2f}" for r in radii))
drop = V[V.one_exit & (V.share_single_0 >= 0.5) & (V.share_single_250 < 0.5)]
line(f"documented one-exit neighbourhoods flagged at baseline that fall below 0.5 at r=250 m: {len(drop)}: " + ", ".join(drop['name'].tolist()[:12]))
pd.DataFrame(MET).to_csv(f"{OUT}/validation_hays_repair_metrics.csv", index=False)
open(f"{OUT}/validation_hays_repair_summary.txt", "w").write("\n".join(out) + "\n")
