"""Figures for the Best Bias Discovery write-up (M1 draft set). usage: figs_m1.py    -> figs/fig1_northern-ca_map.png, figs/fig2_effects_forest.png, figs/fig3_validation.png
Inputs: tables/*.csv from the egress pipeline (all derived from the PROVIDED package + the public sources in SOURCES.md). Seeded/deterministic."""
import sys, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
FIG = f"{LANE}/figs"
import os; os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

# ---------------- Fig 1: Northern California map -------------------------------------------------------------------------------------------
def region_map(region, label, fn, nlabel=8, ntop=40, bounds=None):
    tr = gpd.read_parquet(strata(region, "census-tracts"))
    T = pd.read_parquet(f"{WORK}/{region}_drv_A_tract.parquet").reset_index(names="GEOID")[["GEOID", "eq_s30", "eq_den", "eq_nps30"]]
    G = tr.merge(T, on="GEOID", how="left")
    L = pd.read_csv(f"{OUT}/{region}_drv_A_links.csv", dtype={"tract": str}).sort_values("load_dwell", ascending=False).head(ntop)
    fig, ax = plt.subplots(figsize=(7.5, 8.2))
    G.plot(column="eq_s30", ax=ax, cmap="YlOrRd", norm=PowerNorm(0.6, vmin=0, vmax=0.45), edgecolor="#bbbbbb", linewidth=0.15, missing_kwds={"color": "#eeeeee"})
    ax.scatter(L.lon, L.lat, s=np.sqrt(L.load_dwell) * 3.2, facecolor="none", edgecolor="#0b3d91", linewidth=1.0, alpha=0.9)
    for _, r in L.head(nlabel).iterrows():
        nm = (r.rname if isinstance(r.rname, str) else "(unnamed)")
        ax.annotate(f"{nm} ({r.load_dwell:,.0f})", (r.lon, r.lat), xytext=(6, 5), textcoords="offset points", fontsize=6.5, color="#0b3d91",
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.75))
    lat0 = np.nanmean(G.geometry.centroid.y); ax.set_aspect(1 / np.cos(np.radians(lat0)))
    if bounds: ax.set_xlim(bounds[0], bounds[1]); ax.set_ylim(bounds[2], bounds[3])
    sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=PowerNorm(0.6, vmin=0, vmax=0.45)); cb = fig.colorbar(sm, ax=ax, shrink=0.55, pad=0.01); cb.set_label("S30 share of tract dwellings", fontsize=8)
    ax.set_title(f"{label}\nShading = share of dwellings behind a single link serving >=30 dwellings;\ncircles = the {ntop} largest single links (area ~ dwellings behind them)", fontsize=8.5)
    ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout(); fig.savefig(f"{FIG}/{fn}", dpi=170); plt.close(fig)
    print("wrote", fn)

# fig1 maps (all five regions, incl. northern-ca) are now drawn by figs_regions.py (lead review 2026-10-14 21:15Z); this older region_map() is kept for reference only and is no longer called

# ---------------- Fig 2: effect sizes forest -------------------------------------------------------------------------------------------------
C = pd.read_csv(f"{OUT}/stats_contrasts_drv_A.csv")
F = pd.read_csv(f"{OUT}/fac_stats_drv_A.csv")
M = pd.read_csv(f"{OUT}/mh_tract_drv_A.csv")
rows = []
def addc(name, contrast, group="pooled", metric="S30 (dwellings)"):
    r = C[(C.contrast == contrast) & (C.group == group) & (C.metric == metric)].iloc[0]; rows.append((name, r.ratio, r.ratio_lo, r.ratio_hi))
addc("Rural vs urban tracts", "Rural vs Urban")
addc("High-SVI vs low-SVI tracts (Q4/Q1)", "SVI Q4 vs Q1")
addc("High-CVI vs low-CVI tracts (Q4/Q1)", "CVI Q4 vs Q1")
addc("Wildfire hazard Q4/Q1 (raw)", "WHP Q4 vs Q1 (raw)")
addc("Tribal vs non-tribal, Maricopa", "Tribal vs non-tribal", group="maricopa-az")
q = M[(M.kind == "quartile") & (M.group == "pooled")].iloc[0]; rows.append(("Mobile-home share Q4/Q1 (tract)", q.ratio, q.ratio_lo, q.ratio_hi))
for kind, nm in [("mobile_home_park", "Mobile-home parks vs their tract's dwellings"), ("school", "Schools vs their tract's dwellings"), ("hospital", "Hospitals"), ("fire", "Fire stations"), ("senior_care", "Senior care")]:
    r = F[(F.kind == kind) & (F.group == "pooled") & (F.metric == "S30")].iloc[0]; rows.append((nm, r.ratio, r.ratio_lo, r.ratio_hi))
