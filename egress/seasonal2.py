"""Seasonal-housing follow-up: dose-response, joint model with mobile-home share, rural-only check, named clusters with seasonal units behind the link.
usage: seasonal2.py [BOOT]   (needs seasonal.py outputs: ext/acs_b25004_seasonal.parquet; ext/acs_tract_ext.parquet; tables/<region>_drv_A_links.csv)
Writes tables/seasonal_dose.csv, tables/seasonal_joint.csv, tables/seasonal_clusters.csv"""
import sys, numpy as np, pandas as pd, statsmodels.formula.api as smf
from common import *
B = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
rng = np.random.default_rng(SEED)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 38)
S = pd.read_parquet(f"{REPO_ROOT}/ext/acs_b25004_seasonal.parquet"); X = pd.read_parquet(f"{REPO_ROOT}/ext/acs_tract_ext.parquet")[["GEOID", "mh_share"]]
cn = pd.read_csv(f"{REPO_ROOT}/ext/national_county2020.txt", sep="|", dtype=str); cn["code"] = cn.STATEFP + cn.COUNTYFP
CNAME = dict(zip(cn.code, cn.COUNTYNAME + ", " + cn.STATE))
DS = []
for region in regions_for("drv_A"):
    T = pd.read_parquet(f"{WORK}/{region}_drv_A_tract.parquet").reset_index(names="GEOID")
    st = pd.read_parquet(strata(region), columns=["GEOID", "ALAND", "pop_total", "ur_class", "svi_overall", "cvi_overall", "usfs_WHP_mean", "tribal_any"])
    hu = pd.read_parquet(f"{WORK}/{region}_tracts.parquet")[["GEOID", "housing_units"]]
    D = st.merge(T, on="GEOID").merge(S, on="GEOID", how="left").merge(X, on="GEOID", how="left").merge(hu, on="GEOID", how="left")
    D = D[(D.eq_den > 0) & (D.housing_units > 0)].copy()
    D["seas_share"] = D.seasonal_units / D.housing_units; D["region"] = region; D["county5"] = D.GEOID.str[:5]
    D["ldens"] = np.log((D.pop_total + 1) / (D.ALAND / 1e6)); D["urban"] = (D.ur_class == "Urban").astype(int)
    for c in ("usfs_WHP_mean", "svi_overall", "cvi_overall"): D[c + "_z"] = (D[c] - D[c].mean()) / D[c].std()
    DS.append(D)
ALL = pd.concat(DS, ignore_index=True)
# ---- dose response (pooled, dwelling-weighted S30 by seasonal-share bin, cluster bootstrap over tracts within region)
bins = [-0.001, 0.02, 0.05, 0.10, 0.25, 0.50, 1.01]; labels = ["<2%", "2-5%", "5-10%", "10-25%", "25-50%", ">=50%"]
ALL["bin"] = pd.cut(ALL.seas_share, bins=bins, labels=labels)
rows = []
for lab in labels:
    num = den = 0.0; bs = []
    sub = ALL[ALL.bin == lab]
    for _ in range(B):
        idx = rng.integers(0, len(sub), len(sub)); d = sub.iloc[idx]; bs.append((d.eq_s30 * d.eq_den).sum() / d.eq_den.sum())
    rows.append(dict(bin=lab, tracts=len(sub), dwellings=sub.eq_den.sum(), S30_share=(sub.eq_s30 * sub.eq_den).sum() / sub.eq_den.sum(), lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5),
                     single_route=(sub.eq_spof * sub.eq_den).sum() / sub.eq_den.sum()))
DR = pd.DataFrame(rows); DR.to_csv(f"{OUT}/seasonal_dose.csv", index=False); print(DR.round(4).to_string(index=False))
# ---- rural-only ratio and joint model
RU = []                                  # saved to tables/seasonal_rural_urban.csv (was stdout-only)
for name, sub in [("rural tracts only", ALL[ALL.ur_class == "Rural"]), ("urban tracts only", ALL[ALL.ur_class == "Urban"])]:
    hi = sub[sub.seas_share >= 0.10]; lo_ = sub[sub.seas_share < 0.10]
    r = [(hi.iloc[i].eq_s30 if False else None) for i in range(0)]
    f = lambda d: (d.eq_s30 * d.eq_den).sum() / d.eq_den.sum()
    bs = []
    for _ in range(B):
        a = hi.iloc[rng.integers(0, len(hi), len(hi))]; b = lo_.iloc[rng.integers(0, len(lo_), len(lo_))]; bs.append(f(a) / f(b))
    print(f"{name}: S30 resort-type (>=10% seasonal) {f(hi):.3f} (n={len(hi)}) vs other {f(lo_):.3f} -> ratio {f(hi)/f(lo_):.2f} (95% {np.percentile(bs,2.5):.2f}-{np.percentile(bs,97.5):.2f})")
    RU.append(dict(subset=name, n_resort=len(hi), n_other=len(lo_), S30_resort=f(hi), S30_other=f(lo_), ratio=f(hi) / f(lo_), ratio_lo=np.percentile(bs, 2.5), ratio_hi=np.percentile(bs, 97.5), boot=B))
pd.DataFrame(RU).to_csv(f"{OUT}/seasonal_rural_urban.csv", index=False)
J = []
for gname, D in [(d.region.iloc[0], d) for d in DS] + [("pooled", ALL)]:
    D = D.dropna(subset=["seas_share", "mh_share", "ldens", "usfs_WHP_mean_z", "svi_overall_z", "cvi_overall_z"]).reset_index(drop=True)
    f = "eq_s30 ~ seas_share + mh_share + ldens + urban + usfs_WHP_mean_z + svi_overall_z + cvi_overall_z + C(county5)"
    m = smf.wls(f, data=D, weights=D.eq_den).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(D.county5)[0]}); ci = m.conf_int()
    for t in ("seas_share", "mh_share", "svi_overall_z", "usfs_WHP_mean_z"):
        sc = 0.1 if t in ("seas_share", "mh_share") else 1.0
        J.append(dict(group=gname, term=t, pp_S30=100 * sc * m.params[t], lo=100 * sc * ci.loc[t, 0], hi=100 * sc * ci.loc[t, 1], unit="per +10 pp share" if sc == 0.1 else "per +1 SD", n=len(D)))
JJ = pd.DataFrame(J); JJ.to_csv(f"{OUT}/seasonal_joint.csv", index=False); print(JJ.round(2).to_string(index=False))
# ---- named clusters with seasonal units behind the link
cl = []
sh = ALL.set_index("GEOID")[["seas_share", "seasonal_units", "housing_units"]]
for region in regions_for("drv_A"):
    L = pd.read_csv(f"{OUT}/{region}_drv_A_links.csv", dtype={"tract": str})
    L = L.merge(sh, left_on="tract", right_index=True, how="left"); L["region"] = region
    L["seasonal_behind_link"] = L.load_dwell * L.seas_share; L["county"] = L.tract.str[:5].map(CNAME)
    cl.append(L)
CL = pd.concat(cl, ignore_index=True)
CL = CL[CL.load_dwell >= 100].sort_values("seasonal_behind_link", ascending=False)
CL[["region", "place", "rname", "cls", "tract", "county", "load_dwell", "load_persons", "seas_share", "seasonal_behind_link", "len_m"]].to_csv(f"{OUT}/seasonal_clusters.csv", index=False)
print(CL.head(25)[["region", "place", "rname", "tract", "county", "load_dwell", "load_persons", "seas_share", "seasonal_behind_link"]].round(2).to_string(index=False))
