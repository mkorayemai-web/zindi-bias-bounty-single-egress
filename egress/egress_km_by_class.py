"""Length of the single-egress link segments by Overture road class (S30 links versus the other segments of the same classes), five regions pooled.
Input: work/<region>_cb link files from coverage_bridge.py (work/cb_<region>_link.parquet). Output: tables/single_egress_km_by_class.csv.
Used by NUMBERS_LEDGER (S.01-S.03: 'x % of the single-egress km are in motorway/trunk/primary/secondary', '81 % are residential'); shipped as a table so the ledger runs without work/."""
import sys, glob, pandas as pd
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
L = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{WORK}/cb_*_link.parquet"))])
G = L.groupby("cls")[["S30_L", "oth_L"]].sum() / 1000.0; G.columns = ["s30_km", "other_km"]
G["share_of_s30_km_pct"] = 100 * G.s30_km / G.s30_km.sum(); G = G.sort_values("s30_km", ascending=False).reset_index().rename(columns={"cls": "road_class"})
G.to_csv(f"{OUT}/single_egress_km_by_class.csv", index=False); print(G.round(2).to_string(index=False)); print(f"total single-egress km {G.s30_km.sum():,.0f}")
