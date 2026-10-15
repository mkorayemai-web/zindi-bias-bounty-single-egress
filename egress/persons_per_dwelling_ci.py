"""Persons per dwelling behind single links by seasonal share of the tract (Finding 2 evidence). usage: persons_per_dwelling_ci.py
Inputs: tables/seasonal_clusters.csv (single-link clusters >= 100 dwellings; seasonal2.py). Outputs: tables/persons_per_dwelling_by_seasonal.csv (pooled by seasonal-share bin),
tables/persons_per_dwelling_ci.csv (>= 25 % vs < 2 % seasonal tracts, county-clustered bootstrap 95 % CI, seeded)."""
import sys, numpy as np, pandas as pd
from scipy.stats import spearmanr
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
C = pd.read_csv(f"{OUT}/seasonal_clusters.csv", dtype={"tract": str}); C = C[(C.load_dwell >= 100) & C.seas_share.notna() & (C.load_persons > 0)].copy()
C["ppd"] = C.load_persons / C.load_dwell
bins = [-0.001, 0.02, 0.05, 0.10, 0.25, 1.01]; lab = ["<2%", "2-5%", "5-10%", "10-25%", ">=25%"]
C["bin"] = pd.cut(C.seas_share, bins=bins, labels=lab)
g = C.groupby("bin", observed=False).apply(lambda d: pd.Series({"clusters": len(d), "dwellings": d.load_dwell.sum(), "persons": d.load_persons.sum(), "persons_per_dwelling_pooled": d.load_persons.sum() / d.load_dwell.sum(), "median_ppd": d.ppd.median()}), include_groups=False)
g.to_csv(f"{OUT}/persons_per_dwelling_by_seasonal.csv"); print(g.round(2).to_string())
rho, p = spearmanr(C.seas_share, C.ppd); print(f"Spearman(tract seasonal share, persons per dwelling) = {rho:.2f} (p={p:.1e}, n={len(C)} clusters)")
C["hi"] = C.seas_share >= 0.25; C["lo"] = C.seas_share < 0.02
rng = np.random.default_rng(SEED)
cty = C.groupby("county").apply(lambda d: pd.Series({"p_hi": d.load_persons[d.hi].sum(), "d_hi": d.load_dwell[d.hi].sum(), "p_lo": d.load_persons[d.lo].sum(), "d_lo": d.load_dwell[d.lo].sum()}), include_groups=False)
a = cty.values; n = len(a); base = (a[:, 0].sum() / a[:, 1].sum(), a[:, 2].sum() / a[:, 3].sum()); bs = []
for _ in range(4000):
    s = a[rng.integers(0, n, n)].sum(0)
    if s[1] > 0 and s[3] > 0: bs.append((s[0] / s[1], s[2] / s[3], (s[0] / s[1]) / (s[2] / s[3])))
bs = np.array(bs); q = lambda j, x: np.percentile(bs[:, j], x)
R = dict(hi_ppd=base[0], hi_lo=q(0, 2.5), hi_hi=q(0, 97.5), lo_ppd=base[1], lo_lo=q(1, 2.5), lo_hi=q(1, 97.5), ratio=base[0] / base[1], ratio_lo=q(2, 2.5), ratio_hi=q(2, 97.5), counties=n, spearman=rho, clusters=len(C))
pd.DataFrame([R]).to_csv(f"{OUT}/persons_per_dwelling_ci.csv", index=False)
print(f">=25% seasonal tracts {R['hi_ppd']:.2f} ({R['hi_lo']:.2f}-{R['hi_hi']:.2f}) vs <2% {R['lo_ppd']:.2f} ({R['lo_lo']:.2f}-{R['lo_hi']:.2f}); ratio {R['ratio']:.2f} ({R['ratio_lo']:.2f}-{R['ratio_hi']:.2f}); {n} counties")
