"""Finding 2 local maps: three resort clusters, census persons vs peak-weekend persons. usage: figs_resort.py -> figs/fig9_resort_clusters.png
Red = roads and homes whose only way out is the orange link (diamond); grey = other roads/homes. Panel text: dwellings, seasonal share, census persons, peak persons range (assumption q = 1.2-3.5 per seasonal unit, tables/seasonal_load_range.csv)."""
import sys, numpy as np, pandas as pd, shapely, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely import STRtree, box
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
from spof import load_graph
from figlabels import north_arrow, qa
import pyproj
from matplotlib.lines import Line2D
tf_fwd = pyproj.Transformer.from_crs(CRS_M, "EPSG:4326", always_xy=True); tf_back = pyproj.Transformer.from_crs("EPSG:4326", CRS_M, always_xy=True)
plt.rcParams.update({"font.size": 9})
CASES = [("south-central-tx", "Queen Isabella Causeway", "48061012305", "South Padre Island / Port Isabel TX"),
         ("northern-ca", "Alpine Meadows Road", "06061022014", "Alpine Meadows / Olympic Valley CA"),
         ("eastern-ok", "East 310 Road", "40041375804", "Grand Lake, Delaware County OK")]
SL = pd.read_csv(f"{OUT}/seasonal_load_range.csv", dtype={"tract": str}); ARTERIAL = {"motorway", "trunk", "primary", "secondary"}
fig, axs = plt.subplots(1, 3, figsize=(15.0, 5.6))
for ax, (region, rn, tract, label) in zip(axs, CASES):
    L = pd.read_csv(f"{OUT}/{region}_drv_A_links.csv", dtype={"tract": str}); row = L[(L.rname == rn) & (L.tract == tract)].sort_values("load_dwell", ascending=False).iloc[0]; C = int(row.child)
    S = SL[(SL.rname == rn) & (SL.tract == tract)].sort_values("load_dwell", ascending=False).iloc[0]
    G = load_graph(region, "drv"); P, geoms, nx, ny = G["P"], G["geoms"], G["nx"], G["ny"]; topc = np.load(f"{WORK}/{region}_drv_A_nodes.npz")["topc"]
    nodes = np.where(topc == C)[0]; x0, x1, y0, y1 = nx[nodes].min(), nx[nodes].max(), ny[nodes].min(), ny[nodes].max()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; half = min(max((x1 - x0), (y1 - y0)) / 2 + 350, 6000.0)
    W = box(cx - half, cy - half, cx + half, cy + half); idx = STRtree(geoms).query(W, predicate="intersects")
    for i in idx:
        u, v = int(P.u.values[i]), int(P.v.values[i]); inC = (topc[u] == C) and (topc[v] == C); link = ((topc[u] == C) != (topc[v] == C)) and (topc[u] == C or topc[v] == C); art = P.cls.values[i] in ARTERIAL
        col, lw, z = ("#2166ac", 1.6, 2) if art else (("#ff7f00", 2.8, 4) if link else (("#b2182b", 1.3, 3) if inC else ("#9a9a9a", 0.7, 1)))
        c = np.asarray(geoms[i].coords) - (cx, cy); ax.plot(c[:, 0], c[:, 1], color=col, lw=lw, zorder=z, solid_capstyle="round")
    Bd = pd.read_parquet(f"{WORK}/{region}_bldg.parquet", columns=["x", "y"]); Sn = pd.read_parquet(f"{WORK}/{region}_drv_snap.parquet", columns=["node", "cand"])
    inwin = (np.abs(Bd.x.values - cx) < half) & (np.abs(Bd.y.values - cy) < half); node = Sn.node.values; clb = (node >= 0) & (topc[np.maximum(node, 0)] == C) & Sn.cand.values
    ax.scatter(Bd.x.values[inwin & ~clb] - cx, Bd.y.values[inwin & ~clb] - cy, s=1.2, color="#d6d6d6", zorder=0)
    ax.scatter(Bd.x.values[inwin & clb] - cx, Bd.y.values[inwin & clb] - cy, s=2.5, color="#e34a33", alpha=0.75, zorder=2)
    ax.scatter([nx[C] - cx], [ny[C] - cy], marker="D", s=60, color="#ff7f00", edgecolor="k", lw=0.7, zorder=8)
    ax.set_xlim(-half, half); ax.set_ylim(-half, half); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    lon_, lat_ = tf_fwd.transform(cx, cy); qx, qy = tf_back.transform(lon_, lat_ + 0.01); th = float(np.degrees(np.arctan2(qx - cx, qy - cy))); north_arrow(ax, th); print(f"   true north is {th:+.1f} deg from map-up (grid convergence) in {region}")
    bar = 1000 if half > 2500 else 500; ax.plot([-half + 0.05 * half, -half + 0.05 * half + bar], [-half + 0.05 * half] * 2, color="k", lw=2); ax.text(-half + 0.05 * half + bar / 2, -half + 0.09 * half, f"{bar/1000:g} km", ha="center", fontsize=7)
    ax.set_title(f"{label}\n{rn}: {S.load_dwell:,.0f} dwellings, {100*S.seas_share:.0f}% seasonal tract\ncensus persons {S.load_persons:,.0f} -> peak {S.peak_low:,.0f}-{S.peak_high:,.0f}", fontsize=8.6)
    print(region, rn, "cluster nodes", len(nodes), "window half (m)", round(half))
fig.suptitle("Second homes behind one link: the census counts the residents, not the weekend (peak = census + seasonal units x q; q = 1.2-3.5 persons per seasonal unit is an assumption range)", fontsize=9, y=0.982)
hs = [Line2D([0], [0], color="#ff7f00", lw=3, label="the single link (only way out)"), Line2D([0], [0], color="#b2182b", lw=1.5, label="roads behind the link"), Line2D([0], [0], marker="o", ls="", ms=3.5, color="#e34a33", label="homes behind the link"),
      Line2D([0], [0], color="#2166ac", lw=1.6, label="arterial (scored-class) roads"), Line2D([0], [0], color="#9a9a9a", lw=1, label="other roads"), Line2D([0], [0], marker="o", ls="", ms=3.5, color="#d6d6d6", label="other homes")]
fig.legend(handles=hs, loc="lower center", ncol=6, fontsize=7.8, frameon=False, columnspacing=1.4, handlelength=1.8)
fig.tight_layout(pad=1.4, rect=(0, 0.075, 1, 0.94)); qa(fig, "fig9"); fig.savefig(f"{REPO_ROOT}/figs/fig9_resort_clusters.png", dpi=170); print("wrote fig9")
