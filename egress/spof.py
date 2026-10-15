"""SPOF (single point of failure) egress library — numpy/scipy/shapely only. Module version of analyze.py with sensitivity switches:
   cset: 'drv' (scored classes + living_street) | 'drvplus' (+ service, track)
   sink: 'A' (motorway,trunk,primary,secondary + region exits) | 'B' (motorway,trunk + region exits)
   repair_m: if set, dead-end nodes within repair_m of an unconnected road piece are snapped (piece split) before the analysis (digitising-gap repair)."""
import time, numpy as np, pandas as pd, shapely, geopandas as gpd
from shapely import STRtree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from common import *
from graphlib import dfs_bridges, sink_rooted_loads

NONRES_SUB = {"outbuilding", "agricultural", "commercial", "industrial", "transportation", "religious", "education", "civic", "service", "medical", "entertainment", "military"}
NONRES_CLS = {"garage", "garages", "shed", "carport", "roof", "barn", "greenhouse", "hangar", "cabin_shed", "service", "kiosk", "hut", "stable", "silo", "cowshed", "farm_auxiliary", "parking", "boathouse"}

def _fix_geoms(geoms):
    gt = shapely.get_type_id(geoms)
    for i in np.where(gt != 1)[0]:
        g = shapely.line_merge(geoms[i]) if gt[i] == 5 else geoms[i]
        if shapely.get_type_id(g) != 1:
            parts = shapely.get_parts(g)
            cs = np.vstack([np.asarray(p.coords) for p in parts]) if len(parts) else np.array([[0.0, 0.0], [0.0, 0.0]])
            g = shapely.linestrings(cs)
        geoms[i] = g
    return geoms

def load_graph(region, cset="drv", drop_unusable=True):
    P = pd.read_parquet(f"{WORK}/{region}_{cset}_pieces.parquet")
    S = pd.read_parquet(f"{WORK}/{region}_{cset}_segs.parquet")
    flagcols = [c for c in S.columns if c not in ("seg_id", "cls", "subclass", "seg_len_m")]
    P = P.merge(S[flagcols], on="sidx", how="left")
    if drop_unusable:
        P = P[~(P.is_abandoned.fillna(False) | P.is_construction.fillna(False))]
    P = P.reset_index(drop=True)
    n = int(max(P.u.max(), P.v.max())) + 1
    geoms = _fix_geoms(shapely.from_wkb(P.wkb.values))
    sp, ep = shapely.get_point(geoms, 0), shapely.get_point(geoms, -1)
    nx = np.zeros(n); ny = np.zeros(n)
    nx[P.u.values] = shapely.get_x(sp); ny[P.u.values] = shapely.get_y(sp)
    nx[P.v.values] = shapely.get_x(ep); ny[P.v.values] = shapely.get_y(ep)
    P = P.drop(columns=["wkb"])
    return dict(P=P, geoms=geoms, n=n, nx=nx, ny=ny, region=region, cset=cset)

def sinks(G, sinkv="A", exit_buffer=200):
    P, n, nx, ny, region = G["P"], G["n"], G["nx"], G["ny"], G["region"]
    sink_cls = ARTERIAL_A if sinkv == "A" else ARTERIAL_B
    isart = P.cls.isin(sink_cls).values
    art = np.unique(np.concatenate([P.u.values[isart], P.v.values[isart]]))
    deg = np.bincount(np.concatenate([P.u.values, P.v.values]), minlength=n)
    tr = gpd.read_parquet(strata(region, "census-tracts")).to_crs(CRS_M)
    ring = tr.union_all().boundary.buffer(exit_buffer); shapely.prepare(ring)
    ex = np.where(shapely.contains_xy(ring, nx, ny) & (deg == 1))[0]
    return np.unique(np.concatenate([art, ex])), art, ex, deg, tr

def near_miss_repair(G, sink_all, deg, r):
    """Return (eu, ev, info) with dead-end nodes snapped (piece split) to unconnected pieces within r metres."""
    P, geoms, n, nx, ny = G["P"], G["geoms"], G["n"], G["nx"], G["ny"]
    eu, ev = P.u.values.copy(), P.v.values.copy()
    dead = np.where((deg == 1) & ~np.isin(np.arange(n), sink_all))[0]
    pts = shapely.points(nx[dead], ny[dead])
    tree = STRtree(geoms)
    a, b = tree.query(pts, predicate="dwithin", distance=r)
    pair = pd.DataFrame({"d": dead[a], "p": b})
    pair = pair[(eu[pair.p.values] != pair.d.values) & (ev[pair.p.values] != pair.d.values)]
    if len(pair):
        pair["dist"] = shapely.distance(shapely.points(nx[pair.d.values], ny[pair.d.values]), geoms[pair.p.values])
        pair = pair.sort_values("dist").drop_duplicates("d").drop_duplicates("p")
    newu, newv = [], []
    drop = np.zeros(len(eu), dtype=bool)
    for d, p in zip(pair.d.values, pair.p.values):
        drop[p] = True
        newu += [eu[p], d]; newv += [d, ev[p]]
    eu2 = np.concatenate([eu[~drop], np.array(newu, dtype=eu.dtype)]); ev2 = np.concatenate([ev[~drop], np.array(newv, dtype=ev.dtype)])
    info = dict(dead_ends=len(dead), within_r=int(pair.d.nunique()) if len(pair) else 0, repaired=len(pair))
    return eu2, ev2, info, pair

