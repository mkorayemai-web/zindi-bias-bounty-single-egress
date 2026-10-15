"""Facility-type contrasts: for each facility kind, is the facility more often behind a single link than the dwellings of its own census tract?
usage: fac_stats.py TAG [BOOT]       TAG e.g. drv_A | drvplus_A   (needs tables/fac_<region>_<TAG>.csv and work/<region>_<TAG>_tract.parquet)
Paired design: indicator for facility f (single route AND >=T dwellings behind its worst link) minus the dwelling-weighted tract share of the same tract.
Cluster bootstrap over tracts (seeded). Writes tables/fac_stats_<TAG>.csv."""
import sys, numpy as np, pandas as pd
from common import *
TAG = sys.argv[1]; B = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
rng = np.random.default_rng(SEED)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
FS = []
for region in regions_for(TAG):
    try:
        F = pd.read_csv(f"{OUT}/fac_{region}_{TAG}.csv", dtype={"tract": str})
        T = pd.read_parquet(f"{WORK}/{region}_{TAG}_tract.parquet")
    except FileNotFoundError:
        print("missing", region); continue
    if "eq_den" not in T.columns:
        continue
    T = T.reset_index(names="tract")[["tract", "eq_spof", "eq_s30", "eq_s100", "eq_s300", "eq_den"]]
    F = F[(F.dist_m <= 500) & F.tract.notna()].merge(T, on="tract", how="inner")
    F["region"] = region
    F["f_single"] = (F.egress == 1).astype(float)
    F["f_s30"] = ((F.egress == 1) & (F.load_dwell >= 30)).astype(float)
    F["f_s100"] = ((F.egress == 1) & (F.load_dwell >= 100)).astype(float)
    F["f_s300"] = ((F.egress == 1) & (F.load_dwell >= 300)).astype(float)
    FS.append(F)
F = pd.concat(FS, ignore_index=True)
rows = []
PAIRS = [("single route", "f_single", "eq_spof"), ("S30", "f_s30", "eq_s30"), ("S100", "f_s100", "eq_s100"), ("S300", "f_s300", "eq_s300")]
for kind in ["mobile_home_park", "campground_rv", "senior_care", "childcare", "school", "dialysis", "hospital", "fire", "ems", "police", "shelter_housing"]:
    for grp in regions_for(TAG) + ["pooled"]:
        d = F[(F.kind == kind)] if grp == "pooled" else F[(F.kind == kind) & (F.region == grp)]
        if len(d) < 15:
            continue
        key = (d.region + "|" + d.tract).values
        uk, inv = np.unique(key, return_inverse=True)
        for mname, fc, bc in PAIRS:
            f = d[fc].values; b = d[bc].values
            # per-cluster sums
            sf = np.bincount(inv, weights=f); sb = np.bincount(inv, weights=b); nn = np.bincount(inv)
            k = len(uk)
            cnt = rng.multinomial(k, np.ones(k) / k, size=B).astype(float)
            m_f = (cnt @ sf) / (cnt @ nn); m_b = (cnt @ sb) / (cnt @ nn)
            rows.append(dict(kind=kind, group=grp, metric=mname, n_fac=len(d), n_tracts=k, fac_share=f.mean(), tract_share=b.mean(), diff_pp=100 * (f.mean() - b.mean()),
                             diff_lo=100 * np.percentile(m_f - m_b, 2.5), diff_hi=100 * np.percentile(m_f - m_b, 97.5),
                             ratio=f.mean() / b.mean() if b.mean() > 0 else np.nan,
                             ratio_lo=np.nanpercentile(m_f / np.where(m_b > 0, m_b, np.nan), 2.5), ratio_hi=np.nanpercentile(m_f / np.where(m_b > 0, m_b, np.nan), 97.5)))
R = pd.DataFrame(rows)
R.to_csv(f"{OUT}/fac_stats_{TAG}.csv", index=False)
print(R[(R.metric == "S30")][["kind", "group", "n_fac", "n_tracts", "fac_share", "tract_share", "diff_pp", "diff_lo", "diff_hi", "ratio", "ratio_lo", "ratio_hi"]].round(3).to_string(index=False))
