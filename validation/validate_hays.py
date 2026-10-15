"""Independent validation #2 (Texas): Hays County, TX wildfire-evacuation study.
Source: Ramos, C. & Yuan, Y. (2024) 'Neighborhood-Scale Wildfire Evacuation Vulnerability in Hays County, TX', Geographies 4(3):481-499,
doi:10.3390/geographies4030026 (CC BY 4.0). Table 1 = 57 WUI neighbourhoods with >200 houses per community exit (house count, adjusted exits, egress ratio,
fire-risk level, lon/lat). Transcribed to ext/hays_table1.csv (retrieved 2026-10-14).
Test: the paper identifies neighbourhoods by NG9-1-1 neighbourhood names + address points; we know nothing of it. For each neighbourhood we take the K nearest
Overture residential-candidate buildings to its published centroid (K = published house count) and read the graph classification of those buildings
(work/south-central-tx_drv_A_bres.parquet from variants.py: egress 1 = single route to the arterial network, top_eq = ACS-weighted dwellings behind the worst
single link). Placebo: same K drawn around random candidate buildings of Hays County (seeded), so density/rurality is matched by construction.
Outputs tables/validation_hays.csv and tables/validation_hays_summary.txt.   usage: validate_hays.py"""
import sys, numpy as np, pandas as pd, pyproj
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "egress"))
from common import *

rng = np.random.default_rng(SEED)
region = "south-central-tx"
H = pd.read_csv(f"{LANE}/ext/hays_table1.csv")
H.columns = ["rank", "name", "houses", "exits", "ratio", "fire_level", "lon", "lat"]
H["lon"] = H.lon.astype(str).str.replace("\u2212", "-").astype(float); H["lat"] = H.lat.astype(float)
tf = pyproj.Transformer.from_crs("EPSG:4326", CRS_M, always_xy=True)
H["x"], H["y"] = tf.transform(H.lon.values, H.lat.values)
pad = 6000
x0, x1, y0, y1 = H.x.min() - pad, H.x.max() + pad, H.y.min() - pad, H.y.max() + pad
B = pd.read_parquet(f"{WORK}/{region}_bldg.parquet", columns=["bidx", "x", "y"], filters=[("x", ">=", x0), ("x", "<=", x1), ("y", ">=", y0), ("y", "<=", y1)])
S = pd.read_parquet(f"{WORK}/{region}_drv_snap.parquet", columns=["bidx", "cand", "tract_i", "dist_m"])
R = pd.read_parquet(f"{WORK}/{region}_drv_A_bres.parquet", columns=["bidx", "egress", "nb", "top_eq"])
T = pd.read_parquet(f"{WORK}/{region}_tracts.parquet")
D = B.merge(S, on="bidx").merge(R, on="bidx")
D = D[D.cand & (D.egress >= 0)].reset_index(drop=True)          # candidate residential buildings within 500 m of the drivable graph (as in the headline)
D["geoid"] = T.GEOID.values[D.tract_i.values]
print("candidate buildings in the Hays window:", len(D))
tree = cKDTree(D[["x", "y"]].values)
egress = D.egress.values; top = D.top_eq.values; single = (egress == 1)

def summarize(cx, cy, K):
    K = int(min(K, len(D)))
    d, ix = tree.query([cx, cy], k=K)
    ix = np.atleast_1d(ix)
    s = single[ix]
    return dict(share_single=float(s.mean()), share_s30=float((s & (top[ix] >= 30)).mean()), load_med=float(np.median(top[ix][s])) if s.any() else 0.0,
                load_p90=float(np.percentile(top[ix][s], 90)) if s.any() else 0.0, radius_m=float(d.max()))

rows = []
for _, r in H.iterrows():
    rows.append(dict(rank=r["rank"], name=r["name"], houses=r.houses, exits=r.exits, ratio=r.ratio, fire_level=r.fire_level, **summarize(r.x, r.y, r.houses)))
