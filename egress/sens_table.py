"""Assemble the sensitivity grid (region x road-class set x sink x weighting x digitising-gap repair) from tables/<tag>_summary.csv.
usage: sens_table.py  -> tables/sens_grid.csv, tables/sens_grid.md"""
import glob, os, re, numpy as np, pandas as pd
from common import *
rows = []
for f in sorted(glob.glob(f"{OUT}/*_summary.csv")):
    b = os.path.basename(f)
    m = re.match(r"(northern-ca|eastern-ok|maricopa-az|south-central-tx|eastern-wa)_(drv|drvplus)_(A|B)(_r\d+)?_summary\.csv$", b)
    if not m:
        continue
    d = pd.read_csv(f)
    for _, r in d.iterrows():
        rows.append(dict(region=m.group(1), classes={"drv": "scored classes", "drvplus": "+service+track"}[m.group(2)], sink="A: motorway..secondary" if m.group(3) == "A" else "B: motorway,trunk",
                         repair="snap dead ends <=25 m" if m.group(4) else "none", scheme={"eq": "ACS dwellings", "ar": "area-weighted dwellings", "str": "structure count"}[r.scheme],
                         den=r.den, single_route=r.spof, S10=r.s10, S30=r.s30, S60=r.s60, S100=r.s100, S300=r.s300, S1000=r.s1000))
G = pd.DataFrame(rows)
G.to_csv(f"{OUT}/sens_grid.csv", index=False)
lines = ["| region | road classes | sink | repair | weights | single route | S30 | S100 | S300 |", "|---|---|---|---|---|---|---|---|---|"]
for _, r in G.sort_values(["region", "classes", "sink", "repair", "scheme"]).iterrows():
    lines.append(f"| {r.region} | {r.classes} | {r.sink} | {r.repair} | {r.scheme} | {100*r.single_route:.1f}% | {100*r.S30:.1f}% | {100*r.S100:.1f}% | {100*r.S300:.2f}% |")
open(f"{OUT}/sens_grid.md", "w").write("\n".join(lines) + "\n")
print(open(f"{OUT}/sens_grid.md").read())
