"""Second finding (fallback / companion): census person counts understate the people behind single links in second-home (resort) clusters.
Peak persons behind a single link = census persons (ACS, usual residents) + seasonal units behind the link x q, with q = persons per seasonal unit on a peak weekend/holiday - an ASSUMPTION stated as a range, not a measurement:
  low  q = 1.2  (about half of the seasonal units occupied at the year-round household size)
  mid  q = 2.3  (every seasonal unit occupied at the observed year-round persons per dwelling of non-resort single-link clusters, 2.34 - computed here)
  high q = 3.5  (all occupied by visiting groups 1.5x the year-round size)
Seasonal units behind a link = dwellings behind the link x the tract's seasonal share (ACS B25004 E006 / B25001), i.e. a tract-uniform allocation (only bias-free when the whole tract is resort-like; hence the >= 25 % stratum).
Inputs tables/seasonal_clusters.csv (single-link clusters >= 100 dwellings, 5 regions; seasonal2.py). usage: seasonal_load.py -> tables/seasonal_load_range.csv, tables/seasonal_load_summary.csv, figs/fig8_seasonal_load.png"""
import sys, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
from figlabels import qa
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
C = pd.read_csv(f"{OUT}/seasonal_clusters.csv", dtype={"tract": str}); C = C[(C.load_dwell >= 100) & C.seas_share.notna() & (C.load_persons > 0)].copy()
base = C[C.seas_share < 0.02]; PPD0 = base.load_persons.sum() / base.load_dwell.sum()
Q = {"low": 1.2, "mid": round(PPD0, 2), "high": 3.5}
print(f"clusters used: {len(C)}; year-round persons per dwelling in non-resort single-link clusters (<2% seasonal): {PPD0:.3f}; scenarios q = {Q}")
C["seasonal_units"] = C.load_dwell * C.seas_share
for k, q in Q.items():
    C[f"peak_{k}"] = C.load_persons + C.seasonal_units * q; C[f"ratio_{k}"] = C[f"peak_{k}"] / C.load_persons
C.to_csv(f"{OUT}/seasonal_load_range.csv", index=False)
rows = []
def summ(name, d):
    r = dict(group=name, clusters=len(d), dwellings=d.load_dw if False else d.load_dwell.sum(), census_persons=d.load_persons.sum(), seasonal_units=d.seasonal_units.sum())
    for k in Q: r[f"peak_{k}"] = d[f"peak_{k}"].sum(); r[f"ratio_{k}"] = r[f"peak_{k}"] / r["census_persons"]; r[f"extra_{k}"] = r[f"peak_{k}"] - r["census_persons"]
    r["clusters_ratio_ge_1.5_mid"] = int((d.ratio_mid >= 1.5).sum()); r["clusters_ratio_ge_2_mid"] = int((d.ratio_mid >= 2).sum()); r["clusters_ratio_ge_2_low"] = int((d.ratio_low >= 2).sum()); return r
rows.append(summ("all single-link clusters (>=100 dw), 5 regions", C))
for reg in ["northern-ca", "eastern-ok", "maricopa-az", "south-central-tx", "eastern-wa"]: rows.append(summ(reg, C[C.region == reg]))
for lab, m in [("tracts >=10% seasonal", C.seas_share >= 0.10), ("tracts >=25% seasonal (allocation least biased)", C.seas_share >= 0.25), ("tracts >=50% seasonal", C.seas_share >= 0.50)]: rows.append(summ(lab, C[m]))
S = pd.DataFrame(rows); S.to_csv(f"{OUT}/seasonal_load_summary.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(S[["group", "clusters", "dwellings", "census_persons", "seasonal_units", "peak_low", "peak_mid", "peak_high", "ratio_low", "ratio_mid", "ratio_high", "clusters_ratio_ge_1.5_mid", "clusters_ratio_ge_2_mid"]].round(2).to_string(index=False))
top = C[C.seas_share >= 0.25].sort_values("seasonal_units", ascending=False).head(12).iloc[::-1]   # resort-type clusters only (tracts >= 25 % seasonal): a non-resort giant (Walden Rd, 8.3 k census persons, ratio ~1.1x) must not set the axis
print(C.sort_values("seasonal_units", ascending=False).head(15)[["region", "place", "rname", "tract", "county", "load_dwell", "load_persons", "seas_share", "seasonal_units", "peak_low", "peak_mid", "peak_high", "ratio_mid"]].round(1).to_string(index=False))
fig, axs = plt.subplots(1, 2, figsize=(13.0, 5.0), gridspec_kw={"width_ratios": [1.5, 1]})
ax = axs[0]; y = np.arange(len(top))
lab = [f"{(r.rname if isinstance(r.rname, str) else '(unnamed road)')}, {str(r.place).split(',')[0]} ({r.region.split('-')[-1].upper()})" for r in top.itertuples()]
ax.barh(y, top.load_persons, color="#9e9e9e", label="census persons (usual residents)")
ax.barh(y, top.peak_mid - top.load_persons, left=top.load_persons, color="#e6550d", label=f"+ seasonal units x {Q['mid']} persons (mid scenario)")
ax.errorbar(top.peak_mid, y, xerr=[top.peak_mid - top.peak_low, top.peak_high - top.peak_mid], fmt="none", ecolor="k", capsize=2.5, lw=1, label=f"assumed range q = {Q['low']}-{Q['high']} persons per seasonal unit")
for yi, r in zip(y, top.itertuples()): ax.text(r.peak_high + 80, yi, f"{r.ratio_low:.1f}-{r.ratio_high:.1f}x", va="center", fontsize=7)
ax.set_yticks(y); ax.set_yticklabels(lab, fontsize=7.5); ax.set_xlim(0, top.peak_high.max() * 1.18); ax.set_xlabel("persons behind one road link"); ax.legend(fontsize=7, frameon=False, loc="lower right")
ax.set_title("Peak-weekend load vs census count: the 12 single links with most second homes\nbehind them (tracts with 25 %+ seasonal housing)", fontsize=9)
ax = axs[1]; G = S[S.group.isin(["tracts >=10% seasonal", "tracts >=25% seasonal (allocation least biased)", "tracts >=50% seasonal"])]
xi = np.arange(len(G)) * 1.8; ax.bar(xi, G.ratio_mid, color="#e6550d", width=0.55); ax.errorbar(xi, G.ratio_mid, yerr=[G.ratio_mid - G.ratio_low, G.ratio_high - G.ratio_mid], fmt="none", ecolor="k", capsize=4)
for x_, r_, lo_, hi_ in zip(xi, G.ratio_mid, G.ratio_low, G.ratio_high): ax.text(x_ + 0.36, r_, f"{r_:.2f}x\n({lo_:.2f}-{hi_:.2f})", ha="left", va="center", fontsize=8)   # beside the bar, clear of the whisker
ax.axhline(1, color="k", lw=0.8, ls="--"); ax.set_xticks(xi); ax.set_xticklabels(["10 %+", "25 %+", "50 %+"]); ax.set_xlim(-0.5, xi[-1] + 1.5); ax.set_xlabel("tracts by seasonal share of housing units"); ax.set_ylabel("peak persons / census persons", fontsize=8.5)
ax.set_title(f"Understatement of the people behind single links\nbars = mid case (q = {Q['mid']})\nwhiskers = assumed range q = {Q['low']}-{Q['high']}", fontsize=8.5)
fig.tight_layout(pad=1.6); qa(fig, "fig8"); fig.savefig(f"{REPO_ROOT}/figs/fig8_seasonal_load.png", dpi=170); print("wrote fig8")