V = pd.DataFrame(rows)
V["flag_single"] = V.share_single >= 0.5
V["flag_s30"] = V.share_s30 >= 0.5
# placebo: random centres among candidate buildings inside Hays County tracts; K drawn from the empirical house counts
hays = np.where(D.geoid.str.startswith("48209").values)[0]
NPL = 3000
pl = []
for k in range(NPL):
    i = rng.choice(hays); K = rng.choice(H.houses.values)
    pl.append(summarize(D.x.values[i], D.y.values[i], K))
PL = pd.DataFrame(pl)
out = []
def line(s):
    print(s); out.append(s)
from scipy.stats import fisher_exact, mannwhitneyu, binom
line(f"Hays County validation: {len(V)} neighbourhoods from Ramos & Yuan 2024 Table 1 (CC BY 4.0); published 'adjusted exits' = independent label (NG9-1-1 neighbourhood roads vs non-neighbourhood roads).")
V["one_exit"] = V.exits == 1
tp = int((V.one_exit & V.flag_single).sum()); fn = int((V.one_exit & ~V.flag_single).sum()); fp = int((~V.one_exit & V.flag_single).sum()); tn = int((~V.one_exit & ~V.flag_single).sum())
orr, pf = fisher_exact([[tp, fn], [fp, tn]], alternative="greater")
line(f"2x2 (rows: published one-exit / multi-exit; cols: graph flags single-route share>=0.5 yes/no): [[{tp},{fn}],[{fp},{tn}]]  sensitivity {tp/(tp+fn):.3f}  specificity {tn/(tn+fp):.3f}  PPV {tp/max(tp+fp,1):.3f}  Fisher exact p={pf:.2e}")
u = mannwhitneyu(V.share_single[V.one_exit], V.share_single[~V.one_exit], alternative="greater")
auc = u.statistic / (V.one_exit.sum() * (~V.one_exit).sum())
line(f"threshold-free: AUC of graph share_single for 'published one-exit' = {auc:.3f} (Mann-Whitney p={u.pvalue:.2e}; n={int(V.one_exit.sum())} vs {int((~V.one_exit).sum())})")
base = (PL.share_single >= 0.5).mean()
line(f"base rate: {base:.3f} of random Hays County neighbourhoods (same K distribution, n={NPL}) are flagged single-route by the graph; one-exit neighbourhoods flagged {tp/(tp+fn):.3f} = {tp/(tp+fn)/base:.1f}x the base rate; binomial p(>= {tp}/{tp+fn} | p={base:.3f}) = {binom.sf(tp-1, tp+fn, base):.2e}")
for e, g in V.groupby(V.exits.clip(upper=3)):
    line(f"  adjusted exits {'>=3' if e == 3 else int(e)}: n={len(g)}  mean graph share single-route {g.share_single.mean():.3f}  flagged {g.flag_single.mean():.3f}  S30-flagged {g.flag_s30.mean():.3f}  median graph load {g.load_med.median():.0f} dwellings (published median houses {g.houses.median():.0f})")
rho0, p0 = spearmanr(V.exits, V.share_single); line(f"Spearman(published adjusted exits, graph share single-route) = {rho0:.2f} (p={p0:.2g}, n={len(V)})")
o = V[V.one_exit]
rho2, p2 = spearmanr(o.houses, o.load_med); line(f"among one-exit neighbourhoods: Spearman(published house count, graph dwellings behind the worst single link) = {rho2:.2f} (p={p2:.2g}, n={len(o)}); median ratio graph/published = {(o.load_med/o.houses).median():.2f}")
V.to_csv(f"{OUT}/validation_hays.csv", index=False)
open(f"{OUT}/validation_hays_summary.txt", "w").write("\n".join(out) + "\n")
print(V.sort_values("houses", ascending=False).head(12)[["name", "houses", "exits", "ratio", "share_single", "load_med", "radius_m"]].round(2).to_string(index=False))
