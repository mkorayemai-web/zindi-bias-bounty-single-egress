"""County-clustered bootstrap for the headline contrasts (conservative: tracts of one county are spatially correlated, so the unit of resampling is the county).
usage: county_boot.py [BOOT] -> tables/county_boot.csv
Pooled raw ratio of dwelling-weighted S30 shares, group a vs group b, resampling COUNTIES (all five regions together) with replacement. Groups:
 rural vs urban; SVI Q4 vs Q1 and CVI Q4 vs Q1 and WHP Q4 vs Q1 (quartiles within region); resort-type (>=10% seasonal housing) vs other; mobile-home share Q4 vs Q1 (within region); tribal vs not."""
import sys, numpy as np, pandas as pd
from common import *
B = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
rng = np.random.default_rng(SEED)
S = pd.read_parquet(f"{REPO_ROOT}/ext/acs_b25004_seasonal.parquet"); X = pd.read_parquet(f"{REPO_ROOT}/ext/acs_tract_ext.parquet")[["GEOID", "mh_share"]]
DS = []
for region in regions_for("drv_A"):
    T = pd.read_parquet(f"{WORK}/{region}_drv_A_tract.parquet").reset_index(names="GEOID")
    st = pd.read_parquet(strata(region), columns=["GEOID", "ur_class", "svi_overall", "cvi_overall", "usfs_WHP_mean", "tribal_any"])
    hu = pd.read_parquet(f"{WORK}/{region}_tracts.parquet")[["GEOID", "housing_units"]]
    D = st.merge(T, on="GEOID").merge(S, on="GEOID", how="left").merge(X, on="GEOID", how="left").merge(hu, on="GEOID", how="left")
    D = D[(D.eq_den > 0) & (D.housing_units > 0)].copy(); D["region"] = region
    D["seas"] = D.seasonal_units / D.housing_units
    for c in ("svi_overall", "cvi_overall", "usfs_WHP_mean", "mh_share"):
        q = D[c].rank(method="first", pct=True); D[c + "_q"] = np.select([q <= 0.25, q > 0.75], ["Q1", "Q4"], "mid")
    DS.append(D)
A = pd.concat(DS, ignore_index=True); A["county5"] = A.GEOID.str[:5]
CON = {"Rural vs urban": (A.ur_class == "Rural", A.ur_class == "Urban"), "SVI Q4 vs Q1": (A.svi_overall_q == "Q4", A.svi_overall_q == "Q1"),
       "CVI Q4 vs Q1": (A.cvi_overall_q == "Q4", A.cvi_overall_q == "Q1"), "Wildfire hazard Q4 vs Q1 (raw)": (A.usfs_WHP_mean_q == "Q4", A.usfs_WHP_mean_q == "Q1"),
       "Resort-type (>=10% seasonal) vs other": (A.seas >= 0.10, A.seas < 0.10), "Mobile-home share Q4 vs Q1": (A.mh_share_q == "Q4", A.mh_share_q == "Q1"),
       "Tribal vs non-tribal": (A.tribal_any.astype(bool), ~A.tribal_any.astype(bool))}
cty = A.groupby("county5").apply(lambda g: pd.Series({k: [(g.eq_s30 * g.eq_den * m.loc[g.index]).sum() for m in (CON[k][0], CON[k][1])] + [(g.eq_den * m.loc[g.index]).sum() for m in (CON[k][0], CON[k][1])] for k in CON}), include_groups=False)
rows = []
n = len(cty)
for k in CON:
    arr = np.array(cty[k].tolist())               # columns: num_a, num_b, den_a, den_b per county
    base = (arr[:, 0].sum() / arr[:, 2].sum()) / (arr[:, 1].sum() / arr[:, 3].sum())
    idx = rng.integers(0, n, size=(B, n))
    bs = []
    for r in idx:
        s = arr[r].sum(axis=0); bs.append((s[0] / s[2]) / (s[1] / s[3]))
    bs = np.array(bs)
    rows.append(dict(contrast=k, counties=n, ratio=base, lo=np.nanpercentile(bs, 2.5), hi=np.nanpercentile(bs, 97.5), share_a=arr[:, 0].sum() / arr[:, 2].sum(), share_b=arr[:, 1].sum() / arr[:, 3].sum()))
R = pd.DataFrame(rows); R.to_csv(f"{OUT}/county_boot.csv", index=False)
pd.set_option("display.width", 200); print(R.round(3).to_string(index=False))
