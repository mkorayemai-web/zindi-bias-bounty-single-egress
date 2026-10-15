"""Name places from the PROVIDED Overture POIs: dominant addresses[1].locality within RADIUS of a point (EPSG:5070 metres)."""
import numpy as np, pandas as pd, shapely
from shapely import STRtree
from common import *
_cache = {}
def poi_index(region):
    if region in _cache:
        return _cache[region]
    c = con(threads=2)
    F = c.sql(f"""SELECT addresses[1].locality AS locality, ST_X(ST_Transform(geometry,'EPSG:4326','{CRS_M}',always_xy:=true)) AS x,
                  ST_Y(ST_Transform(geometry,'EPSG:4326','{CRS_M}',always_xy:=true)) AS y
                  FROM '{ref(region,'overture-pois')}' WHERE addresses[1].locality IS NOT NULL""").fetchdf()
    pts = shapely.points(F.x.values, F.y.values)
    _cache[region] = (F, STRtree(pts), pts)
    return _cache[region]

def name_points(region, x, y, radius=2000, top=2):
    F, tree, pts = poi_index(region)
    q = shapely.points(np.asarray(x), np.asarray(y))
    a, b = tree.query(q, predicate="dwithin", distance=radius)
    out = [""] * len(q)
    if len(a) == 0:
        return out
    df = pd.DataFrame({"i": a, "loc": F["locality"].values[b]})
    vc = df.groupby(["i", "loc"]).size().reset_index(name="n").sort_values(["i", "n", "loc"], ascending=[True, False, True])
    vc["rk"] = vc.groupby("i").cumcount()
    vc = vc[vc.rk < top]
    for i, g in vc.groupby("i"):
        out[i] = ", ".join(str(v).title() for v in g["loc"].values)
    return out
