"""Coverage bridge + 'false single access' (map-induced) quantification, per region. usage: coverage_bridge.py REGION
Everything is computed on Overture itself (provided package) - no external data.
(1) D2 robustness of building-level S30 status: baseline (scored classes) vs +service/track vs digitising-gap repair 25 m (same bidx space; weights dw_eq = ACS housing units / candidates per tract, exactly as variants.py).
    -> work/cb_<region>_conc.csv
(2) E2(i) building provenance: for candidate dwellings behind S30 links ('trapped') vs other near-network candidates, indicators ml (AI-derived footprint: Microsoft ML Buildings / Google Open Buildings),
    noclass, nosub, old (update year <= 2021). Sufficient statistics per tract -> work/cb_<region>_prov.parquet
(3) E2(ii) attribute coverage of the single egress links: length-weighted shares named / has_surface / has_speed / has_access_rule / OSM-sourced / updated >= 2023 for S30 link pieces (bridge edge with load >= 30 dwellings)
    vs all other pieces of the same road class in the same tract -> work/cb_<region>_link.parquet
Pooling + county-clustered bootstrap: coverage_bridge_agg.py"""
import sys, time, numpy as np, pandas as pd, shapely, geopandas as gpd
from shapely import STRtree
from common import *
region = sys.argv[1]; t0 = time.time()
def log(*a): print(f"[{time.time()-t0:5.0f}s]", *a, flush=True)
T = pd.read_parquet(f"{WORK}/{region}_tracts.parquet"); nT = len(T)
HU = T.housing_units.fillna(0).values.astype("float64")
G = pd.read_parquet(f"{WORK}/{region}_bldg.parquet", columns=["bidx", "dataset", "class", "subtype", "upd_year"])
def variant(snapname, bresname):
    S = pd.read_parquet(f"{WORK}/{region}_{snapname}_snap.parquet", columns=["bidx", "tract_i", "node", "dist_m", "cand"])
    R = pd.read_parquet(f"{WORK}/{bresname}_bres.parquet", columns=["bidx", "egress", "top_eq"])
    assert (S.bidx.values == R.bidx.values).all()
    ti = S.tract_i.values.astype("int64"); cand = S.cand.values & (ti >= 0)
    near = cand & (S.node.values >= 0) & (S.dist_m.values <= 500)
    s30 = near & (R.egress.values == 1) & (R.top_eq.values >= 30)
    return S, ti, cand, near, s30
S0, ti, cand, near0, s30_0 = variant("drv", f"{region}_drv_A")
nc = np.bincount(ti[cand], minlength=nT).astype("float64")
dw = np.zeros(len(S0)); dw[cand] = HU[ti[cand]] / nc[ti[cand]]
assert (G.bidx.values == S0.bidx.values).all()
log("baseline S30 dwellings", round(dw[s30_0].sum()), "of near", round(dw[near0].sum()), "= share", round(dw[s30_0].sum() / dw[near0].sum(), 4))
# ---------- (1) concordance with sensitivity variants
conc = {"region": region, "base_S30_dw": dw[s30_0].sum(), "base_den": dw[near0].sum()}
flags = {}
try:
    _, _, _, near_p, s30_p = variant("drvplus", f"{region}_drvplus_A"); flags["plus"] = s30_p; conc["plus_S30_dw"] = dw[s30_p].sum(); conc["plus_den"] = dw[near_p].sum()
except FileNotFoundError as e:
    log("no drvplus variant", e)
_, _, _, near_r, s30_r = variant("drv", f"{region}_drv_A_r25"); flags["r25"] = s30_r; conc["r25_S30_dw"] = dw[s30_r].sum(); conc["r25_den"] = dw[near_r].sum()
rob = s30_0.copy()
for k, f in flags.items():
    conc[f"flips_{k}_dw"] = dw[s30_0 & ~f].sum(); rob &= f
    conc[f"new_{k}_dw"] = dw[f & ~s30_0].sum()
conc["robust_all_dw"] = dw[rob].sum()
if "plus" in flags and "r25" in flags: conc["flips_either_dw"] = dw[s30_0 & ~(flags["plus"] & flags["r25"])].sum()
pd.DataFrame([conc]).to_csv(f"{WORK}/cb_{region}_conc.csv", index=False); log("conc", {k: round(v, 3) if isinstance(v, float) else v for k, v in conc.items()})
# ---------- (2) provenance of trapped vs other homes (baseline), sufficient statistics per tract
ds = G.dataset.fillna("unknown").values
ML = np.isin(ds, ["Microsoft ML Buildings", "Google Open Buildings"])
ind = {"ml": ML, "noclass": G["class"].isna().values, "nosub": G.subtype.isna().values, "old": (G.upd_year.fillna(0).values <= 2021)}
log("dataset mix (near candidates):", pd.Series(ds[near0]).value_counts(normalize=True).round(3).head(6).to_dict())
rows = []
for grp, m in (("trapped", s30_0), ("other", near0 & ~s30_0)):
    d = pd.DataFrame({"t": ti[m], "dw": dw[m], **{k: dw[m] * v[m] for k, v in ind.items()}}).groupby("t").sum()
    d.columns = [f"{grp}_{c}" for c in d.columns]; rows.append(d)
