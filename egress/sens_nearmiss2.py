"""Latent-connection sweep ('pinholes'): how much single-link exposure disappears if dead-end road tips were connected to the nearest UNCONNECTED road piece within r metres?
usage: sens_nearmiss2.py REGION [r1 r2 ...]   (default radii 50 100 250; sink A, scored classes 'drv'; the 5/10/25 m radii are in sens_nearmiss.py)
Outputs: tables/sens_nearmiss2_<region>.csv (one row per radius: S30 / S100 shares, #dead ends, #repairs, median repair distance)
         work/<region>_nm<r>_bld.parquet  (bidx, egress, top_load_d under the repaired graph) and work/<region>_nm<r>_pairs.parquet (dead-end node x,y [EPSG 5070 m], repair distance)
Interpretation: r<=25 m = digitising gaps; larger r = an UPPER BOUND on latent second connections (private drives / fences / terrain are not excluded)."""
import sys, time, numpy as np, pandas as pd
from spof import *
region = sys.argv[1]
radii = [int(a) for a in sys.argv[2:]] or [50, 100, 250]
t0 = time.time()
G = load_graph(region, "drv")
sink_all, art, ex, deg, tr = sinks(G, "A")
B = load_buildings(region)
B, pts = snap_buildings(G, B)
B = assign_tract_and_weights(region, B, pts, tr)
rows = []
res, eu_all, ev_all = run_graph(G, sink_all)
B0, sub, topc = egress_classes(G, B, res, eu_all, ev_all)
s = summarize(B0, "baseline"); s.update(dict(r_m=0)); rows.append(s)
print(s, f"{time.time()-t0:.0f}s", flush=True)
for r in radii:
    eu2, ev2, info, pair = near_miss_repair(G, sink_all, deg, r)
    res2, eu_all2, ev_all2 = run_graph(G, sink_all, eu2, ev2)
    B2, _, _ = egress_classes(G, B, res2, eu_all2, ev_all2)
    s = summarize(B2, f"repair_{r}m"); s.update(info); s["r_m"] = r
    s["median_repair_dist_m"] = float(pair.dist.median()) if len(pair) else np.nan
    rows.append(s)
    B2[["bidx", "egress", "top_load_d"]].to_parquet(f"{WORK}/{region}_nm{r}_bld.parquet")
    if len(pair):
        pp = pair.copy(); pp["x"] = G["nx"][pp.d.values]; pp["y"] = G["ny"][pp.d.values]; pp[["d", "p", "dist", "x", "y"]].to_parquet(f"{WORK}/{region}_nm{r}_pairs.parquet")
    print(s, f"{time.time()-t0:.0f}s", flush=True)
B0[["bidx", "egress", "top_load_d"]].to_parquet(f"{WORK}/{region}_nm0_bld.parquet")
R = pd.DataFrame(rows); R.to_csv(f"{OUT}/sens_nearmiss2_{region}.csv", index=False)
print(R.round(4).to_string())
