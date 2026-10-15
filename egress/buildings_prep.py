"""Extract building centroids (EPSG:5070), footprint area, class/subtype and primary source dataset from the PROVIDED Overture
buildings layer. usage: buildings_prep.py REGION  -> work/<region>_bldg.parquet"""
import sys, time
from common import *
region = sys.argv[1]
t0 = time.time()
c = con()
src = ref(region, "overture-buildings")
c.sql(f"""
COPY (
 SELECT row_number() OVER (ORDER BY id) AS bidx, id AS bid,
        ST_X(ST_Centroid(gm)) AS x, ST_Y(ST_Centroid(gm)) AS y, ST_Area(gm) AS area_m2,
        subtype, class,
        list_extract(list_transform(sources, s -> s.dataset), 1) AS dataset,
        try_cast(substr(list_max(list_transform(sources, s -> s.update_time)), 1, 4) AS INTEGER) AS upd_year
 FROM (SELECT *, ST_Transform(geometry, 'EPSG:4326', '{CRS_M}', always_xy := true) AS gm FROM '{src}')
) TO '{WORK}/{region}_bldg.parquet' (FORMAT parquet, COMPRESSION zstd)
""")
print(region, "buildings", c.sql(f"SELECT count(*) FROM '{WORK}/{region}_bldg.parquet'").fetchone()[0], f"{time.time()-t0:.0f}s")
