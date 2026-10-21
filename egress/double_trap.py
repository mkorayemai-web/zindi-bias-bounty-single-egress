"""'Double-trapped' add-on: no-vehicle households that live behind a single link (S30) AND have no mapped transit stop within 800 m (0.5 mile).
Inputs (all provided/public): work/<region>_bldg.parquet, _drv_snap.parquet, _drv_A_bres.parquet, _tracts.parquet (provided Overture buildings/roads, ACS B25001),
ACS B25044 no-vehicle share (ext/acs_tract_ext.parquet), Overture infrastructure transit stops (provided).  usage: double_trap.py   -> tables/double_trap.csv
Households without a vehicle per building = dwellings(building) x (tract no-vehicle households / tract housing units) (ACS B25044 / B25001), so tract totals equal ACS counts; stops = Overture infrastructure subtype 'transit' (bus_stop, platform, railway_station, bus_station, railway_halt)."""
import sys, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from common import *
THR = 800.0
A = pd.read_parquet(f"{REPO_ROOT}/ext/acs_tract_ext.parquet").set_index("GEOID")
c = con(threads=2)
rows = []
for region in ALLREG:
    T = pd.read_parquet(f"{WORK}/{region}_tracts.parquet")
    HU = T.housing_units.fillna(0).values.astype("float64")
    ncs = (A.nocar_hh.reindex(T.GEOID.values).fillna(0).values / np.maximum(HU, 1.0))        # no-vehicle households per housing unit of the tract (ACS B25044 / B25001)
    B = pd.read_parquet(f"{WORK}/{region}_bldg.parquet", columns=["bidx", "x", "y"])
    S = pd.read_parquet(f"{WORK}/{region}_drv_snap.parquet", columns=["bidx", "cand", "tract_i"])
    R = pd.read_parquet(f"{WORK}/{region}_drv_A_bres.parquet", columns=["bidx", "egress", "top_eq"])
    D = B.merge(S, on="bidx").merge(R, on="bidx")
    D = D[D.cand & (D.tract_i >= 0)].reset_index(drop=True)
    ti = D.tract_i.values.astype(int)
    nc = np.bincount(ti, minlength=len(T)).astype(float)
    D["dw"] = HU[ti] / np.maximum(nc[ti], 1)
    D["nocar"] = D.dw.values * ncs[ti]
    st = c.sql(f"""SELECT ST_X(ST_Centroid(ST_Transform(geometry,'EPSG:4326','{CRS_M}',always_xy:=true))) x, ST_Y(ST_Centroid(ST_Transform(geometry,'EPSG:4326','{CRS_M}',always_xy:=true))) y
                   FROM '{ref(region,'overture-infrastructure')}' WHERE subtype='transit'""").fetchdf()
    d, _ = cKDTree(st[["x", "y"]].values).query(D[["x", "y"]].values, k=1)
    D["nostop"] = d > THR
    near = D.egress.values >= 0
    s30 = near & (D.egress.values == 1) & (D.top_eq.values >= 30)
    oth = near & ~s30
    def w(mask, col): return float((D[col].values * mask).sum())
    # within-tract comparison: weighted by the smaller of the two groups' dwellings in each tract
    g = pd.DataFrame({"t": ti, "dw": D.dw.values, "s30": s30, "oth": oth, "ns": D.nostop.values})
    a = g[g.s30].groupby("t").apply(lambda x: pd.Series({"w": x.dw.sum(), "p": np.average(x.ns, weights=np.maximum(x.dw, 1e-9))}), include_groups=False)
    b = g[g.oth].groupby("t").apply(lambda x: pd.Series({"w": x.dw.sum(), "p": np.average(x.ns, weights=np.maximum(x.dw, 1e-9))}), include_groups=False)
    j = a.join(b, lsuffix="_s", rsuffix="_o", how="inner"); ww = np.minimum(j.w_s, j.w_o)
    within = float(np.average(j.p_s - j.p_o, weights=ww)) if len(j) else np.nan
    rows.append(dict(region=region, dwellings_S30=w(s30, "dw"), nocar_hh_S30=w(s30, "nocar"),
                     share_S30_dwellings_no_stop=w(s30 & D.nostop.values, "dw") / w(s30, "dw"), share_other_dwellings_no_stop=w(oth & D.nostop.values, "dw") / w(oth, "dw"),
                     within_tract_diff_pp=100 * within, tracts_compared=len(j),
                     nocar_hh_S30_no_stop=w(s30 & D.nostop.values, "nocar"), nocar_hh_all=float(np.sum(ncs * HU)),
                     nocar_hh_S30_share_of_all=w(s30, "nocar") / max(float(np.sum(ncs * HU)), 1)))
    print(rows[-1], flush=True)
R_ = pd.DataFrame(rows)
tot = R_[["dwellings_S30", "nocar_hh_S30", "nocar_hh_S30_no_stop", "nocar_hh_all"]].sum()
R_.to_csv(f"{OUT}/double_trap.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(R_.round(3).to_string(index=False)); print("TOTAL", tot.round(0).to_dict())
