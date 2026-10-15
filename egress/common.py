"""Shared paths/helpers for the egress (single-point-of-failure) analysis. Seeded, re-runnable; every path is derived from the location of this file (data root: $BIAS_BOUNTY_ROOT or ./data)."""
import os, duckdb, numpy as np
_HERE = os.path.dirname(os.path.abspath(__file__))
LANE = os.environ.get("EGRESS_LANE") or os.path.dirname(_HERE)      # the repository root: the directory that holds egress/, tables/, work/, ext/ ... (derived from this file's location)
def _data_root():
    """Directory that holds data/reference/<region>/ and data/strata/<region>/ (the `aws s3 sync` layout of the challenge README):
    $BIAS_BOUNTY_ROOT if set, else the repository root or its nearest parent directory that has data/reference/."""
    env = os.environ.get("BIAS_BOUNTY_ROOT")
    if env: return env
    d = LANE
    while True:
        if os.path.isdir(os.path.join(d, "data", "reference")): return d
        p = os.path.dirname(d)
        if p == d: return LANE
        d = p
ROOT = _data_root()
DATA = f"{ROOT}/data"
WORK = f"{LANE}/work"
OUT = f"{LANE}/tables"
REGIONS = ["northern-ca", "eastern-ok", "maricopa-az", "south-central-tx"]      # the four regions of the original task
ALLREG = REGIONS + ["eastern-wa"]                                              # eastern-wa (415 tracts) joined the scored set on 2026-09-28

def regions_for(tag):
    """Regions (of ALLREG) that have a finished tract table for this configuration tag, e.g. drv_A."""
    return [r for r in ALLREG if os.path.exists(f"{WORK}/{r}_{tag}_tract.parquet")]
SEED = 20261014
# class sets -------------------------------------------------------------------------------------------------
SCORED = ("motorway", "trunk", "primary", "secondary", "tertiary", "residential", "unclassified")   # == *-overture-roads.parquet
DRV = SCORED + ("living_street",)
DRVPLUS = DRV + ("service", "track")
ARTERIAL_A = ("motorway", "trunk", "primary", "secondary")     # sink A: the classes the scorecard itself scores
ARTERIAL_B = ("motorway", "trunk")                              # sink B: high-speed corridors only
CRS_M = "EPSG:5070"

def ref(region, layer):
    return f"{DATA}/reference/{region}/{region}-{layer}.parquet"

def strata(region, name="strata-tract-table"):
    return f"{DATA}/strata/{region}/{region}-{name}.parquet"

def con(threads=4, mem="10GB"):
    c = duckdb.connect()
    c.sql("INSTALL spatial; LOAD spatial;")
    c.sql(f"SET threads={threads}; SET memory_limit='{mem}'; SET temp_directory='{WORK}/duck_tmp';")
    os.makedirs(f"{WORK}/duck_tmp", exist_ok=True)
    return c

def scored_geoids(region):
    import pandas as pd
    return pd.read_csv(f"{DATA}/reference/{region}/{region}-sample-submission.csv", dtype={"GEOID": str})["GEOID"].tolist()
