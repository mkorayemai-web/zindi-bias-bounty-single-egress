"""Runner-up candidate: SEASONAL / RECREATIONAL housing behind single links (an 'intersection the strata miss': SVI/CVI are built on residents; vacation homes carry no residents in the census
but fill up at peak season - weekend/holiday populations unfamiliar with the roads and towing boats/trailers).
Extra public data: ACS 2020-2024 5-year B25004 (vacancy status; E006 = vacant for seasonal, recreational or occasional use), Census table-based summary file (public domain), retrieved 2026-10-14.
usage: seasonal.py [BOOT]    -> ext/acs_b25004_seasonal.parquet, tables/seasonal_contrasts.csv, tables/seasonal_regress.csv, tables/seasonal_tracts.csv
Seasonal share of a tract = B25004_E006 / B25001 housing units. Dwelling-weighted S30 shares from work/<region>_drv_A_tract.parquet (variants.py)."""
import sys, numpy as np, pandas as pd, statsmodels.formula.api as smf
from common import *
B = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
rng = np.random.default_rng(SEED)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
import os
RAW, PQ = f"{LANE}/ext/acsdt5y2024-b25004.dat", f"{LANE}/ext/acs_b25004_seasonal.parquet"
if os.path.exists(RAW):      # extraction from the national Census file (SOURCES.md row 8); the repository ships the extract (PQ) instead of the 100+ MB raw file
    keep = ("1400000US04", "1400000US06", "1400000US35", "1400000US40", "1400000US48", "1400000US53")
    out = []
    for ch in pd.read_csv(RAW, sep="|", usecols=["GEO_ID", "B25004_E001", "B25004_E006"], dtype=str, chunksize=200000):
        out.append(ch[ch.GEO_ID.str.startswith(keep)])
    A = pd.concat(out); A["GEOID"] = A.GEO_ID.str[-11:]
    A["vacant_total"] = pd.to_numeric(A.B25004_E001, errors="coerce"); A["seasonal_units"] = pd.to_numeric(A.B25004_E006, errors="coerce")
    A = A[["GEOID", "vacant_total", "seasonal_units"]]; A.to_parquet(PQ)
else:
    A = pd.read_parquet(PQ)
cn = pd.read_csv(f"{LANE}/ext/national_county2020.txt", sep="|", dtype=str); cn["code"] = cn.STATEFP + cn.COUNTYFP
CNAME = dict(zip(cn.code, cn.COUNTYNAME + ", " + cn.STATE))
DS = []
for region in regions_for("drv_A"):
    T = pd.read_parquet(f"{WORK}/{region}_drv_A_tract.parquet").reset_index(names="GEOID")
    st = pd.read_parquet(strata(region), columns=["GEOID", "ALAND", "pop_total", "ur_class", "svi_overall", "cvi_overall", "usfs_WHP_mean", "tribal_any"])
    hu = pd.read_parquet(f"{WORK}/{region}_tracts.parquet")[["GEOID", "housing_units"]]
    D = st.merge(T, on="GEOID").merge(A, on="GEOID", how="left").merge(hu, on="GEOID", how="left")
    D = D[(D.eq_den > 0) & (D.housing_units > 0)].copy()
    D["seas_share"] = D.seasonal_units / D.housing_units
    D["region"] = region; D["county5"] = D.GEOID.str[:5]
    D["ldens"] = np.log((D.pop_total + 1) / (D.ALAND / 1e6)); D["urban"] = (D.ur_class == "Urban").astype(int); D["tribal"] = D.tribal_any.astype(int)
    for c in ("usfs_WHP_mean", "svi_overall", "cvi_overall"):
        D[c + "_z"] = (D[c] - D[c].mean()) / D[c].std()
    D["hi_seas"] = D.seas_share >= 0.10                                  # 'resort-type' tracts: >= 10% of housing units seasonal
    DS.append(D)
ALL = pd.concat(DS, ignore_index=True)
print("tracts", len(ALL), "| tracts with >=10% seasonal units:", int(ALL.hi_seas.sum()), "| seasonal units total", int(ALL.seasonal_units.sum()), "of HU", int(ALL.housing_units.sum()))

