"""Tract-level triangulation of the mobile-home finding with ACS B25024/B25044 (extra public data, ext/acs_tract_ext.parquet) and the no-vehicle estimate.
usage: mh_tract.py TAG [BOOT]    (reads work/<region>_<TAG>_tract.parquet)
Outputs tables/mh_tract_<TAG>.csv (quartile contrast + regression) and tables/nocar_<TAG>.csv"""
import sys, numpy as np, pandas as pd, statsmodels.formula.api as smf
from common import *
TAG = sys.argv[1]; B = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
rng = np.random.default_rng(SEED)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
EXT = f"{REPO_ROOT}/ext/acs_tract_ext.parquet"
A = pd.read_parquet(EXT)
DS = []
for region in regions_for(TAG):
    T = pd.read_parquet(f"{WORK}/{region}_{TAG}_tract.parquet")
    if "eq_den" not in T.columns:
        continue
    T = T.reset_index(names="GEOID")
    st = pd.read_parquet(strata(region), columns=["GEOID", "ALAND", "pop_total", "ur_class", "svi_overall", "cvi_overall", "usfs_WHP_mean", "tribal_any"])
    D = st.merge(T, on="GEOID").merge(A, on="GEOID", how="left")
    D = D[(D.eq_den > 0) & D.mh_share.notna()].copy()
    D["region"] = region; D["county5"] = D.GEOID.str[:5]
    D["mh_q"] = pd.qcut(D.mh_share.rank(method="first"), 4, labels=["Q1", "Q2", "Q3", "Q4"])
    D["ldens"] = np.log((D.pop_total + 1) / (D.ALAND / 1e6)); D["urban"] = (D.ur_class == "Urban").astype(int); D["tribal"] = D.tribal_any.astype(int)
    D["WHP_z"] = (D.usfs_WHP_mean - D.usfs_WHP_mean.mean()) / D.usfs_WHP_mean.std()
    D["svi_z"] = (D.svi_overall - D.svi_overall.mean()) / D.svi_overall.std()
    D["cvi_z"] = (D.cvi_overall - D.cvi_overall.mean()) / D.cvi_overall.std()
    DS.append(D)
rows = []
def boot_share(D, mask, col="eq_s30", den="eq_den"):
    a = mask.values.astype(float); num = (D[col] * D[den]).values; dn = D[den].values; n = len(D)
    cnt = rng.multinomial(n, np.ones(n) / n, size=B).astype(float)
    return (num * a).sum() / (dn * a).sum(), (cnt @ (num * a)) / (cnt @ (dn * a))
for D in DS + [None]:
    grp = "pooled" if D is None else D.region.iloc[0]
    if D is None:
        Wt = sum(d.eq_den.sum() for d in DS)
        res = {}
        for q in ("Q1", "Q4"):
            parts = [(d.eq_den.sum(), *boot_share(d, d.mh_q == q)) for d in DS]
            res[q] = (sum(p[0] * p[1] for p in parts) / Wt, sum(p[0] * p[2] for p in parts) / Wt)
    else:
        res = {q: boot_share(D, D.mh_q == q) for q in ("Q1", "Q4")}
    s1, b1 = res["Q1"]; s4, b4 = res["Q4"]
    r = b4 / b1
    rows.append(dict(group=grp, test="S30 by tract mobile-home-share quartile (Q4 vs Q1)", share_q1=s1, share_q4=s4, ratio=s4 / s1, ratio_lo=np.percentile(r, 2.5), ratio_hi=np.percentile(r, 97.5)))
CT = pd.DataFrame(rows)
print(CT.round(3).to_string(index=False))
reg = []
for grp in [d.region.iloc[0] for d in DS] + ["pooled"]:
    D = pd.concat(DS) if grp == "pooled" else next(d for d in DS if d.region.iloc[0] == grp)
    D = D.dropna(subset=["mh_share", "ldens", "urban", "WHP_z", "svi_z", "cvi_z", "eq_s30"]).reset_index(drop=True)
    for spec, f in [("alone", "eq_s30 ~ mh_share"), ("+ density/urban/WHP/SVI/CVI", "eq_s30 ~ mh_share + ldens + urban + WHP_z + svi_z + cvi_z"),
                    ("+ controls + county FE", "eq_s30 ~ mh_share + ldens + urban + WHP_z + svi_z + cvi_z + C(county5)")]:
        m = smf.wls(f, data=D, weights=D.eq_den).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(D.county5)[0]})
        ci = m.conf_int()
        # coefficient = change in S30 share (0-1 scale) per +1.0 of mobile-home share; report percentage points of S30 per +10 pp of mobile homes
        reg.append(dict(group=grp, spec=spec, pp_S30_per_10pp_mh=100 * 0.1 * m.params["mh_share"], lo=100 * 0.1 * ci.loc["mh_share", 0], hi=100 * 0.1 * ci.loc["mh_share", 1], n=len(D)))
RG = pd.DataFrame(reg)
print(RG.round(3).to_string(index=False))
pd.concat([CT.assign(kind="quartile"), RG.assign(kind="regression")]).to_csv(f"{OUT}/mh_tract_{TAG}.csv", index=False)
nc = []
for D in DS:
    for gname, m in [("all", D.eq_den > 0), ("WHP top quartile", D.usfs_WHP_mean >= D.usfs_WHP_mean.quantile(0.75))]:
        d = D[m]
        nc.append(dict(region=D.region.iloc[0], subset=gname, nocar_hh=d.nocar_hh.sum(), nocar_hh_in_S30=(d.nocar_hh * d.eq_s30).sum(), nocar_hh_in_S100=(d.nocar_hh * d.eq_s100).sum(),
                       nocar_hh_single=(d.nocar_hh * d.eq_spof).sum(), nocar_share=d.nocar_hh.sum() / d.occ_hh.sum()))
NC = pd.DataFrame(nc); NC.to_csv(f"{OUT}/nocar_{TAG}.csv", index=False)
print(NC.round(1).to_string(index=False))
