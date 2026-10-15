"""Dissociation test vs the road-DENSITY entries (forum 35157/35081): does road density (km / 100 km2, km / 1,000 residents) predict single-link exposure (S30)?
usage: density_dissoc.py -> tables/density_dissoc.csv, tables/density_dissoc_regress.csv   (needs work/cb_<region>_link.parquet: total drivable km per tract = S30_L + oth_L, independent of the S30 flag)
Tract-level: Spearman(S30 share, density) per region and pooled; and WLS S30 ~ seasonal share + mobile-home share + log road density + controls + county FE, with and without the density term."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy.stats import spearmanr
from common import *
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
S = pd.read_parquet(f"{LANE}/ext/acs_b25004_seasonal.parquet"); X = pd.read_parquet(f"{LANE}/ext/acs_tract_ext.parquet")[["GEOID", "mh_share"]]
DS = []
for region in regions_for("drv_A"):
    T = pd.read_parquet(f"{WORK}/{region}_drv_A_tract.parquet").reset_index(names="GEOID")
    st = pd.read_parquet(strata(region), columns=["GEOID", "ALAND", "pop_total", "ur_class", "svi_overall", "cvi_overall", "usfs_WHP_mean"])
    hu = pd.read_parquet(f"{WORK}/{region}_tracts.parquet")[["GEOID", "housing_units"]]
    L = pd.read_parquet(f"{WORK}/cb_{region}_link.parquet"); L["len"] = L.S30_L + L.oth_L; L = L.groupby("GEOID", as_index=False).len.sum()
    D = st.merge(T, on="GEOID").merge(L, on="GEOID", how="left").merge(S, on="GEOID", how="left").merge(X, on="GEOID", how="left").merge(hu, on="GEOID", how="left")
    D = D[(D.eq_den > 0) & (D.housing_units > 0) & (D.ALAND > 0)].copy(); D["len"] = D.len.fillna(0.0)
    D["km100"] = (D.len / 1000) / (D.ALAND / 1e6 / 100)                     # km per 100 km2
    D["km1000"] = np.where(D.pop_total > 0, (D.len / 1000) / (D.pop_total / 1000), np.nan)
    D["lkm100"] = np.log(D.km100 + 1); D["ldens"] = np.log((D.pop_total + 1) / (D.ALAND / 1e6)); D["urban"] = (D.ur_class == "Urban").astype(int)
    D["seas"] = D.seasonal_units / D.housing_units; D["region"] = region; D["county5"] = D.GEOID.str[:5]
    for c in ("usfs_WHP_mean", "svi_overall", "cvi_overall"): D[c + "_z"] = (D[c] - D[c].mean()) / D[c].std()
    DS.append(D)
ALL = pd.concat(DS, ignore_index=True)
rows = []
for name, D in [(d.region.iloc[0], d) for d in DS] + [("pooled", ALL)]:
    for sub, m in (("all tracts", np.ones(len(D), bool)), ("rural", (D.ur_class == "Rural").values), ("urban", (D.ur_class == "Urban").values)):
        d = D[m].dropna(subset=["eq_s30", "km100"])
        r1 = spearmanr(d.eq_s30, d.km100).statistic; d2 = d.dropna(subset=["km1000"]); r2 = spearmanr(d2.eq_s30, d2.km1000).statistic
        rows.append(dict(group=name, subset=sub, tracts=len(d), spearman_S30_vs_km_per_100km2=r1, spearman_S30_vs_km_per_1000_residents=r2))
R = pd.DataFrame(rows); R.to_csv(f"{OUT}/density_dissoc.csv", index=False); print(R.round(3).to_string(index=False))
reg = []
for gname, D in [("pooled", ALL)] + [(d.region.iloc[0], d) for d in DS]:
    D = D.dropna(subset=["seas", "mh_share", "lkm100", "ldens", "usfs_WHP_mean_z", "svi_overall_z", "cvi_overall_z"]).reset_index(drop=True)
    for spec, f in [("without density", "eq_s30 ~ seas + mh_share + ldens + urban + usfs_WHP_mean_z + svi_overall_z + cvi_overall_z + C(county5)"),
                    ("with log road density", "eq_s30 ~ seas + mh_share + lkm100 + ldens + urban + usfs_WHP_mean_z + svi_overall_z + cvi_overall_z + C(county5)")]:
        m = smf.wls(f, data=D, weights=D.eq_den).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(D.county5)[0]}); ci = m.conf_int()
        for t, sc, unit in (("seas", 0.1, "pp S30 per +10 pp seasonal share"), ("mh_share", 0.1, "pp S30 per +10 pp mobile-home share")) + ((("lkm100", 1.0, "pp S30 per +1 log-unit road density"),) if "lkm100" in f else ()):
            reg.append(dict(group=gname, spec=spec, term=t, pp=100 * sc * m.params[t], lo=100 * sc * ci.loc[t, 0], hi=100 * sc * ci.loc[t, 1], unit=unit, n=len(D)))
RG = pd.DataFrame(reg); RG.to_csv(f"{OUT}/density_dissoc_regress.csv", index=False); print(RG[RG.group == "pooled"].round(2).to_string(index=False))
