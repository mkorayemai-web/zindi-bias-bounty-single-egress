"""Pinhole figures. usage: figs_pinholes.py -> figs/fig6_pinholes_sweep.png (sweep + gap histogram), figs/fig7_pinhole_cases.png (three zoomed candidate maps)
Inputs: tables/latent_connection_sweep.csv, tables/pinholes_<region>_r50.csv, work/<region>_nm50_pairs.parquet (sens_nearmiss2.py), work/<region>_drv_A_nodes.npz, work/<region>_drv_snap.parquet, work/<region>_bldg.parquet.
Map colours: red = roads and homes of the single-link cluster; orange = the single link; grey = other roads; blue = arterial (sink); blue star + dashed line = shortest candidate connection."""
import sys, numpy as np, pandas as pd, shapely, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely import STRtree, box
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
from spof import load_graph
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
FIG = f"{LANE}/figs"
NAME = {"northern-ca": "N. California", "eastern-ok": "E. Oklahoma", "maricopa-az": "Maricopa AZ", "south-central-tx": "S-C Texas", "eastern-wa": "E. Washington"}
COL = {"northern-ca": "#d95f02", "eastern-ok": "#7570b3", "maricopa-az": "#1b9e77", "south-central-tx": "#e7298a", "eastern-wa": "#66a61e"}
# ---------------- Fig 6: sweep + gap histogram
SW = pd.read_csv(f"{OUT}/latent_connection_sweep.csv")
fig, axs = plt.subplots(1, 3, figsize=(15.2, 4.4), gridspec_kw={"width_ratios": [1.15, 1, 0.95]})
ax = axs[0]; xs = [0, 25, 50, 100, 250]
for _, r in SW.iterrows():
    ys = [100, 100 - r.cut_25m_pct, 100 - r.cut_50m_pct, 100 - r.cut_100m_pct, 100 - r.cut_250m_pct]
    ax.plot(xs, ys, "-o", color=COL[r.region], lw=1.6, ms=4, label=NAME[r.region]); ax.text(252, ys[-1], f"{ys[-1]:.0f}%", fontsize=7, va="center", color=COL[r.region])