def boot_ratio(Ds, mask_fn, col="eq_s30", den="eq_den"):
    parts = []
    for D in Ds:
        a = mask_fn(D).values.astype(float); b = 1 - a
        if a.sum() == 0 or b.sum() == 0: continue
        num = (D[col] * D[den]).values; dn = D[den].values; n = len(D)
        cnt = rng.multinomial(n, np.ones(n) / n, size=B).astype(float)
        parts.append((dn.sum(), (cnt @ (num * a)) / (cnt @ (dn * a)), (cnt @ (num * b)) / (cnt @ (dn * b)), (num * a).sum() / (dn * a).sum(), (num * b).sum() / (dn * b).sum()))
    if not parts: return None
    Wt = sum(p[0] for p in parts)
    ba = sum(p[0] * p[1] for p in parts) / Wt; bb = sum(p[0] * p[2] for p in parts) / Wt
    sa = sum(p[0] * p[3] for p in parts) / Wt; sb = sum(p[0] * p[4] for p in parts) / Wt
    r = ba / bb
    return sa, sb, sa / sb, np.percentile(r, 2.5), np.percentile(r, 97.5), (sa - sb) * 100
rows = []
for gname, Ds in [(D.region.iloc[0], [D]) for D in DS] + [("pooled", DS)]:
    for mname, col, den in [("S30 (dwellings)", "eq_s30", "eq_den"), ("S100 (dwellings)", "eq_s100", "eq_den"), ("single route (dwellings)", "eq_spof", "eq_den"), ("S30 (persons)", "eq_ps30", "eq_pden")]:
        res = boot_ratio(Ds, lambda D: D.hi_seas, col, den)
        if res is None: continue
        rows.append(dict(group=gname, metric=mname, share_hi_seasonal=res[0], share_other=res[1], ratio=res[2], ratio_lo=res[3], ratio_hi=res[4], diff_pp=res[5],
                         n_tracts_hi=int(sum(D.hi_seas.sum() for D in Ds))))
CT = pd.DataFrame(rows); CT.to_csv(f"{OUT}/seasonal_contrasts.csv", index=False)
print(CT[CT.metric == "S30 (dwellings)"].round(3).to_string(index=False))
reg = []
for gname, Ds in [(D.region.iloc[0], [D]) for D in DS] + [("pooled", DS)]:
    D = pd.concat(Ds, ignore_index=True).dropna(subset=["seas_share", "ldens", "usfs_WHP_mean_z", "svi_overall_z", "cvi_overall_z"]).reset_index(drop=True)
    for spec, f in [("alone", "eq_s30 ~ seas_share"), ("+ density/urban/WHP/SVI/CVI", "eq_s30 ~ seas_share + ldens + urban + usfs_WHP_mean_z + svi_overall_z + cvi_overall_z"),
                    ("+ controls + county FE", "eq_s30 ~ seas_share + ldens + urban + usfs_WHP_mean_z + svi_overall_z + cvi_overall_z + C(county5)")]:
        m = smf.wls(f, data=D, weights=D.eq_den).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(D.county5)[0]}); ci = m.conf_int()
        reg.append(dict(group=gname, spec=spec, pp_S30_per_10pp_seasonal=100 * 0.1 * m.params["seas_share"], lo=100 * 0.1 * ci.loc["seas_share", 0], hi=100 * 0.1 * ci.loc["seas_share", 1], n=len(D)))
RG = pd.DataFrame(reg); RG.to_csv(f"{OUT}/seasonal_regress.csv", index=False)
print(RG.round(2).to_string(index=False))
# counts: seasonal units behind S30 links (tract-uniform assumption) and the top tracts
ALL["seas_in_s30"] = ALL.eq_nds30 * ALL.seas_share
ALL["county"] = ALL.GEOID.str[:5].map(CNAME)
print("\nseasonal/recreational units estimated behind S30 links (tract-uniform allocation):", int(ALL.seas_in_s30.sum()), "of", int(ALL.eq_nds30.sum()), "S30 dwellings =", round(100 * ALL.seas_in_s30.sum() / ALL.eq_nds30.sum(), 1), "%; all-HU seasonal share", round(100 * ALL.seasonal_units.sum() / ALL.housing_units.sum(), 1), "%")
print(ALL.groupby("region").apply(lambda g: pd.Series({"seasonal_units_in_S30": g.seas_in_s30.sum(), "S30_dwellings": g.eq_nds30.sum(), "share": g.seas_in_s30.sum() / g.eq_nds30.sum()}), include_groups=False).round(3).to_string())
top = ALL.sort_values("seas_in_s30", ascending=False).head(25)[["GEOID", "county", "region", "seas_share", "seasonal_units", "eq_nds30", "seas_in_s30", "eq_s30"]]
top.to_csv(f"{OUT}/seasonal_tracts.csv", index=False)
print(top.round(3).to_string(index=False))
