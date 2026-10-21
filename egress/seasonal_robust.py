"""Robustness of the seasonal-housing contrast: weighting scheme (eq = ACS-weighted dwellings, ar = footprint-area-weighted dwellings, str = structure counts, i.e. NO ACS housing units used)
x resort-type threshold (>=5%, >=10%, >=20% of housing units seasonal) x road-class set (scored classes vs +service+track). Pooled over the regions that have each configuration, cluster bootstrap over tracts.
usage: seasonal_robust.py [BOOT] -> tables/seasonal_robust.csv"""
import sys, numpy as np, pandas as pd
from common import *
B = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
rng = np.random.default_rng(SEED)
S = pd.read_parquet(f"{REPO_ROOT}/ext/acs_b25004_seasonal.parquet")
rows = []
for tag in ("drv_A", "drvplus_A"):
    DS = []
    for region in regions_for(tag):
        T = pd.read_parquet(f"{WORK}/{region}_{tag}_tract.parquet").reset_index(names="GEOID")
        hu = pd.read_parquet(f"{WORK}/{region}_tracts.parquet")[["GEOID", "housing_units"]]
        D = T.merge(S, on="GEOID", how="left").merge(hu, on="GEOID", how="left")
        D = D[D.housing_units > 0].copy(); D["seas"] = D.seasonal_units / D.housing_units; D["region"] = region
        DS.append(D)
    for sch in ("eq", "ar", "str"):
        for thr in (0.05, 0.10, 0.20):
            for met in ("s30", "s100"):
                parts = []
                for D in DS:
                    D = D[D[f"{sch}_den"] > 0]
                    a = (D.seas >= thr).values.astype(float); b = 1 - a
                    if a.sum() < 5 or b.sum() < 5: continue
                    num = (D[f"{sch}_{met}"] * D[f"{sch}_den"]).values; dn = D[f"{sch}_den"].values; n = len(D)
                    cnt = rng.multinomial(n, np.ones(n) / n, size=B).astype(float)
                    parts.append((dn.sum(), (cnt @ (num * a)) / (cnt @ (dn * a)), (cnt @ (num * b)) / (cnt @ (dn * b)), (num * a).sum() / (dn * a).sum(), (num * b).sum() / (dn * b).sum()))
                Wt = sum(p[0] for p in parts); ba = sum(p[0] * p[1] for p in parts) / Wt; bb = sum(p[0] * p[2] for p in parts) / Wt
                sa = sum(p[0] * p[3] for p in parts) / Wt; sb = sum(p[0] * p[4] for p in parts) / Wt; r = ba / bb
                rows.append(dict(config=tag, scheme=sch, threshold=thr, metric=met.upper(), regions=len(parts), share_resort=sa, share_other=sb, ratio=sa / sb, lo=np.percentile(r, 2.5), hi=np.percentile(r, 97.5)))
R = pd.DataFrame(rows); R.to_csv(f"{OUT}/seasonal_robust.csv", index=False)
pd.set_option("display.width", 200)
print(R.round(3).to_string(index=False))
