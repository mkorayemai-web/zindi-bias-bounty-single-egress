"""County-clustered bootstrap for the facility rows of the effect-size figure (draft Fig. 5): same paired design as fac_stats.py (facility indicator = single route AND >=30 dwellings
behind its worst link, minus the dwelling-weighted S30 share of the facility's own tract), but the resampling unit is the COUNTY (tracts of one county are spatially correlated), as in county_boot.py.
usage: county_boot_facilities.py [BOOT] -> tables/county_boot_facilities.csv   (needs tables/fac_<region>_drv_A.csv and work/<region>_drv_A_tract.parquet; asserts that the point estimates equal tables/fac_stats_drv_A.csv)"""
import sys, numpy as np, pandas as pd
from common import *
B = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
rng = np.random.default_rng(SEED)
FS = []
for region in regions_for("drv_A"):
    F = pd.read_csv(f"{OUT}/fac_{region}_drv_A.csv", dtype={"tract": str}); T = pd.read_parquet(f"{WORK}/{region}_drv_A_tract.parquet")
    if "eq_s30" not in T.columns: continue
    T = T.reset_index(names="tract")[["tract", "eq_s30"]]
    F = F[(F.dist_m <= 500) & F.tract.notna()].merge(T, on="tract", how="inner")
    F["f_s30"] = ((F.egress == 1) & (F.load_dwell >= 30)).astype(float); F["county"] = F.tract.str[:5]; FS.append(F)
F = pd.concat(FS, ignore_index=True)
FST = pd.read_csv(f"{OUT}/fac_stats_drv_A.csv"); rows = []
for kind in ["mobile_home_park", "school", "hospital", "fire", "senior_care"]:
    d = F[F.kind == kind]
    uk, inv = np.unique(d.county.values, return_inverse=True); k = len(uk)
    sf = np.bincount(inv, weights=d.f_s30.values); sb = np.bincount(inv, weights=d.eq_s30.values); nn = np.bincount(inv)
    cnt = rng.multinomial(k, np.ones(k) / k, size=B).astype(float)
    m_f = (cnt @ sf) / (cnt @ nn); m_b = (cnt @ sb) / (cnt @ nn); r = m_f / np.where(m_b > 0, m_b, np.nan)
    ratio = d.f_s30.mean() / d.eq_s30.mean()
    ref = FST[(FST.kind == kind) & (FST.group == "pooled") & (FST.metric == "S30")].iloc[0]
    assert abs(ratio - ref.ratio) < 1e-9 and len(d) == ref.n_fac, (kind, ratio, ref.ratio, len(d), ref.n_fac)     # same point estimate as fac_stats.py
    rows.append(dict(kind=kind, counties=k, n_fac=len(d), fac_share=d.f_s30.mean(), tract_share=d.eq_s30.mean(), ratio=ratio, lo=np.nanpercentile(r, 2.5), hi=np.nanpercentile(r, 97.5)))
R = pd.DataFrame(rows); R.to_csv(f"{OUT}/county_boot_facilities.csv", index=False)
print(R.round(3).to_string(index=False))