fig, ax = plt.subplots(figsize=(7.6, 4.4))
y = np.arange(len(rows))[::-1]
for yi, (nm, r, lo, hi) in zip(y, rows):
    col = "#b2182b" if lo > 1 else ("#2166ac" if hi < 1 else "#777777")
    ax.plot([lo, hi], [yi, yi], color=col, lw=2); ax.plot([r], [yi], "o", color=col)
    ax.text(3.2, yi, f"{r:.2f}x  ({lo:.2f}-{hi:.2f})", va="center", ha="left", fontsize=7.5)
ax.axvline(1, color="k", lw=0.8, ls="--"); ax.set_xscale("log"); ax.set_xlim(0.1, 9)
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows]); ax.set_xlabel("ratio of S30 exposure (95% cluster-bootstrap CI), 5 regions pooled", fontsize=8)
ax.set_title("Who is behind a single link? Mobile-home parks and rural tracts;\nnot high-SVI tracts, not public facilities", fontsize=9)
plt.close(fig); print("fig2 (effects forest) is drawn by figs_forest.py with the seasonal row; not written here")

# ---------------- Fig 3: validation ----------------------------------------------------------------------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.9))
V = pd.read_csv(f"{OUT}/validation_tehama.csv"); V = V[V.matched_pieces > 0]
ax = axs[0]
import re as _re
n20 = int((V.max_cluster_load_dwell >= 20).sum()); nV = len(V); S_ = open(f"{OUT}/validation_tehama_summary.txt").read()
m20 = _re.search(r"max cluster load >= 20 dwellings: documented [0-9.]+ \((\d+)/(\d+)\)", S_); assert m20 and (int(m20.group(1)), int(m20.group(2))) == (n20, nV), "figure and validation summary disagree on the 20+ dwellings count"
sp_ = _re.search(r"Spearman\(.*?\) = ([0-9.]+) \(p=[0-9.e+-]+, n=(\d+)\)", S_); rho = float(sp_.group(1)); assert int(sp_.group(2)) == nV
ax.scatter(V.est_population, V.max_cluster_load_dwell.clip(lower=1), c=np.where(V.max_cluster_load_dwell >= 20, "#b2182b", "#777777"), s=28)
ax.axhline(20, color="#555555", ls=":", lw=1); ax.text(V.est_population.max(), 22, "20 dwellings", fontsize=7, ha="right", va="bottom", color="#555555")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("population documented by Tehama County study (est.)"); ax.set_ylabel("dwellings behind the worst\nsingle link (graph)", fontsize=8.5)
T3 = f"Tehama County CA: 32 documented single-access areas\nSpearman {rho:.2f} (n={nV}); {n20} of {nV} have 20+ dwellings behind one link"; ax.set_title(T3, fontsize=8.5)
H = pd.read_csv(f"{OUT}/validation_hays.csv")
ax = axs[1]
rng = np.random.default_rng(SEED)
groups = [("1 exit", H[H.exits == 1]), ("2 exits", H[H.exits == 2]), (">=3 exits", H[H.exits >= 3])]
for i, (nm, g) in enumerate(groups):
    ax.scatter(i + rng.uniform(-0.15, 0.15, len(g)), g.share_single, s=22, color=["#b2182b", "#999999", "#2166ac"][i], alpha=0.85)
    ax.hlines(g.share_single.mean(), i - 0.28, i + 0.28, color="k", lw=1.5)
ax.axhline(0.265, color="#555555", ls=":", lw=1); ax.text(2.35, 0.28, "random Hays\nbase rate", fontsize=7, ha="right")
ax.set_xticks(range(3)); ax.set_xticklabels([n for n, _ in groups]); ax.set_ylabel("share of buildings with\na single route (graph)", fontsize=8.5)
ax.set_xlabel("published adjusted exits (Ramos & Yuan 2024, Table 1)"); T4 = "Hays County TX: 57 neighbourhoods; AUC 0.854, Fisher p=3e-7"; ax.set_title(T4, fontsize=8.5); open(f"{OUT}/fig3_validation_labels.txt", "w").write(T3 + "\n" + T4 + "\n")   # the number ledger checks these titles against the text
fig.tight_layout(pad=1.6); fig.savefig(f"{FIG}/fig3_validation.png", dpi=170); plt.close(fig); print("wrote fig3")
