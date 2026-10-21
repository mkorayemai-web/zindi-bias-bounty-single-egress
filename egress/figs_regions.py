"""Figures for D5: one map per region (all five, final fig1 set) + region bars (baseline vs robust S30). usage: figs_regions.py
-> figs/fig1_<region>_map.png for all 5 regions (run AFTER figs_m1.py; figs_m1.py no longer draws fig1), figs/fig5_region_bars.png
Inputs: tables/<region>_drv_A_links.csv, work/<region>_drv_A_tract.parquet, tables/false_single_access.csv. Deterministic.
Layout review 2026-10-14 21:15Z applied: axes removed, de-overlapped labels with leader lines kept inside the map, circle-size key, non-linear colour scale stated, circle encoding stated correctly
(marker area proportional to the SQUARE ROOT of dwellings; the earlier title said 'area ~ dwellings', which was wrong)."""
import sys, os, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from matplotlib.lines import Line2D
import shapely
from shapely.geometry import box as sbox
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
from figlabels import place_labels, qa
FIG = f"{REPO_ROOT}/figs"; os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
LABELS = {"eastern-ok": "Eastern Oklahoma", "maricopa-az": "Maricopa County, Arizona", "south-central-tx": "South-Central Texas", "eastern-wa": "Eastern Washington", "northern-ca": "Northern California"}
NORM = PowerNorm(0.6, vmin=0, vmax=0.45); BLUE = "#0b3d91"; FILL = (0.04, 0.24, 0.57, 0.12)
W1, H1 = 5.0, 5.6; K1 = W1 / 7.5                                    # canvas of the maps (in); the earlier 7.5 x 8.4 in canvas printed 8-9 pt fonts at ~4.5 pt
SZ = lambda d: np.sqrt(np.asarray(d, dtype=float)) * 3.2 * K1 ** 2   # scatter s = marker area (pt^2): area proportional to sqrt(dwellings), scaled with the canvas

