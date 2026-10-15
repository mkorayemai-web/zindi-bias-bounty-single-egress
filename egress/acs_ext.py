"""Parse the ACS 2020-2024 5-year table-based summary files (public domain, downloaded 2026-10-14 into ext/) for tract rows of the five study states (04, 06, 35, 40, 48, 53).
B25024 (units in structure): mobile homes = E010 / total E001.   B25044 (tenure by vehicles available): households with no vehicle = E003 + E010, occupied = E001.
Output ext/acs_tract_ext.parquet : GEOID, hu_total, mobile_homes, mh_share, occ_hh, nocar_hh, nocar_share."""
import pandas as pd, numpy as np
import os as _os; EXT = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "ext")
keep = ("1400000US04", "1400000US06", "1400000US35", "1400000US40", "1400000US48", "1400000US53")
def load(fn, cols):
    out = []
    for ch in pd.read_csv(f"{EXT}/{fn}", sep="|", usecols=["GEO_ID"] + cols, dtype=str, chunksize=200000):
        out.append(ch[ch.GEO_ID.str.startswith(keep)])
    d = pd.concat(out)
    d["GEOID"] = d.GEO_ID.str[-11:]
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.drop(columns="GEO_ID")
a = load("acsdt5y2024-b25024.dat", ["B25024_E001", "B25024_E010"])
b = load("acsdt5y2024-b25044.dat", ["B25044_E001", "B25044_E003", "B25044_E010"])
d = a.merge(b, on="GEOID", how="outer")
d = d.rename(columns={"B25024_E001": "hu_total", "B25024_E010": "mobile_homes", "B25044_E001": "occ_hh"})
d["nocar_hh"] = d.B25044_E003 + d.B25044_E010
d["mh_share"] = d.mobile_homes / d.hu_total.where(d.hu_total > 0)
d["nocar_share"] = d.nocar_hh / d.occ_hh.where(d.occ_hh > 0)
d = d[["GEOID", "hu_total", "mobile_homes", "mh_share", "occ_hh", "nocar_hh", "nocar_share"]]
d.to_parquet(f"{EXT}/acs_tract_ext.parquet")
print(len(d), d.describe().round(3).to_string())
