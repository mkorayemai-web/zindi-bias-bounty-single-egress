"""Aggregate response_time.py outputs: 'hard to reach AND hard to leave'. usage: resp_summary.py [BOOT]
Per region and pooled, strict (category fire_department) and broad (category OR fire-like name) station definitions, free-flow speeds, threshold 10 min:
  far   = share of dwellings with modelled drive time > 10 min to the nearest mapped fire station (or no route)
  P(S30|far), P(S30|near) and their ratio (cluster bootstrap over tracts, regions weighted by dwellings, seeded)
  both  = dwellings that are far AND behind a single link serving >= 30 dwellings; share of all S30 dwellings that are far.
Inputs tables/resp_<region>[_broad].csv (per tract: dw, far10, far15, s30 share, both10, both15)."""
import sys, numpy as np, pandas as pd
from common import *
B = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
rng = np.random.default_rng(SEED)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
rows = []
for variant, suf in (("strict", ""), ("broad", "_broad")):
    parts = []
    for r in ALLREG:
        T = pd.read_csv(f"{OUT}/resp_{r}{suf}.csv", dtype={"tract": str}).dropna(subset=["dw"])
        T = T[T.dw > 0]
        dw = T.dw.values; far = T.far10.values; s30 = T.s30.values; both = T.both10.values
        W = dw.sum()
        def stat(cnt):
            d = cnt * dw
            far_d = (d * far).sum(); s30_d = (d * s30).sum(); both_d = (cnt * both).sum()
            p_far = both_d / far_d; p_near = (s30_d - both_d) / (d.sum() - far_d)
            return far_d / d.sum(), p_far, p_near, p_far / p_near, both_d / s30_d
        base = stat(np.ones(len(T)))
        bs = np.array([stat(rng.multinomial(len(T), np.ones(len(T)) / len(T)).astype(float)) for _ in range(B)])
        lo, hi = np.percentile(bs[:, 3], [2.5, 97.5])
        rows.append(dict(variant=variant, region=r, dwellings=W, far_share=base[0], P_S30_far=base[1], P_S30_near=base[2], ratio=base[3], ratio_lo=lo, ratio_hi=hi,
                         both_dwellings=(T.both10).sum(), share_of_S30_that_is_far=base[4]))
        parts.append((T, bs))
    # pooled: resample within region, combine with dwelling weights
    Ts = [p[0] for p in parts]
    def pooled(cnts):
        far_d = s30_d = both_d = tot = 0.0
        for T, cnt in zip(Ts, cnts):
            d = cnt * T.dw.values
            far_d += (d * T.far10.values).sum(); s30_d += (d * T.s30.values).sum(); both_d += (cnt * T.both10.values).sum(); tot += d.sum()
        return far_d / tot, both_d / far_d, (s30_d - both_d) / (tot - far_d), (both_d / far_d) / ((s30_d - both_d) / (tot - far_d)), both_d / s30_d
    base = pooled([np.ones(len(T)) for T in Ts])
    bs = np.array([pooled([rng.multinomial(len(T), np.ones(len(T)) / len(T)).astype(float) for T in Ts]) for _ in range(B)])
    lo, hi = np.percentile(bs[:, 3], [2.5, 97.5])
    rows.append(dict(variant=variant, region="pooled", dwellings=sum(T.dw.sum() for T in Ts), far_share=base[0], P_S30_far=base[1], P_S30_near=base[2], ratio=base[3], ratio_lo=lo, ratio_hi=hi,
                     both_dwellings=sum(T.both10.sum() for T in Ts), share_of_S30_that_is_far=base[4]))
R = pd.DataFrame(rows)
R.to_csv(f"{OUT}/resp_summary.csv", index=False)
print(R.round(3).to_string(index=False))
