"""Effect-size forest (draft Fig. 5 = figs/fig2_effects_forest.png). EVERY row is a county-clustered estimate (325 counties, five regions pooled; dwelling-weighted pooled ratios), so a reader sees
one number per contrast, the same one the text quotes. Rows come from tables/county_boot.csv (county_boot.py) and tables/county_boot_facilities.csv (county_boot_facilities.py);
the figure's input is written to tables/effects_forest_county.csv (the number ledger checks the text against it).
usage: figs_forest.py -> figs/fig2_effects_forest.png, tables/effects_forest_county.csv"""
import sys, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False})
CB = pd.read_csv(f"{OUT}/county_boot.csv").set_index("contrast"); FB = pd.read_csv(f"{OUT}/county_boot_facilities.csv").set_index("kind")
rows = []
def addc(label, contrast): r = CB.loc[contrast]; rows.append((label, r.ratio, r.lo, r.hi, "county_boot.csv", int(r.counties)))
def addf(label, kind): r = FB.loc[kind]; rows.append((label, r.ratio, r.lo, r.hi, "county_boot_facilities.csv", int(r.counties)))
addc("Resort-type tracts (10%+ seasonal) vs others", "Resort-type (>=10% seasonal) vs other")
addc("Mobile-home share Q4/Q1 (tract)", "Mobile-home share Q4 vs Q1")
addf("Mobile-home parks vs their tract's dwellings", "mobile_home_park")
addc("Rural vs urban tracts", "Rural vs urban")
addc("High-SVI vs low-SVI tracts (Q4/Q1)", "SVI Q4 vs Q1")
addc("High-CVI vs low-CVI tracts (Q4/Q1)", "CVI Q4 vs Q1")
addc("Wildfire hazard Q4/Q1 (raw)", "Wildfire hazard Q4 vs Q1 (raw)")
addc("Tribal vs non-tribal tracts", "Tribal vs non-tribal")
addf("Schools vs their tract's dwellings", "school"); addf("Hospitals", "hospital"); addf("Fire stations", "fire"); addf("Senior care", "senior_care")
T = pd.DataFrame(rows, columns=["row", "ratio", "lo", "hi", "source", "counties"]); T.to_csv(f"{OUT}/effects_forest_county.csv", index=False)
assert T.lo.min() > 0.15 and T.hi.max() < 4.0, "x-range 0.15-4 must hold every interval"
fig, ax = plt.subplots(figsize=(7.4, 3.3)); y = np.arange(len(T))[::-1]
for yi, r in zip(y, T.itertuples()):
    col = "#b2182b" if r.lo > 1 else ("#2166ac" if r.hi < 1 else "#777777")
    ax.plot([r.lo, r.hi], [yi, yi], color=col, lw=2); ax.plot([r.ratio], [yi], "o", color=col)
    ax.text(1.02, yi, f"{r.ratio:.2f}x  ({r.lo:.2f}-{r.hi:.2f})", transform=ax.get_yaxis_transform(), va="center", ha="left", fontsize=7.8, clip_on=False)
ax.axvline(1, color="k", lw=0.8, ls="--"); ax.set_xscale("log"); ax.set_xlim(0.15, 4); ax.set_ylim(-0.6, len(T) - 0.4)
ax.xaxis.set_major_locator(FixedLocator([0.2, 0.5, 1, 2, 4])); ax.xaxis.set_major_formatter(FixedFormatter(["0.2", "0.5", "1", "2", "4"])); ax.xaxis.set_minor_formatter(NullFormatter()); ax.minorticks_off()
ax.set_yticks(y); ax.set_yticklabels(T.row.tolist()); ax.set_xlabel("ratio of S30 exposure (95% county-clustered bootstrap CI), 5 regions pooled", fontsize=8)
fig.text(0.012, 0.985, "Resort-type, mobile-home and rural tracts are more exposed; high-SVI tracts and public facilities less", ha="left", va="top", fontsize=8.6)
fig.subplots_adjust(left=0.37, right=0.80, top=0.92, bottom=0.15)
fig.savefig(f"{LANE}/figs/fig2_effects_forest.png", dpi=170, bbox_inches="tight", pad_inches=0.06); plt.close(fig)
for r in T.itertuples(): print(f"{r.row:55s} {r.ratio:5.2f}x ({r.lo:.2f}-{r.hi:.2f})  [{r.source}, {r.counties} counties]")
print("wrote fig2_effects_forest.png and tables/effects_forest_county.csv")
