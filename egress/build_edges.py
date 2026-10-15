"""Build the drivable road graph pieces for one region from the PROVIDED Overture roads-unfiltered layer.
usage: build_edges.py REGION SET   (SET = drv | drvplus)
Each Overture segment lists connectors (connector_id, at in [0,1]); consecutive connectors define graph edges ("pieces").
Writes work/<region>_<set>_pieces.parquet (one row per piece, with integer node ids, length, class, attributes, EPSG:5070 WKB)
and work/<region>_<set>_segs.parquet (one row per segment: attribute completeness, flags, last-edit year)."""
import sys, time
from common import *
region, cset = sys.argv[1], sys.argv[2]
classes = DRV if cset == "drv" else DRVPLUS
cl = ",".join(f"'{c}'" for c in classes)
t0 = time.time()
c = con()
src = ref(region, "overture-roads-unfiltered")
c.sql(f"""
CREATE TABLE seg AS
SELECT row_number() OVER (ORDER BY id) AS sidx, id AS seg_id, class AS cls, subclass, names.primary AS rname, list_extract(list_transform(routes, r -> r.ref), 1) AS rref,
       (names.primary IS NOT NULL OR (routes IS NOT NULL AND len(routes) > 0)) AS named,
       (road_surface IS NOT NULL AND len(road_surface) > 0) AS has_surface,
       (speed_limits IS NOT NULL AND len(speed_limits) > 0) AS has_speed,
       (access_restrictions IS NOT NULL AND len(access_restrictions) > 0) AS has_access_rule,
       coalesce(len(list_filter(road_flags, rf -> list_contains(rf['values'], 'is_bridge'))) > 0, false) AS is_bridge,
       coalesce(len(list_filter(road_flags, rf -> list_contains(rf['values'], 'is_tunnel'))) > 0, false) AS is_tunnel,
       coalesce(len(list_filter(road_flags, rf -> list_contains(rf['values'], 'is_abandoned'))) > 0, false) AS is_abandoned,
       coalesce(len(list_filter(road_flags, rf -> list_contains(rf['values'], 'is_under_construction'))) > 0, false) AS is_construction,
       coalesce(len(list_filter(road_flags, rf -> list_contains(rf['values'], 'is_link'))) > 0, false) AS is_link,
       try_cast(substr(list_max(list_transform(sources, s -> s.update_time)), 1, 4) AS INTEGER) AS upd_year,
       list_extract(list_transform(sources, s -> s.dataset), 1) AS dataset,
       connectors,
       CASE WHEN ST_GeometryType(geometry) = 'LINESTRING' THEN ST_Transform(geometry, 'EPSG:4326', '{CRS_M}', always_xy := true)
            ELSE ST_LineMerge(ST_Transform(geometry, 'EPSG:4326', '{CRS_M}', always_xy := true)) END AS g
FROM '{src}'
WHERE class IN ({cl}) AND connectors IS NOT NULL AND len(connectors) >= 2
""")
n = c.sql("SELECT count(*) FROM seg").fetchone()[0]
print(region, cset, "segments", n, f"{time.time()-t0:.0f}s", flush=True)
c.sql("""
CREATE TABLE cn AS
SELECT sidx, cc.connector_id AS cid, cc."at" AS at, row_number() OVER (PARTITION BY sidx ORDER BY cc."at") AS rn
FROM (SELECT sidx, unnest(connectors) AS cc FROM seg)
""")
c.sql("""
CREATE TABLE pieces0 AS
SELECT a.sidx, a.cid AS ucid, b.cid AS vcid, a.at AS at0, b.at AS at1
FROM cn a JOIN cn b ON a.sidx = b.sidx AND b.rn = a.rn + 1
WHERE a.cid <> b.cid AND b.at > a.at
""")
c.sql("CREATE TABLE nodes AS SELECT cid, row_number() OVER (ORDER BY cid) - 1 AS nid FROM (SELECT ucid AS cid FROM pieces0 UNION SELECT vcid FROM pieces0)")
c.sql(f"""
COPY (
 SELECT p.sidx, nu.nid AS u, nv.nid AS v, (p.at1 - p.at0) * ST_Length(s.g) AS len_m, s.cls,
        ST_AsWKB(CASE WHEN (p.at0 = 0 AND p.at1 = 1) OR ST_GeometryType(s.g) <> 'LINESTRING' THEN s.g ELSE ST_LineSubstring(s.g, p.at0, p.at1) END) AS wkb
 FROM pieces0 p JOIN seg s USING (sidx) JOIN nodes nu ON nu.cid = p.ucid JOIN nodes nv ON nv.cid = p.vcid
 ORDER BY p.sidx, p.at0
) TO '{WORK}/{region}_{cset}_pieces.parquet' (FORMAT parquet, COMPRESSION zstd)
""")
c.sql(f"""
COPY (SELECT sidx, seg_id, cls, subclass, rname, rref, named, has_surface, has_speed, has_access_rule, is_bridge, is_tunnel, is_abandoned,
             is_construction, is_link, upd_year, dataset, ST_Length(g) AS seg_len_m FROM seg)
TO '{WORK}/{region}_{cset}_segs.parquet' (FORMAT parquet, COMPRESSION zstd)
""")
npieces = c.sql("SELECT count(*) FROM pieces0").fetchone()[0]
print(region, cset, "pieces", npieces, "nodes", c.sql("SELECT count(*) FROM nodes").fetchone()[0], f"{time.time()-t0:.0f}s", flush=True)
