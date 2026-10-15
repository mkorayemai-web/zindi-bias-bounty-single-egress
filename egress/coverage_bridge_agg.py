"""Pool coverage_bridge.py outputs. usage: coverage_bridge_agg.py [BOOT]  -> tables/false_single_access.csv, tables/cov_bridge_buildings.csv, tables/cov_bridge_links.csv
Paired within-stratum estimator (stratum = tract for buildings; tract x road class for links):
  P1 = share of attribute among the 'trapped' (S30) units; P0 = share among all OTHER units of the SAME strata, re-weighted to the trapped units' strata mix (so P1-P0 is a within-tract / within-class difference).
  CI: bootstrap over COUNTIES (all five regions pooled; counties resampled with replacement)."""
import sys, numpy as np, pandas as pd
from common import *
B = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
rng = np.random.default_rng(SEED)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
RG = ALLREG
# ---------------- D2: robustness of S30 status to the map's own incompleteness
C = pd.concat([pd.read_csv(f"{WORK}/cb_{r}_conc.csv") for r in RG], ignore_index=True)
rows = []
for name, sub in [(r, C[C.region == r]) for r in RG] + [("pooled", C)]:
    base = sub.base_S30_dw.sum(); d = dict(region=name, S30_dwellings=base, S30_share=base / sub.base_den.sum())
    if "plus_S30_dw" in sub and sub.plus_S30_dw.notna().all():
        d["plus_share"] = sub.plus_S30_dw.sum() / sub.plus_den.sum(); d["flips_with_service_track_pct"] = 100 * sub.flips_plus_dw.sum() / base
    else:
        s2 = sub.dropna(subset=["plus_S30_dw"]) if "plus_S30_dw" in sub else sub.iloc[:0]
        if len(s2): d["plus_share"] = s2.plus_S30_dw.sum() / s2.plus_den.sum(); d["flips_with_service_track_pct"] = 100 * s2.flips_plus_dw.sum() / s2.base_S30_dw.sum()
    d["r25_share"] = sub.r25_S30_dw.sum() / sub.r25_den.sum(); d["flips_with_repair25_pct"] = 100 * sub.flips_r25_dw.sum() / base
    s3 = sub.dropna(subset=["flips_either_dw"]) if "flips_either_dw" in sub else sub.iloc[:0]
    if len(s3): d["flips_either_pct"] = 100 * s3.flips_either_dw.sum() / s3.base_S30_dw.sum(); d["robust_pct"] = 100 - d["flips_either_pct"]
    rows.append(d)
FS = pd.DataFrame(rows); FS.to_csv(f"{OUT}/false_single_access.csv", index=False); print("== D2: how much of the baseline S30 status survives the map's own incompleteness (service/track roads added; <=25 m gaps repaired)"); print(FS.round(3).to_string(index=False))

def paired_boot(df, key_n1, pairs, label):
    """df has columns county, <key_n1> (units of group1), and for each (g1col, g0col, n0col, name) in pairs: sums; returns table with P1, P0, diff, ratio, CI over counties."""
    out = []
    ok = df[(df[key_n1] > 0)]
    for (g1, g0, n0, name) in pairs:
        # per stratum: p1 = g1/n1, p0 = g0/n0  -> n1*p0 = key_n1 * g0 / n0
        d = ok[ok[n0] > 0].copy(); d["A"] = d[g1]; d["Bc"] = d[key_n1] * d[g0] / d[n0]; d["N"] = d[key_n1]
        cs = d.groupby("county")[["A", "Bc", "N"]].sum()
        a, b, n = cs.A.values, cs.Bc.values, cs.N.values
        P1, P0 = a.sum() / n.sum(), b.sum() / n.sum()
        idx = rng.integers(0, len(cs), size=(B, len(cs)))
        bs1 = a[idx].sum(1) / n[idx].sum(1); bs0 = b[idx].sum(1) / n[idx].sum(1)
        out.append(dict(what=label, indicator=name, units=n.sum(), counties=len(cs), P_trapped=P1, P_same_tract_others=P0, diff_pp=100 * (P1 - P0),
                        diff_lo=100 * np.percentile(bs1 - bs0, 2.5), diff_hi=100 * np.percentile(bs1 - bs0, 97.5), ratio=P1 / P0, ratio_lo=np.percentile(bs1 / bs0, 2.5), ratio_hi=np.percentile(bs1 / bs0, 97.5)))
    return out
# ---------------- E2(i): provenance of the trapped homes
Pv = pd.concat([pd.read_parquet(f"{WORK}/cb_{r}_prov.parquet") for r in RG], ignore_index=True)
res = []
for name, sub in [(r, Pv[Pv.region == r]) for r in RG] + [("pooled", Pv)]:
    sub = sub[(sub.trapped_dw > 0) & (sub.other_dw > 0)].copy()
    pairs = [(f"trapped_{k}", f"other_{k}", "other_dw", k) for k in ("ml", "noclass", "nosub", "old")]
    # trapped_dw is the n1 key; trapped_<k> are dwelling-weighted sums of the indicator among trapped units; other_<k>/other_dw = P0 in the tract
    for r_ in paired_boot(sub, "trapped_dw", pairs, "buildings (dwelling-weighted)"): r_["group"] = name; res.append(r_)
BR = pd.DataFrame(res); BR.to_csv(f"{OUT}/cov_bridge_buildings.csv", index=False)
print("\n== E2(i): footprint provenance of trapped homes vs other homes in the SAME tracts (ml = AI-derived footprint; noclass/nosub = building class/subtype missing; old = last updated <= 2021)")
print(BR[BR.group == "pooled"].round(3).drop(columns=["what", "group"]).to_string(index=False)); print(BR[BR.indicator == "ml"][["group", "units", "counties", "P_trapped", "P_same_tract_others", "diff_pp", "diff_lo", "diff_hi", "ratio"]].round(3).to_string(index=False))
# ---------------- E2(ii): attribute coverage of the single egress links
Lk = pd.concat([pd.read_parquet(f"{WORK}/cb_{r}_link.parquet") for r in RG], ignore_index=True)
res = []
for name, sub in [(r, Lk[Lk.region == r]) for r in RG] + [("pooled", Lk)]:
    sub = sub[(sub.S30_L > 0) & (sub.oth_L > 0)].copy()
    pairs = [(f"S30_{k}", f"oth_{k}", "oth_L", k) for k in ("named", "surface", "speed", "access", "osm", "recent")]
    for r_ in paired_boot(sub, "S30_L", pairs, "links (length-weighted, same tract and road class)"): r_["group"] = name; res.append(r_)
LR = pd.DataFrame(res); LR.to_csv(f"{OUT}/cov_bridge_links.csv", index=False)
print("\n== E2(ii): attribute coverage of single-egress link segments vs other segments of the same road class in the same tract (share WITH the attribute)")
print(LR[LR.group == "pooled"].round(3).drop(columns=["what", "group"]).to_string(index=False)); print(LR[LR.indicator == "named"][["group", "units", "counties", "P_trapped", "P_same_tract_others", "diff_pp", "diff_lo", "diff_hi"]].round(3).to_string(index=False))
