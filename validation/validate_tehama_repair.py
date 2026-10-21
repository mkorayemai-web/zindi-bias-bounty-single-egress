"""Second independent calibration of the latent-connection repairs: Tehama County CA (all 32 documented neighbourhoods have ONE ingress/egress point per the county study, Table 2).
For each repair radius (0, 25, 50, 100, 250 m) the graph is repaired exactly as in sens_nearmiss2.py, the bridge search is rerun, and the SAME matched road nodes of each documented area are re-read:
flag = >= 50% of the area's road nodes have >= 1 bridge to the arterial network; load = max dwellings behind a single link among the area's nodes.
Since every documented area truly has one way out, a faithful repair should keep these flags: retention = share of baseline flags that survive.
usage: validate_tehama_repair.py -> tables/validation_tehama_repair.csv, tables/validation_tehama_repair_summary.txt"""
import sys, re, warnings, numpy as np, pandas as pd, pyproj
from scipy.stats import spearmanr
warnings.filterwarnings('ignore', message='This pattern is interpreted as a regular expression')
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "egress"))
from common import *
from spof import *
from graphlib import sink_rooted_loads
region = "northern-ca"
G = load_graph(region, "drv"); P, nx, ny, n = G["P"], G["nx"], G["ny"], G["n"]
sink_all, art, ex, deg, tr = sinks(G, "A")
B = load_buildings(region); B, pts = snap_buildings(G, B); B = assign_tract_and_weights(region, B, pts, tr)
bn = B[(B.node >= 0) & (B.dist_m <= 500) & B.cand]
wd = np.zeros(n + 1); ws = np.zeros(n + 1); np.add.at(wd, bn.node.values, bn.w.values); np.add.at(ws, bn.node.values, 1.0)
tf = pyproj.Transformer.from_crs(CRS_M, "EPSG:4326", always_xy=True)
mx, my = (nx[P.u.values] + nx[P.v.values]) / 2, (ny[P.u.values] + ny[P.v.values]) / 2
lon, lat = tf.transform(mx, my); P = P.assign(lon=lon, lat=lat)
BOX = {"Cottonwood": (-122.45, -122.12, 40.30, 40.50), "Red Bluff": (-122.35, -122.10, 40.05, 40.30)}
def inbox(df, town):
    a, b, c, d = BOX[town]; return (df.lon >= a) & (df.lon <= b) & (df.lat >= c) & (df.lat <= d)
T = pd.read_csv(f"{REPO_ROOT}/validation/tehama_table2.csv")
areas = []
for _, r in T.iterrows():
    m = P[P.rname.fillna("").str.contains(r.name_regex, flags=re.I, regex=True) & inbox(P, r.community)]
    if len(m): areas.append((r.community, r.neighborhood, r.est_population, np.unique(np.concatenate([m.u.values, m.v.values]))))
print("matched documented areas:", len(areas))
radii = [0, 25, 50, 100, 250]; rows = []
for rad in radii:
    if rad == 0: res, eu_all, ev_all = run_graph(G, sink_all)
    else:
        eu2, ev2, info, pair = near_miss_repair(G, sink_all, deg, rad); res, eu_all, ev_all = run_graph(G, sink_all, eu2, ev2)
    (top_d, top_s), nb, topc, sub = sink_rooted_loads(n + 1, res, [wd, ws])
    for com, nbh, pop, nodes in areas:
        rows.append(dict(radius_m=rad, community=com, neighborhood=nbh, est_population=pop, n_nodes=len(nodes), share_single=float((nb[nodes] >= 1).mean()), max_load_dw=float(top_d[nodes].max())))
    print("radius", rad, "done", flush=True)
R = pd.DataFrame(rows); R["flag"] = R.share_single >= 0.5; R.to_csv(f"{OUT}/validation_tehama_repair.csv", index=False)
out = []
def line(s): print(s); out.append(s)
line(f"Tehama calibration of the latent-connection repairs: {len(areas)} documented single-ingress/egress neighbourhoods matched by road name (county study Table 2); flag = >=50% of road nodes single-route")
b0 = R[R.radius_m == 0].set_index(["community", "neighborhood"])
for rad in radii:
    s = R[R.radius_m == rad].set_index(["community", "neighborhood"]); kept = int((s.flag & b0.flag).sum()); base = int(b0.flag.sum())
    rho, p = spearmanr(s.est_population, s.max_load_dw)
    line(f"  r={rad:>3} m | flagged {int(s.flag.sum())}/{len(s)} | baseline flags retained {kept}/{base} | max load >=20 dwellings in {int((s.max_load_dw >= 20).sum())}/{len(s)} | Spearman(population, load) {rho:.2f} (p={p:.1e}) | mean share single-route {s.share_single.mean():.3f}")
open(f"{OUT}/validation_tehama_repair_summary.txt", "w").write("\n".join(out) + "\n")