ax.axvspan(25, 250, color="#f0f0f0", zorder=0); ax.text(140, 53.5, "upper bound beyond 25 m:\nprivate drives, fences,\nterrain not excluded", fontsize=7, ha="center", color="#555555")
ax.set_xlim(-8, 285); ax.set_ylim(50, 102); ax.set_xlabel("dead-end tips joined to the nearest unconnected road within r metres"); ax.set_ylabel("single-link exposure remaining (% of baseline S30)")
ax.set_title("How much single-link exposure hinges on short gaps?", fontsize=9); ax.legend(fontsize=7.5, frameon=False, loc="lower left")
ax = axs[1]
A = pd.concat([pd.read_csv(f"{OUT}/pinholes_{r}_r50.csv", dtype={"tract": str}) for r in SW.region], ignore_index=True)
big = A[(A.load_dw >= 100) & (A.share_relieved >= 0.5) & A.min_gap_m.notna()]
bins = [0, 5, 10, 25, 50]; lab = ["<5 m", "5-10 m", "10-25 m", "25-50 m"]
cnt = pd.cut(big.min_gap_m, bins=bins, labels=lab, right=True).value_counts().reindex(lab); dwl = big.groupby(pd.cut(big.min_gap_m, bins=bins, labels=lab, right=True), observed=False).relieved_dw.sum().reindex(lab)
ax.bar(range(4), cnt.values, color=["#b2182b", "#ef8a62", "#fddbc7", "#d9d9d9"], width=0.7)
for i, (c, d) in enumerate(zip(cnt.values, dwl.values)): ax.text(i, c + max(cnt.values) * 0.02, f"{int(c)} clusters\n{d/1000:.1f}k dwellings", ha="center", fontsize=7.5)
ax.set_xticks(range(4)); ax.set_xticklabels(lab); ax.set_ylim(0, max(cnt.values) * 1.28); ax.set_xlabel("shortest candidate connection (m)"); ax.set_ylabel("single-link clusters (>=100 dwellings) with >=50% relieved")
ax.set_title(f"{int(cnt.sum())} candidate pinholes, 5 regions", fontsize=9)
ax = axs[2]; M = pd.read_csv(f"{OUT}/validation_hays_repair_metrics.csv"); xi = np.arange(len(M))
ax.bar(xi - 0.18, M.true_positives, 0.36, color="#b2182b", label=f"documented one-exit areas still flagged (of {int(M.n_one_exit.iloc[0])})")
ax.bar(xi + 0.18, M.false_positives, 0.36, color="#2166ac", label=f"documented multi-exit areas flagged (of {int(M.n_multi_exit.iloc[0])})")
for x_, t_, f_ in zip(xi, M.true_positives, M.false_positives): ax.text(x_ - 0.18, t_ + 0.3, int(t_), ha="center", fontsize=7.5); ax.text(x_ + 0.18, f_ + 0.3, int(f_), ha="center", fontsize=7.5)
ax.set_xticks(xi); ax.set_xticklabels([("baseline" if r == 0 else f"{int(r)} m") for r in M.radius_m]); ax.set_ylim(0, 22); ax.set_xlabel("repair radius"); ax.set_ylabel("Hays County neighbourhoods flagged single-route")
ax.legend(fontsize=6.8, frameon=False, loc="upper right"); ax.set_title("Independent check (Ramos & Yuan 2024, 57 neighbourhoods):\nrepairs >= 100 m erase true single-exit flags", fontsize=8.5)
fig.tight_layout(pad=1.6); fig.savefig(f"{FIG}/fig6_pinholes_sweep.png", dpi=170); plt.close(fig); print("wrote fig6")
# ---------------- Fig 7: three zoomed cases
CASES = [("northern-ca", "Mountain Shadows Boulevard"), ("maricopa-az", "Wall Street"), ("eastern-wa", "Lincoln Drive")]
fig, axs = plt.subplots(1, 3, figsize=(13.2, 4.8)); HALF = 330
ARTERIAL = {"motorway", "trunk", "primary", "secondary"}
for ax, (region, rn) in zip(axs, CASES):
    T = pd.read_csv(f"{OUT}/pinholes_{region}_r50.csv", dtype={"tract": str}); row = T[(T.rname == rn) & (T.load_dw >= 100)].sort_values("relieved_dw", ascending=False).iloc[0]; C = int(row.cluster)
    G = load_graph(region, "drv"); P, geoms, nx, ny = G["P"], G["geoms"], G["nx"], G["ny"]
    topc = np.load(f"{WORK}/{region}_drv_A_nodes.npz")["topc"]; pr = pd.read_parquet(f"{WORK}/{region}_nm50_pairs.parquet")
    ids = np.stack([topc[pr.d.values], topc[P.u.values[pr.p.values]], topc[P.v.values[pr.p.values]]], 1); m = (ids == C).any(1) & (ids != C).any(1)
    cd = pr[m].sort_values("dist").iloc[0]; tip = np.array([nx[int(cd.d)], ny[int(cd.d)]]); sl = shapely.shortest_line(shapely.Point(tip), geoms[int(cd.p)]); tgt = np.array(sl.coords[-1]); mid = (tip + tgt) / 2; lnk = np.array([nx[C], ny[C]]); cen = (mid + lnk) / 2; HALF = min(700.0, max(330.0, 0.5 * float(np.hypot(*(mid - lnk))) + 220.0))
    W = box(cen[0] - HALF, cen[1] - HALF, cen[0] + HALF, cen[1] + HALF); idx = STRtree(geoms).query(W, predicate="intersects")
    for i in idx:
        u, v = int(P.u.values[i]), int(P.v.values[i]); inC = (topc[u] == C) and (topc[v] == C); link = (topc[u] == C) != (topc[v] == C) and (topc[u] == C or topc[v] == C)
        art = P.cls.values[i] in ARTERIAL
        col, lw, z = ("#2166ac", 2.2, 2) if art else (("#ff7f00", 2.6, 4) if link else (("#b2182b", 1.6, 3) if inC else ("#9a9a9a", 1.1, 1)))
        c = np.asarray(geoms[i].coords) - cen; ax.plot(c[:, 0], c[:, 1], color=col, lw=lw, zorder=z, solid_capstyle="round")
    Bd = pd.read_parquet(f"{WORK}/{region}_bldg.parquet", columns=["x", "y"]); S = pd.read_parquet(f"{WORK}/{region}_drv_snap.parquet", columns=["node", "cand"])
    inwin = ((Bd.x.values - cen[0]).__abs__() < HALF) & ((Bd.y.values - cen[1]).__abs__() < HALF); node = S.node.values
    clb = (node >= 0) & (topc[np.maximum(node, 0)] == C) & S.cand.values
    ax.scatter(Bd.x.values[inwin & ~clb] - cen[0], Bd.y.values[inwin & ~clb] - cen[1], s=2.5, color="#d0d0d0", zorder=0)
    ax.scatter(Bd.x.values[inwin & clb] - cen[0], Bd.y.values[inwin & clb] - cen[1], s=3.5, color="#e34a33", alpha=0.8, zorder=2)
    ax.plot([tip[0] - cen[0], tgt[0] - cen[0]], [tip[1] - cen[1], tgt[1] - cen[1]], color="#08519c", lw=2.2, ls=(0, (2, 1)), zorder=6)
    ax.scatter([tip[0] - cen[0]], [tip[1] - cen[1]], marker="*", s=130, color="#08519c", edgecolor="white", lw=0.6, zorder=7)
    ax.scatter([lnk[0] - cen[0]], [lnk[1] - cen[1]], marker="D", s=46, color="#ff7f00", edgecolor="k", lw=0.6, zorder=8)
    ax.set_xlim(-HALF, HALF); ax.set_ylim(-HALF, HALF); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.plot([-HALF + 25, -HALF + 125], [-HALF + 22, -HALF + 22], color="k", lw=2); ax.text(-HALF + 75, -HALF + 36, "100 m", ha="center", fontsize=7)
    pl = str(row.place).split(",")[0]
    ax.set_title(f"{rn}, {pl}\n{row.load_dw:,.0f} dwellings behind one link; candidate gap {row.min_gap_m:.1f} m", fontsize=8.5)
fig.suptitle("Candidate pinholes: red = homes/roads whose only way out is the orange link (diamond); blue star + dashed line = shortest unconnected gap to another road (UNVERIFIED)", fontsize=8.8, y=0.985)
fig.tight_layout(pad=1.4, rect=(0, 0, 1, 0.945)); fig.savefig(f"{FIG}/fig7_pinhole_cases.png", dpi=170); plt.close(fig); print("wrote fig7")
