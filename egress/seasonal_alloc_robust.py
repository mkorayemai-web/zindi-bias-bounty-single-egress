"""Finding 2 robustness: does the peak-load multiplier survive when the tract-uniform allocation of seasonal units is (nearly) exact?
The draft allocates a tract's seasonal units to a single-link cluster in proportion to the cluster's dwellings (cluster dwellings x tract seasonal share). That is exact only if the cluster looks like its tract.
Restriction: keep clusters that serve at least a share c of their own tract's housing units (c = 0, 0.25, 0.5, 0.75): for c -> 1 the cluster IS the tract and the allocation needs no assumption.
tract housing units = ACS B25004 seasonal units / seasonal share (the share was computed against B25001, see seasonal2.py).
usage: seasonal_alloc_robust.py -> tables/seasonal_alloc_robust.csv (+ stdout). q = 1.2 / observed year-round persons per dwelling in <2 % seasonal clusters / 3.5 (assumption range, as seasonal_load.py)."""
import sys, numpy as np, pandas as pd
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
C = pd.read_csv(f"{OUT}/seasonal_clusters.csv", dtype={"tract": str}); C = C[(C.load_dwell >= 100) & C.seas_share.notna() & (C.load_persons > 0)].copy()
T = pd.read_parquet(f"{LANE}/ext/acs_b25004_seasonal.parquet")[["GEOID", "seasonal_units"]].rename(columns={"GEOID": "tract", "seasonal_units": "tract_seasonal_units"})
T["tract"] = T.tract.astype(str).str[-11:]
C = C.merge(T, on="tract", how="left")
C["tract_hu"] = np.where(C.seas_share > 0, C.tract_seasonal_units / C.seas_share, np.nan)
C["coverage"] = C.load_dwell / C.tract_hu
base = C[C.seas_share < 0.02]; PPD0 = base.load_persons.sum() / base.load_dwell.sum(); Q = {"low": 1.2, "mid": round(PPD0, 2), "high": 3.5}
C["seasonal_units"] = C.load_dwell * C.seas_share
for k, q in Q.items(): C[f"peak_{k}"] = C.load_persons + C.seasonal_units * q
hi = C[C.seas_share >= 0.25].copy()
print(f"scenarios q={Q}; clusters in >=25 % seasonal tracts: {len(hi)}; tract housing units recovered for {hi.tract_hu.notna().sum()}; coverage quartiles {hi.coverage.quantile([.25, .5, .75]).round(2).tolist()}; max {hi.coverage.max():.2f}")
rng = np.random.default_rng(SEED); rows = []
for c in [0, 0.25, 0.5, 0.75]:
    d = hi[hi.coverage >= c] if c > 0 else hi
    if len(d) == 0: continue
    r = dict(min_coverage=c, clusters=len(d), counties=d.county.nunique(), dwellings=d.load_dwell.sum(), census_persons=d.load_persons.sum(), ppd_census=d.load_persons.sum() / d.load_dwell.sum())
    for k in Q: r[f"peak_{k}"] = d[f"peak_{k}"].sum(); r[f"x_{k}"] = r[f"peak_{k}"] / r["census_persons"]
    cty = d.groupby("county")[["load_persons", "peak_low", "peak_mid", "peak_high"]].sum().values; n = len(cty); bs = []
    for _ in range(3000):
        s = cty[rng.integers(0, n, n)].sum(0); bs.append((s[1] / s[0], s[2] / s[0], s[3] / s[0]))
    bs = np.array(bs); r.update({f"x_{k}_lo": np.percentile(bs[:, i], 2.5) for i, k in enumerate(Q)}); r.update({f"x_{k}_hi": np.percentile(bs[:, i], 97.5) for i, k in enumerate(Q)}); rows.append(r)
R = pd.DataFrame(rows); R.to_csv(f"{OUT}/seasonal_alloc_robust.csv", index=False)
pd.set_option("display.width", 220)
print(R[["min_coverage", "clusters", "counties", "census_persons", "ppd_census", "x_low", "x_mid", "x_high", "x_low_lo", "x_mid_lo", "x_mid_hi", "x_high_hi"]].round(2).to_string(index=False))
print(f"reference: <2 % seasonal clusters census persons per dwelling {PPD0:.2f}")