def run_graph(G, sink_all, eu=None, ev=None):
    n = G["n"]
    if eu is None:
        eu, ev = G["P"].u.values, G["P"].v.values
    eu_all = np.concatenate([eu, np.full(len(sink_all), n)]); ev_all = np.concatenate([ev, sink_all])
    res = dfs_bridges(n + 1, eu_all, ev_all, root=n)
    return res, eu_all, ev_all

def load_buildings(region):
    B = pd.read_parquet(f"{WORK}/{region}_bldg.parquet")
    return B

def snap_buildings(G, B, max_d=1500):
    geoms, P, nx, ny = G["geoms"], G["P"], G["nx"], G["ny"]
    pts = shapely.points(B.x.values, B.y.values)
    tree = STRtree(geoms)
    ii, dd = tree.query_nearest(pts, max_distance=max_d, return_distance=True, all_matches=False)
    B = B.copy()
    B["piece"] = -1; B["dist_m"] = np.nan
    B.loc[ii[0], "piece"] = ii[1]; B.loc[ii[0], "dist_m"] = dd
    ok = B.piece.values >= 0
    pu = P.u.values[B.piece.values[ok]]; pv = P.v.values[B.piece.values[ok]]
    bx, by = B.x.values[ok], B.y.values[ok]
    du = (nx[pu] - bx) ** 2 + (ny[pu] - by) ** 2; dv = (nx[pv] - bx) ** 2 + (ny[pv] - by) ** 2
    B["node"] = -1; B.loc[ok, "node"] = np.where(du <= dv, pu, pv)
    B["nearest_cls"] = None; B.loc[ok, "nearest_cls"] = P.cls.values[B.piece.values[ok]]
    return B, pts

def assign_tract_and_weights(region, B, pts, tr=None):
    if tr is None:
        tr = gpd.read_parquet(strata(region, "census-tracts")).to_crs(CRS_M)
    ttree = STRtree(tr.geometry.values)
    a, b = ttree.query(pts, predicate="intersects")
    tmp = pd.DataFrame({"i": a, "t": b}).drop_duplicates("i")
    B["tract"] = None
    B.loc[tmp.i.values, "tract"] = tr.GEOID.values[tmp.t.values]
    cand = (B.area_m2 >= 35) & ~B.subtype.isin(NONRES_SUB) & ~B["class"].isin(NONRES_CLS)
    B["cand"] = cand
    acs = pd.read_parquet(ref(region, "census-acs-housing"), columns=["GEOID", "housing_units"])
    nc = B[B.cand & B.tract.notna()].groupby("tract").size().rename("n_cand")
    tw = acs.set_index("GEOID").join(nc, how="left")
    tw["w"] = np.where(tw.n_cand > 0, tw.housing_units / tw.n_cand, 0.0)
    B["w"] = 0.0
    m = B.cand & B.tract.notna()
    B.loc[m, "w"] = B.loc[m, "tract"].map(tw["w"]).fillna(0.0).values
    return B

def egress_classes(G, B, res, eu_all, ev_all, max_snap=500):
    n = G["n"]
    wd = np.zeros(n + 1); ws = np.zeros(n + 1)
    bn = B[(B.node >= 0) & (B.dist_m <= max_snap) & B.cand]
    np.add.at(wd, bn.node.values, bn.w.values); np.add.at(ws, bn.node.values, 1.0)
    (top_d, top_s), nb, topc, sub = sink_rooted_loads(n + 1, res, [wd, ws])
    reached = res["disc"] >= 0
    B = B.copy()
    okn = (B.node.values >= 0) & (B.dist_m.values <= max_snap)
    eg = np.full(len(B), -1)
    nd = np.where(okn, B.node.values, 0)
    r = reached[nd]
    eg[okn & ~r] = 0
    eg[okn & r & (nb[nd] >= 1)] = 1
    eg[okn & r & (nb[nd] == 0)] = 2
    B["egress"] = eg
    B["top_load_d"] = np.where(okn, top_d[nd], 0.0)
    B["top_load_s"] = np.where(okn, top_s[nd], 0.0)
    B["nb"] = np.where(okn, nb[nd], -1)
    return B, sub, topc

def tract_table(B):
    Bc = B[B.cand & B.tract.notna() & (B.w > 0)]
    near = Bc[Bc.egress >= 0]
    w2 = near.groupby("tract").w.sum()
    out = pd.DataFrame({"dwell": Bc.groupby("tract").w.sum(), "n_cand": Bc.groupby("tract").size()})
    out["dwell_near"] = w2
    out["w_isl"] = near[near.egress == 0].groupby("tract").w.sum() / w2
    out["w_spof"] = near[near.egress == 1].groupby("tract").w.sum() / w2
    for T in (10, 30, 100, 300, 1000):
        out[f"w_spof{T}"] = near[(near.egress == 1) & (near.top_load_d >= T)].groupby("tract").w.sum() / w2
    for d in (100, 250, 500):
        out[f"w_off{d}"] = Bc[Bc.dist_m > d].groupby("tract").w.sum() / out["dwell"]
    out["w_track"] = near[near.nearest_cls == "track"].groupby("tract").w.sum() / w2
    return out.fillna({c: 0.0 for c in out.columns if c.startswith("w_")})

def summarize(B, label=""):
    Bc = B[B.cand & B.tract.notna() & (B.w > 0) & (B.egress >= 0)]
    tot = Bc.w.sum()
    d = {"label": label, "dwell": tot, "isl": Bc.w[Bc.egress == 0].sum() / tot, "spof": Bc.w[Bc.egress == 1].sum() / tot}
    for T in (10, 30, 100, 300, 1000):
        d[f"spof{T}"] = Bc.w[(Bc.egress == 1) & (Bc.top_load_d >= T)].sum() / tot
    return d