def add_zoom_inset(fig, ax, G, L, lat0, s_frac=0.33, k_min=6, r_deg=0.55):
    """Zoom inset on the densest cluster of the top links (>= k_min links within r_deg), placed in the corner that hides the least map content; skipped if it would cover links."""
    X = L[["lon", "lat"]].values; cosl = np.cos(np.radians(lat0)); best = None
    for x, y in X:
        m = np.hypot((X[:, 0] - x) * cosl, X[:, 1] - y) < r_deg
        if m.sum() >= k_min and (best is None or m.sum() > best[0]): best = (int(m.sum()), m)
    if best is None: return None, "no dense cluster (fewer than %d links within %.2f deg)" % (k_min, r_deg)
    sel = L[best[1]]; cx, cy = sel.lon.mean(), sel.lat.mean()
    ext_km = max((sel.lon.max() - sel.lon.min()) * cosl, sel.lat.max() - sel.lat.min()) * 111.0
    hw_km = max(22.0, ext_km / 2 + 9.0); hw_lat = hw_km / 111.0; hw_lon = hw_km / (111.0 * cosl); win = sbox(cx - hw_lon, cy - hw_lat, cx + hw_lon, cy + hw_lat)
    ab = ax.get_window_extent(); s_px = s_frac * min(ab.width, ab.height); fx, fy = s_px / ab.width, s_px / ab.height
    inv = ax.transAxes + ax.transData.inverted(); U = shapely.union_all(G.geometry.simplify(0.01).values)
    cands = {"lower-left": (0.015, 0.015), "lower-right": (1 - fx - 0.015, 0.015), "upper-left": (0.015, 1 - fy - 0.015), "upper-right": (1 - fx - 0.015, 1 - fy - 0.015)}
    scored = []
    for name, (a0, b0) in cands.items():
        (x0, y0) = inv.transform((a0, b0)); (x1, y1) = inv.transform((a0 + fx, b0 + fy)); b = sbox(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        content = U.intersection(b).area / b.area; nc = int(((L.lon > b.bounds[0]) & (L.lon < b.bounds[2]) & (L.lat > b.bounds[1]) & (L.lat < b.bounds[3])).sum())
        scored.append((content + 0.1 * nc, name, a0, b0, content, nc))
    ok = [t for t in scored if t[5] == 0 and t[4] <= 0.30]                       # an inset may not hide any of the top links and at most 30 % of its own area may sit on map content
    if not ok: sc, name, a0, b0, content, nc = min(scored); return None, f"every corner would hide links or map content (best {name}: {100*content:.0f} % covered, {nc} links)"
    sc, name, a0, b0, content, nc = min(ok)
    axi = ax.inset_axes([a0, b0, fx, fy]); Gw = G[G.intersects(win)]
    Gw.plot(column="eq_s30", ax=axi, cmap="YlOrRd", norm=NORM, edgecolor="#bbbbbb", linewidth=0.2, missing_kwds={"color": "#eeeeee"}, aspect=None)
    wb = win.bounds; Lw = L[(L.lon > wb[0]) & (L.lon < wb[2]) & (L.lat > wb[1]) & (L.lat < wb[3])]
    axi.scatter(Lw.lon, Lw.lat, s=SZ(Lw.load_dwell), facecolor=FILL, edgecolor=BLUE, linewidth=0.9, zorder=3)
    axi.set_xlim(wb[0], wb[2]); axi.set_ylim(wb[1], wb[3]); axi.set_xticks([]); axi.set_yticks([]); axi.set_xlabel(""); axi.set_ylabel("")   # geopandas adds "Geodetic latitude/longitude" axis labels
    for sp in axi.spines.values(): sp.set_visible(True); sp.set_linewidth(0.9)
    axi.text(0.03, 0.97, f"zoom: {len(Lw)} of the {len(L)} links", transform=axi.transAxes, ha="left", va="top", fontsize=7.5, zorder=10, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    ax.add_patch(plt.Rectangle((wb[0], wb[1]), wb[2] - wb[0], wb[3] - wb[1], fill=False, ec="k", lw=0.8, zorder=5))
    return axi, dict(corner=name, map_content_under_inset=round(content, 3), window_km=round(2 * hw_km), links_in_zoom=len(Lw), tracts_in_zoom=len(Gw))

def region_map(region, label, fn, nlabel=8, ntop=40):
    tr = gpd.read_parquet(strata(region, "census-tracts"))
    T = pd.read_parquet(f"{WORK}/{region}_drv_A_tract.parquet").reset_index(names="GEOID")[["GEOID", "eq_s30", "eq_den", "eq_nps30"]]
    G = tr.merge(T, on="GEOID", how="left")
    L = pd.read_csv(f"{OUT}/{region}_drv_A_links.csv", dtype={"tract": str}).sort_values("load_dwell", ascending=False).head(ntop)
    fig, ax = plt.subplots(figsize=(W1, H1))
    G.plot(column="eq_s30", ax=ax, cmap="YlOrRd", norm=NORM, edgecolor="#bbbbbb", linewidth=0.15, missing_kwds={"color": "#eeeeee"})
    ax.scatter(L.lon, L.lat, s=SZ(L.load_dwell), facecolor=FILL, edgecolor=BLUE, linewidth=0.7, zorder=3)          # largest first: small circles stay visible on top
    lat0 = np.nanmean(G.geometry.centroid.y); ax.set_aspect(1 / np.cos(np.radians(lat0))); ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=NORM)
    cb = fig.colorbar(sm, ax=ax, shrink=0.55, pad=0.01, extend="max", ticks=[0, 0.05, 0.10, 0.20, 0.30, 0.45]); cb.ax.set_yticklabels(["0", "5 %", "10 %", "20 %", "30 %", "45 %+"], fontsize=8)
    cb.set_label("S30 share of tract dwellings\n(non-linear scale, capped at 45 %)", fontsize=8)
    keys = [k for k in (300, 1000, 3000) if k <= 1.05 * L.load_dwell.max()]
    hs = [Line2D([0], [0], marker="o", ls="", mfc=FILL, mec=BLUE, mew=0.9, ms=float(np.sqrt(SZ(k))), label=f"{k:,} dwellings") for k in keys]
    fig.legend(handles=hs, title="circle size key", loc="lower center", ncol=len(keys), fontsize=8, title_fontsize=8, frameon=False, labelspacing=1.0, handletextpad=0.5, columnspacing=2.2, borderpad=0.2, borderaxespad=0.9)
    fig.tight_layout(pad=0.8, rect=(0, 0.09, 1, 1)); fig.canvas.draw()
    inset, info = add_zoom_inset(fig, ax, G, L, lat0); avoid = []
    if inset is not None: ib = inset.get_window_extent(); avoid = [(ib.x0, ib.y0, ib.x1, ib.y1)]
    print(f"   inset: {info}")
    top = L.head(nlabel); txt = [f"{(r.rname if isinstance(r.rname, str) else '(unnamed)')} ({r.load_dwell:,.0f})" for r in top.itertuples()]
    done, skipped = place_labels(fig, ax, top.lon.values, top.lat.values, txt, fontsize=8.0, color=BLUE, avoid=avoid)
    print(f"{region}: labels placed {len(done)}/{len(txt)}; skipped {skipped}")
    out, ov = qa(fig, region)
    tmp = f"{FIG}/_uncropped_{fn}"; fig.savefig(tmp, dpi=170)                      # pixel check on the uncropped canvas (the inset coordinates refer to it); the published PNG is cropped below
    if inset is not None:                                                         # pixel check of the saved PNG: the inset must be non-empty, contain circle-blue pixels and stay off the figure edge
        from PIL import Image
        im = np.asarray(Image.open(tmp).convert("RGB")).astype(int); Hh, Ww, _ = im.shape; k = 170.0 / fig.dpi
        x0, y0, x1, y1 = [int(round(v * k)) for v in (ib.x0, ib.y0, ib.x1, ib.y1)]; sub = im[Hh - y1:Hh - y0, x0:x1]
        nonwhite = float((sub.sum(axis=2) < 740).mean()); blue = int(((sub[:, :, 0] < 60) & (sub[:, :, 1] < 90) & (sub[:, :, 2] > 110)).sum())
        print(f"   inset pixel check: {sub.shape[1]}x{sub.shape[0]} px, non-white {100*nonwhite:.0f} %, circle-blue px {blue}, margins to figure edge L{x0} R{Ww-x1} T{Hh-y1} B{y0}")
    os.remove(tmp); fig.savefig(f"{FIG}/{fn}", dpi=170, bbox_inches="tight", pad_inches=0.06)     # crop the white margins
    plt.close(fig); print("wrote", fn)
for r in ("northern-ca", "eastern-ok", "maricopa-az", "south-central-tx", "eastern-wa"):
    region_map(r, f"{LABELS[r]} (Overture 2026-08-19.0 road graph)", f"fig1_{r}_map.png")
# ---- region bars: baseline S30 vs the part that survives service/track roads AND <=25 m gap repair
F = pd.read_csv(f"{OUT}/false_single_access.csv"); F = F[F.region != "pooled"].set_index("region").loc[["northern-ca", "eastern-ok", "maricopa-az", "south-central-tx", "eastern-wa"]]
fig, ax = plt.subplots(figsize=(7.6, 4.2)); x = np.arange(len(F)); base = 100 * F.S30_share.values
rob = np.where(F.robust_pct.notna(), base * F.robust_pct.fillna(0).values / 100, np.nan)
r25 = base * (1 - F.flips_with_repair25_pct.values / 100)
ax.bar(x - 0.2, base, 0.38, color="#e6550d", label="baseline: dwellings behind a single link serving >=30 dwellings")
ax.bar(x + 0.2, np.where(np.isnan(rob), r25, rob), 0.38, color=np.where(np.isnan(rob), "#fdae6b", "#9ecae1"),
       label="survives gap repair <=25 m AND service/track roads")
for xi, b, rb in zip(x, base, np.where(np.isnan(rob), r25, rob)):
    ax.text(xi - 0.2, b + 0.2, f"{b:.1f}%", ha="center", fontsize=7.5); ax.text(xi + 0.2, rb + 0.2, f"{rb:.1f}%", ha="center", fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels([LABELS[r].replace(", Arizona", "").replace("Maricopa County", "Maricopa AZ") for r in F.index], fontsize=8)
ax.set_ylabel("% of dwellings"); ax.set_ylim(0, max(base) * 1.3); ax.legend(fontsize=6.8, frameon=False, loc="upper right")
ax.set_title("Single-link exposure by region and how much of it is robust to the map's own incompleteness", fontsize=9)
fig.tight_layout(pad=1.6); qa(fig, "fig5"); fig.savefig(f"{FIG}/fig5_region_bars.png", dpi=170); plt.close(fig); print("wrote fig5")
