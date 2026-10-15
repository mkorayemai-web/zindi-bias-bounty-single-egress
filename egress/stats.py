"""Strata contrasts with cluster bootstrap (tracts resampled with replacement within region; seeded) for one configuration.
usage: stats.py TAG [BOOT]        TAG e.g. drv_A | drvplus_A | drv_B | drv_A_r25     (reads work/<region>_<TAG>_tract.parquet for the 4 regions)
Outputs tables/stats_contrasts_<TAG>.csv (+ printed), tables/stats_regress_<TAG>.csv, tables/stats_burden_<TAG>.csv"""
import sys, numpy as np, pandas as pd, statsmodels.formula.api as smf
from common import *
TAG = sys.argv[1]
B = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
S = sys.argv[3] if len(sys.argv) > 3 else "eq"      # weighting scheme: eq (headline) | ar (area-weighted) | str (structure counts)
SUF = "" if S == "eq" else "_" + S
rng = np.random.default_rng(SEED)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
COLS = ["GEOID", "STATEFP", "COUNTYFP", "ALAND", "pop_total", "ur_class", "tribal_any", "svi_overall", "svi_housing_transport", "cvi_overall", "usfs_WHP_mean"]
DS = []
for region in regions_for(TAG):
    T = pd.read_parquet(f"{WORK}/{region}_{TAG}_tract.parquet")
    if f"{S}_den" not in T.columns or "eq_den" not in T.columns:
        print("skip (old schema)", region); continue
    T.index.name = "GEOID"; T = T.reset_index()
    st = pd.read_parquet(strata(region), columns=COLS)
    D = st.merge(T, on="GEOID", how="inner")
    D = D[D[f"{S}_den"] > 0].copy()
    D["region"] = region
    for col in ("svi_overall", "cvi_overall", "usfs_WHP_mean"):
        D[col + "_q"] = pd.qcut(D[col], 4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop")
    D["county5"] = D.GEOID.str[:5]
    DS.append(D)
ALL = pd.concat(DS, ignore_index=True)

CONTRASTS = [
    ("Rural vs Urban", lambda D: D.ur_class == "Rural", lambda D: D.ur_class == "Urban"),
    ("SVI Q4 vs Q1", lambda D: D.svi_overall_q == "Q4", lambda D: D.svi_overall_q == "Q1"),
    ("SVI housing/transport top tercile vs bottom", lambda D: D.svi_housing_transport >= D.svi_housing_transport.quantile(2 / 3), lambda D: D.svi_housing_transport <= D.svi_housing_transport.quantile(1 / 3)),
    ("CVI Q4 vs Q1", lambda D: D.cvi_overall_q == "Q4", lambda D: D.cvi_overall_q == "Q1"),
    ("Tribal vs non-tribal", lambda D: D.tribal_any.astype(bool), lambda D: ~D.tribal_any.astype(bool)),
    ("WHP Q4 vs Q1 (raw)", lambda D: D.usfs_WHP_mean_q == "Q4", lambda D: D.usfs_WHP_mean_q == "Q1"),
]
METRICS = {"S30 (dwellings)": (f"{S}_s30", f"{S}_den"), "S100 (dwellings)": (f"{S}_s100", f"{S}_den"), "single-route any (dwellings)": (f"{S}_spof", f"{S}_den")}
if S == "eq":
    METRICS.update({"S30 (persons)": ("eq_ps30", "eq_pden"), "S100 (persons)": ("eq_ps100", "eq_pden")})

def boot_pair(Ds, fa, fb, col, den, B):
    """Direct standardisation across regions: share_g = sum_r W_r * share_{g,r} / sum_r W_r with W_r = region dwellings (persons for person metrics);
    tracts are resampled with replacement within region (cluster bootstrap). Regions lacking either group are dropped from both sides."""
    parts = []
    for D in Ds:
        a = fa(D).values.astype(float); b = fb(D).values.astype(float)
        if a.sum() == 0 or b.sum() == 0:
            continue
        num = (D[col] * D[den]).values; dn = D[den].values
        n = len(D)
        cnt = rng.multinomial(n, np.ones(n) / n, size=B).astype(float)
        W = dn.sum()
        parts.append((W, (cnt @ (num * a)) / (cnt @ (dn * a)), (cnt @ (num * b)) / (cnt @ (dn * b)), (num * a).sum() / (dn * a).sum(), (num * b).sum() / (dn * b).sum()))
    if not parts:
        return None
    Wt = sum(p[0] for p in parts)
    ba = sum(p[0] * p[1] for p in parts) / Wt; bb = sum(p[0] * p[2] for p in parts) / Wt
    sa0 = sum(p[0] * p[3] for p in parts) / Wt; sb0 = sum(p[0] * p[4] for p in parts) / Wt
    return sa0, sb0, ba, bb

rows = []
RG = [D.region.iloc[0] for D in DS]
groups = [(r, [D]) for r, D in zip(RG, DS)] + [("pooled", DS)]
for cname, fa, fb in CONTRASTS:
    for gname, Ds in groups:
        if cname.startswith("Tribal") and gname == "south-central-tx":
            continue
        for mname, (col, den) in METRICS.items():
            res = boot_pair(Ds, fa, fb, col, den, B)
            if res is None:
                continue
            sa, sb, ba, bb = res
            ratio = ba / np.where(bb > 0, bb, np.nan); diff = ba - bb
            rows.append(dict(contrast=cname, group=gname, metric=mname, share_a=sa, share_b=sb, ratio=sa / sb if sb > 0 else np.nan,
                             ratio_lo=np.nanpercentile(ratio, 2.5), ratio_hi=np.nanpercentile(ratio, 97.5), diff_pp=100 * (sa - sb),
                             diff_lo=100 * np.percentile(diff, 2.5), diff_hi=100 * np.percentile(diff, 97.5)))
CT = pd.DataFrame(rows)
CT.to_csv(f"{OUT}/stats_contrasts_{TAG}{SUF}.csv", index=False)
show = CT[(CT.metric == "S30 (dwellings)")]
print(f"==== {TAG}: S30 share of dwellings behind a single link serving >30 dwellings; a vs b, ratio with 95% cluster-bootstrap CI ====")
print(show[["contrast", "group", "share_a", "share_b", "ratio", "ratio_lo", "ratio_hi", "diff_pp", "diff_lo", "diff_hi"]].round(3).to_string(index=False))

# ---- regressions: tract-level WLS (weights = dwellings), SE clustered by county ---------------------------------------------------------
reg = []
def fit(D, y, spec, label):
    m = smf.wls(f"{y} ~ {spec}", data=D, weights=D[f"{S}_den"]).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(D.county5)[0]})
    ci = m.conf_int()
    return m, ci
