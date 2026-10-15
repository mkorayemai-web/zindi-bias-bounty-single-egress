"""Validation against an independent official list: Tehama County Safety, Secondary Access, Community Planning & Evacuation Planning Study
(Tehama County Transportation Commission, adopted June 2024), Table 2 'Communities/Neighborhoods with 1 Ingress/Egress Point' (32 rows, transcribed in tehama_table2.csv).
Method: match each documented neighborhood name to Overture road names inside the stated town's box (Cottonwood or Red Bluff), then ask whether the road graph
classifies those road nodes as single-route (>=1 bridge between the node and the arterial network). Control = same test for random same-size sets of
named residential roads in the same town boxes (placebo), seeded.
usage: validate_tehama.py"""
import sys, re, warnings, numpy as np, pandas as pd, pyproj
from scipy.stats import spearmanr
warnings.filterwarnings('ignore', message='This pattern is interpreted as a regular expression')
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "egress"))
from common import *
from spof import load_graph
rng = np.random.default_rng(SEED)
G = load_graph("northern-ca", "drv")
P, nx, ny = G["P"], G["nx"], G["ny"]
Z = np.load(f"{WORK}/northern-ca_drv_A_nodes.npz")
nb, reached, topc, top_eq = Z["nb"], Z["reached"], Z["topc"], Z["top_eq"]
tf = pyproj.Transformer.from_crs(CRS_M, "EPSG:4326", always_xy=True)
mx, my = (nx[P.u.values] + nx[P.v.values]) / 2, (ny[P.u.values] + ny[P.v.values]) / 2
lon, lat = tf.transform(mx, my)
P = P.assign(lon=lon, lat=lat)
BOX = {"Cottonwood": (-122.45, -122.12, 40.30, 40.50), "Red Bluff": (-122.35, -122.10, 40.05, 40.30)}
def inbox(df, town):
    a, b, c, d = BOX[town]
    return (df.lon >= a) & (df.lon <= b) & (df.lat >= c) & (df.lat <= d)
T = pd.read_csv(f"{LANE}/validation/tehama_table2.csv")
rows = []
for _, r in T.iterrows():
    m = P[P.rname.fillna("").str.contains(r.name_regex, flags=re.I, regex=True) & inbox(P, r.community)]
    if len(m) == 0:
        rows.append(dict(**r.to_dict(), matched_pieces=0)); continue
    nodes = np.unique(np.concatenate([m.u.values, m.v.values]))
    share = float((nb[nodes] >= 1).mean())
    top = top_eq[nodes].max()
    rows.append(dict(**r.to_dict(), matched_pieces=len(m), matched_nodes=len(nodes), share_nodes_single_route=share, max_cluster_load_dwell=float(top),
                     named_roads=";".join(sorted(m.rname.dropna().unique())[:4])))
R = pd.DataFrame(rows)
R["flag"] = R.share_nodes_single_route >= 0.5
matched = R[R.matched_pieces > 0]
print(R[["community", "neighborhood", "est_population", "matched_pieces", "share_nodes_single_route", "max_cluster_load_dwell", "flag", "named_roads"]].round(2).to_string())
print(f"\nmatched {len(matched)}/{len(R)} neighborhoods by road name; flagged single-route (>=50% of road nodes with a bridge to the arterial network): {int(matched.flag.sum())}/{len(matched)}")
# placebo: random sets of named residential/tertiary/unclassified roads in the same boxes, same number of matched pieces per set
base_rows = []
for town in BOX:
    pool = P[inbox(P, town) & P.rname.notna() & P.cls.isin(["residential", "unclassified", "tertiary"])]
    base_rows.append(pool)
pool_all = pd.concat(base_rows)
pool_names = pool_all.groupby("rname").agg(n=("u", "size")).reset_index()
shares = []
for k in range(2000):
    nm = rng.choice(pool_names.rname.values, size=len(matched), replace=False)
    ss = []
    for z in nm:
        m = pool_all[pool_all.rname == z]
        nodes = np.unique(np.concatenate([m.u.values, m.v.values]))
        ss.append((nb[nodes] >= 1).mean() >= 0.5)
    shares.append(np.mean(ss))
shares = np.array(shares)
obs = matched.flag.mean()
print(f"placebo (random named roads in same boxes): mean flagged share {shares.mean():.3f} (95% range {np.percentile(shares,2.5):.3f}-{np.percentile(shares,97.5):.3f}); observed {obs:.3f}")
R.to_csv(f"{OUT}/validation_tehama.csv", index=False)
with open(f"{OUT}/validation_tehama_summary.txt", "w") as f:
    f.write(f"matched {len(matched)}/{len(R)}; flagged {int(matched.flag.sum())}/{len(matched)} = {obs:.3f}; placebo mean {shares.mean():.3f} (95% {np.percentile(shares,2.5):.3f}-{np.percentile(shares,97.5):.3f})\n")

# ---- sharper tests: dose-response and large-cluster base rates --------------------------------------------------------------------
M = R[R.matched_pieces > 0].copy()
rho, p = spearmanr(M.est_population, M.max_cluster_load_dwell)
lines = [f"Spearman(documented est. population, graph cluster load in dwellings) = {rho:.2f} (p={p:.2g}, n={len(M)})"]
pool = pd.concat([P[inbox(P, t) & P.rname.notna() & P.cls.isin(["residential", "unclassified", "tertiary"])] for t in BOX])
names = pool.groupby("rname").size(); names = names[names >= 3].index.values
vals = []
for nm in names:
    m = pool[pool.rname == nm]; nodes = np.unique(np.concatenate([m.u.values, m.v.values])); vals.append((top_eq[nodes].max(), (nb[nodes] >= 1).mean()))
vals = np.array(vals)
for thr in (20, 30, 50):
    lines.append(f"max cluster load >= {thr} dwellings: documented {(M.max_cluster_load_dwell>=thr).mean():.3f} ({int((M.max_cluster_load_dwell>=thr).sum())}/{len(M)}) vs base rate {(vals[:,0]>=thr).mean():.3f} over {len(names)} named roads (>=3 pieces) in the same two town boxes")
lines.append(f"share of road nodes single-route >= 0.5: documented {M.flag.mean():.3f} vs base rate {(vals[:,1]>=0.5).mean():.3f}")
print("\n".join(lines))
with open(f"{OUT}/validation_tehama_summary.txt", "a") as f:
    f.write("\n".join(lines) + "\n")