P = rows[0].join(rows[1], how="outer").fillna(0.0); P["GEOID"] = T.GEOID.values[P.index.values]; P["county"] = P.GEOID.str[:5]; P["region"] = region
P.to_parquet(f"{WORK}/cb_{region}_prov.parquet"); log("prov tracts", len(P))
# ---------- (3) attribute coverage of single egress links
tr = gpd.read_parquet(strata(region, "census-tracts")).to_crs(CRS_M)
Pc = pd.read_parquet(f"{WORK}/{region}_drv_pieces.parquet"); Sg = pd.read_parquet(f"{WORK}/{region}_drv_segs.parquet")
Pc = Pc.merge(Sg[["sidx", "named", "has_surface", "has_speed", "has_access_rule", "dataset", "upd_year", "is_abandoned", "is_construction"]], on="sidx", how="left")
Pc = Pc[~(Pc.is_abandoned.fillna(False) | Pc.is_construction.fillna(False))].reset_index(drop=True)
from spof import load_graph, sinks, run_graph
# single-egress-link segments from the CURRENT graph (same DFS + variants loads that produced the headline numbers). NOTE: work/<region>_drv_A_bridges.parquet / _bld.parquet are stale
# artefacts of the early analyze.py run (older node/segment/building numbering) and must NOT be joined to the current pieces/snap.
G2 = load_graph(region, "drv"); P2 = G2["P"]; sink_all, art, ex, deg, _ = sinks(G2, "A"); res, eu_all, ev_all = run_graph(G2, sink_all)
sub_eq = np.load(f"{WORK}/{region}_drv_A_nodes.npz")["sub_eq"]; pe = res["parent_edge"]; isb = res["is_bridge"]
c = np.where((pe >= 0) & (pe < len(P2)))[0]; c = c[isb[pe[c]] & (sub_eq[c] >= 30)]
s30_sidx = set(P2.sidx.values[pe[c]]); how = "DFS re-run + variants nodes.npz sub_eq"
log("S30 link segments", len(s30_sidx), "via", how)
Pc["load_dwell"] = np.where(Pc.sidx.isin(s30_sidx), 30.0, 0.0)
geoms = shapely.from_wkb(Pc.wkb.values); cen = shapely.centroid(shapely.make_valid(geoms) if False else geoms)
a, b = STRtree(tr.geometry.values).query(cen, predicate="intersects")
tmp = pd.DataFrame({"i": a, "t": b}).drop_duplicates("i"); Pc["t"] = -1; Pc.loc[tmp.i.values, "t"] = tmp.t.values
Pc = Pc[Pc.t >= 0].copy(); Pc["GEOID"] = tr.GEOID.values[Pc.t.values]
Pc["s30"] = Pc.load_dwell >= 30
attrs = {"named": Pc.named.fillna(False).astype(bool), "surface": Pc.has_surface.fillna(False).astype(bool), "speed": Pc.has_speed.fillna(False).astype(bool),
         "access": Pc.has_access_rule.fillna(False).astype(bool), "osm": Pc.dataset.fillna("").eq("OpenStreetMap"), "recent": Pc.upd_year.fillna(0).ge(2023)}
D = pd.DataFrame({"GEOID": Pc.GEOID.values, "cls": Pc.cls.values, "s30": Pc.s30.values, "L": Pc.len_m.values})
for k, v in attrs.items(): D[k] = D.L * v.values
agg = D.groupby(["GEOID", "cls", "s30"]).sum(numeric_only=True).unstack("s30", fill_value=0.0)
agg.columns = [f"{'S30' if c[1] else 'oth'}_{c[0]}" for c in agg.columns]; agg = agg.reset_index(); agg["county"] = agg.GEOID.str[:5]; agg["region"] = region
agg.to_parquet(f"{WORK}/cb_{region}_link.parquet"); log("link strata", len(agg), "| S30 link km", round(Pc.len_m[Pc.s30].sum() / 1000, 1), "| other km", round(Pc.len_m[~Pc.s30].sum() / 1000, 1))
log("done")