for gname, Ds in [(r, [D]) for r, D in zip(RG, DS)] + [("pooled", DS)]:
    D = pd.concat(Ds, ignore_index=True)
    D = D[D.usfs_WHP_mean.notna() & D.svi_overall.notna() & D.cvi_overall.notna()].copy()
    for c in ("usfs_WHP_mean", "svi_overall", "cvi_overall"):
        D[c + "_z"] = D.groupby("region")[c].transform(lambda s: (s - s.mean()) / s.std())
    D["ldens"] = np.log((D.pop_total + 1) / (D.ALAND / 1e6)); D["urban"] = (D.ur_class == "Urban").astype(int); D["tribal"] = D.tribal_any.astype(int)
    D["whp_z"] = D.usfs_WHP_mean_z; D["svi_z"] = D.svi_overall_z; D["cvi_z"] = D.cvi_overall_z
    for y in (f"{S}_s30", f"{S}_s100"):
        base = "ldens + urban + svi_z + cvi_z + tribal + whp_z"
        fe = "C(county5)" if gname != "pooled" else "C(county5)"
        for label, spec in [("naive (each alone)", None), ("+density+urban", "whp_z + ldens + urban"), ("all controls", base), ("all controls + county FE", base + " + " + fe)]:
            if spec is None:
                for v in ("whp_z", "svi_z", "cvi_z", "urban", "tribal"):
                    if v == "tribal" and D.tribal.sum() < 10:
                        continue
                    m, ci = fit(D, y, v, label)
                    reg.append(dict(group=gname, y=y, spec="alone", term=v, coef_pp=100 * m.params[v], lo_pp=100 * ci.loc[v, 0], hi_pp=100 * ci.loc[v, 1], n=len(D), mean_pp=100 * np.average(D[y], weights=D[f"{S}_den"])))
            else:
                if gname != "pooled" and "C(county5)" in spec and D.county5.nunique() < 3:
                    continue
                m, ci = fit(D, y, spec, label)
                for v in ("whp_z", "svi_z", "cvi_z", "urban", "tribal", "ldens"):
                    if v in m.params.index:
                        reg.append(dict(group=gname, y=y, spec=label, term=v, coef_pp=100 * m.params[v], lo_pp=100 * ci.loc[v, 0], hi_pp=100 * ci.loc[v, 1], n=len(D), mean_pp=100 * np.average(D[y], weights=D[f"{S}_den"])))
Rg = pd.DataFrame(reg)
Rg.to_csv(f"{OUT}/stats_regress_{TAG}{SUF}.csv", index=False)
print("\n==== regression (coef in percentage points of S30 per unit; z-scores are within region) ====")
print(Rg[(Rg.y == f"{S}_s30") & (Rg.spec.isin(["alone", "all controls", "all controls + county FE"])) & Rg.term.isin(["whp_z", "svi_z", "cvi_z", "urban", "tribal"])].round(2).to_string(index=False))

if S != "eq":
    sys.exit(0)
# ---- burden tables -------------------------------------------------------------------------------------------------------------------------------
bur = []
for gname, Ds in groups:
    D = pd.concat(Ds, ignore_index=True)
    r = dict(group=gname, dwellings=D.eq_den.sum(), persons=D.eq_pden.sum())
    for t in (10, 30, 60, 100, 300, 1000):
        r[f"dwell_S{t}"] = D[f"eq_nds{t}"].sum(); r[f"pers_S{t}"] = D[f"eq_nps{t}"].sum()
    r["dwell_single"] = (D.eq_spof * D.eq_den).sum(); r["pers_single"] = (D.eq_pspof * D.eq_pden).sum()
    bur.append(r)
BU = pd.DataFrame(bur); BU.to_csv(f"{OUT}/stats_burden_{TAG}{SUF}.csv", index=False)
print("\n==== burden (absolute) ====")
print(BU.round(0).to_string(index=False))
