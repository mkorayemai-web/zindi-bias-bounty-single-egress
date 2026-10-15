"""Why the scorecard cannot see it, second half: how many S30 dwellings live in tracts that have NO road of the scorecard's classes?
For every region: tracts whose total length of motorway / trunk / primary / secondary graph links is zero (work/cb_<region>_link.parquet: per tract and link, the
lengths S30_L + oth_L), the S30 dwellings (eq_nds30) and all housing units (HU) in those tracts. Everything else is the draft's complement: 100 - pooled pct_s30_in_those
= 97.9 % of S30 dwellings are in tracts with roads of those classes.
Inputs (all shipped): work/cb_<region>_link.parquet, work/<region>_drv_A_tract.parquet.  usage: s30_scorecard_tracts.py  -> tables/s30_in_tracts_without_scorecard_roads.csv
(Saved 2026-10-15 as a script; the table had been written by an unsaved inline command on 2026-10-14. The script reproduces that table byte for byte.)"""
import pandas as pd
from common import ALLREG, WORK, OUT, ARTERIAL_A

ART = set(ARTERIAL_A)                    # motorway, trunk, primary, secondary = the classes the scorecard's road component scores
rows = []
for r in ALLREG:
    L = pd.read_parquet(f"{WORK}/cb_{r}_link.parquet"); L["art"] = L.cls.isin(ART)
    art_km = (L[L.art].assign(l=lambda d: d.S30_L + d.oth_L).groupby("GEOID").l.sum() / 1000)
    T = pd.read_parquet(f"{WORK}/{r}_drv_A_tract.parquet"); T["art_km"] = art_km.reindex(T.index).fillna(0.0)
    noart = T.art_km <= 0
    rows.append(dict(region=r, tracts=len(T), tracts_no_scorecard_class_road=int(noart.sum()), s30_dw=T.eq_nds30.sum(), s30_dw_in_those=T.eq_nds30[noart].sum(),
                     pct_s30_in_those=100 * T.eq_nds30[noart].sum() / T.eq_nds30.sum(), pct_all_dw_in_those=100 * T.HU[noart].sum() / T.HU.sum()))
R = pd.DataFrame(rows); R.to_csv(f"{OUT}/s30_in_tracts_without_scorecard_roads.csv", index=False)
pd.set_option("display.width", 250); print(R.round(2).to_string(index=False))
print("POOLED: share of S30 dwellings in tracts with NO motorway/trunk/primary/secondary link:", round(100 * R.s30_dw_in_those.sum() / R.s30_dw.sum(), 1),
      "% -> in tracts WITH such roads:", round(100 - 100 * R.s30_dw_in_those.sum() / R.s30_dw.sum(), 1), "%")
