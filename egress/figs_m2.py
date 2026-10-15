"""Figure 4: seasonal / second-home communities behind single links (dose-response only; the named clusters are Fig. 3). usage: figs_m2.py -> figs/fig4_seasonal.png
Inputs: tables/seasonal_dose.csv (from seasonal2.py)."""
import sys, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
DR = pd.read_csv(f"{OUT}/seasonal_dose.csv")
fig, ax = plt.subplots(figsize=(5.4, 3.7))
x = np.arange(len(DR)); y = 100 * DR.S30_share.values
ax.bar(x, y, color=["#9ecae1", "#9ecae1", "#6baed6", "#fd8d3c", "#e6550d", "#a63603"], width=0.7)
ax.errorbar(x, y, yerr=[y - 100 * DR.lo.values, 100 * DR.hi.values - y], fmt="none", ecolor="k", capsize=3, lw=1)
for xi, (_, r) in zip(x, DR.iterrows()):
    ax.text(xi, 100 * r.hi + 0.8, f"n={int(r.tracts):,}", ha="center", fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels(DR.bin); ax.set_xlabel("seasonal/recreational share of the tract's housing units (ACS B25004)", fontsize=8.5)
ax.set_ylabel("% of dwellings behind a single link\nserving >=30 dwellings (S30)", fontsize=8.5)
ax.set_title("Dose-response: resort-type tracts carry 2-3x the exposure\n(5 regions, 9,712 tracts; 95% tract-bootstrap CI)", fontsize=9)
fig.tight_layout(pad=1.2); from figlabels import qa; qa(fig, "fig4"); fig.savefig(f"{LANE}/figs/fig4_seasonal.png", dpi=170, bbox_inches="tight", pad_inches=0.06); print("wrote fig4_seasonal.png")
