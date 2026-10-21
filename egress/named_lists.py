"""Named lists for the write-up (tract GEOIDs + place names): choke links, mobile-home parks and other facilities behind choke links, top tracts.
usage: named_lists.py REGION TAG       (needs tables/<region>_<TAG>_links.csv, tables/fac_<region>_<TAG>.csv, work/<region>_<TAG>_tract.parquet)
Writes tables/named_<region>_<TAG>.md and prints it."""
import sys, numpy as np, pandas as pd
from common import *
region, TAG = sys.argv[1], sys.argv[2]
cn = pd.read_csv(f"{REPO_ROOT}/ext/national_county2020.txt", sep="|", dtype=str)
cn["code"] = cn.STATEFP + cn.COUNTYFP
CNAME = dict(zip(cn.code, cn.COUNTYNAME + ", " + cn.STATE))
def county(g):
    return CNAME.get(str(g)[:5], str(g)[:5]) if isinstance(g, str) else ""
md = []
L = pd.read_csv(f"{OUT}/{region}_{TAG}_links.csv", dtype={"tract": str})
L["county"] = L.tract.map(county)
L["km"] = L.len_m / 1000
top = L.sort_values("load_persons", ascending=False).head(15)
md.append(f"### {region}: largest single-link clusters ({TAG}); persons/dwellings behind the link, tract, county\n")
md.append("| # | community (nearest Overture POI localities) | road carrying the single link | class | tract | county | dwellings | persons | link km |")
md.append("|---|---|---|---|---|---|---|---|---|")
for i, (_, r) in enumerate(top.iterrows(), 1):
    md.append(f"| {i} | {r.place if isinstance(r.place, str) else ''} | {r.rname if isinstance(r.rname, str) else '(unnamed)'} | {r.cls} | {r.tract} | {r.county} | {r.load_dwell:,.0f} | {r.load_persons:,.0f} | {r.km:.2f} |")
F = pd.read_csv(f"{OUT}/fac_{region}_{TAG}.csv", dtype={"tract": str})
F["county"] = F.tract.map(county)
for kind, title, k in [("mobile_home_park", "mobile-home parks", 12), ("senior_care", "senior-care facilities (nursing, assisted living, hospice, retirement)", 8),
                       ("school", "schools", 6), ("campground_rv", "campgrounds / RV parks", 6)]:
    d = F[(F.kind == kind) & (F.egress == 1) & (F.dist_m <= 500)].sort_values("load_persons", ascending=False).head(k)
    if len(d) == 0:
        continue
    md.append(f"\n### {region}: {title} whose only route out is a single link (largest by persons behind the link)\n")
    md.append("| # | name | locality | tract | county | dwellings behind link | persons behind link |")
    md.append("|---|---|---|---|---|---|---|")
    for i, (_, r) in enumerate(d.iterrows(), 1):
        md.append(f"| {i} | {r['name'] if isinstance(r['name'], str) else '(unnamed)'} | {r.locality if isinstance(r.locality, str) else ''} | {r.tract} | {r.county} | {r.load_dwell:,.0f} | {r.load_persons:,.0f} |")
T = pd.read_parquet(f"{WORK}/{region}_{TAG}_tract.parquet").reset_index(names="GEOID")
st = pd.read_parquet(strata(region), columns=["GEOID", "ur_class", "svi_overall", "usfs_WHP_mean", "tribal_any", "aiannh_name"])
T = T.merge(st, on="GEOID")
T["county"] = T.GEOID.map(county)
t10 = T.sort_values("eq_nps30", ascending=False).head(10)
md.append(f"\n### {region}: tracts with the most people behind a single link serving >30 dwellings\n")
md.append("| # | tract | county | urban/rural | persons in S30 | share of tract dwellings in S30 | SVI | tribal area |")
md.append("|---|---|---|---|---|---|---|---|")
for i, (_, r) in enumerate(t10.iterrows(), 1):
    md.append(f"| {i} | {r.GEOID} | {r.county} | {r.ur_class} | {r.eq_nps30:,.0f} | {100*r.eq_s30:.0f}% | {r.svi_overall:.2f} | {r.aiannh_name if bool(r.tribal_any) else ''} |")
out = "\n".join(md) + "\n"
open(f"{OUT}/named_{region}_{TAG}.md", "w").write(out)
print(out)
