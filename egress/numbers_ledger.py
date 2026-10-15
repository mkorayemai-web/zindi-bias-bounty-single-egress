"""NUMBERS LEDGER: re-derives every number quoted in DISCOVERY_DRAFT.md from the saved tables / source documents and compares it with the value printed in the draft.
Each row: id | the exact text in the draft | quoted value | recomputed value | tolerance (half a unit of the last printed digit) | source (file or script) | status.
Status OK = the draft still contains that exact text AND the recomputed value agrees within tolerance. DRAFT-TEXT-MISSING = the text was edited (re-check it); MISMATCH = the number is wrong.
usage: numbers_ledger.py -> tables/numbers_ledger.csv, NUMBERS_LEDGER.md ; exit code 1 if anything is not OK.  Runs in seconds from the shipped tables (no package data needed)."""
import re, sys, glob, numpy as np, pandas as pd
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import *
import os
TEST_DRAFT = os.environ.get("LEDGER_TEST_DRAFT")           # self-test hook: run against a corrupted copy of the draft; outputs then go to LEDGER_TEST_OUT, never into the lane
OUTDIR = os.environ.get("LEDGER_TEST_OUT", LANE) if TEST_DRAFT else LANE; os.makedirs(OUTDIR, exist_ok=True)
DRAFT = open(TEST_DRAFT or f"{LANE}/DISCOVERY_DRAFT.md").read(); rows = []
T = lambda f, **k: pd.read_csv(f"{OUT}/{f}", **k)
def add(cid, needle, quoted, value, tol, src):
    present = needle in DRAFT; ok = present and (abs(quoted - value) <= tol + 1e-9)
    rows.append(dict(id=cid, draft_text=needle, quoted=quoted, recomputed=float(value), tolerance=tol, source=src, status="OK" if ok else ("DRAFT-TEXT-MISSING" if not present else "MISMATCH")))
def flag(cid, needle, cond, desc, src):                                   # qualitative claim: boolean condition
    present = needle in DRAFT; rows.append(dict(id=cid, draft_text=needle, quoted=np.nan, recomputed=float(bool(cond)), tolerance=np.nan, source=f"{src} [{desc}]", status="OK" if (present and cond) else ("DRAFT-TEXT-MISSING" if not present else "MISMATCH")))
def has(cid, needle, path, pattern, src):                                 # external document must contain the figure
    if not os.path.exists(path): return rows.append(dict(id=cid, draft_text=needle, quoted=np.nan, recomputed=np.nan, tolerance=np.nan, source=f"{src} [source document not distributed with the repository: fetch it as listed in SOURCES.md]", status="SKIPPED-NO-SOURCE"))
    txt = re.sub(r"<[^>]+>", " ", open(path, errors="ignore").read()); txt = re.sub(r"\s+", " ", txt); ok = re.search(pattern, txt, re.S) is not None
    rows.append(dict(id=cid, draft_text=needle, quoted=np.nan, recomputed=float(ok), tolerance=np.nan, source=src, status="OK" if (needle in DRAFT and ok) else ("DRAFT-TEXT-MISSING" if needle not in DRAFT else "MISMATCH")))
# ------------------------------------------------------------------ Finding 1
B = T("stats_burden_drv_A.csv").set_index("group"); P = B.loc["pooled"]; S = "stats_burden_drv_A.csv (pooled row; stats.py)"
add("F1.01", "17.0 M dwellings", 17.0, P.dwellings / 1e6, 0.05, S); add("F1.02", "39.9 M people", 39.9, P.persons / 1e6, 0.05, S)
add("F1.03", "21.3 % reach the arterial network", 21.3, 100 * P.dwell_single / P.dwellings, 0.05, S); add("F1.04", "**9.9 % (1.68 M dwellings", 9.9, 100 * P.dwell_S30 / P.dwellings, 0.05, S)
add("F1.05", "1.68 M dwellings", 1.68, P.dwell_S30 / 1e6, 0.005, S); add("F1.06", "3.76 M people", 3.76, P.pers_S30 / 1e6, 0.005, S)
add("F1.07", "806 k behind links", 806, P.dwell_S100 / 1e3, 0.5, S); add("F1.08", "277 k 300+", 277, P.dwell_S300 / 1e3, 0.5, S)
for i, (nd, rg, q) in enumerate([("N. California 10.7 %", "northern-ca", 10.7), ("E. Oklahoma 6.5 %", "eastern-ok", 6.5), ("Maricopa 9.8 %", "maricopa-az", 9.8), ("S-C Texas 10.5 %", "south-central-tx", 10.5), ("E. Washington 7.5 %", "eastern-wa", 7.5)]):
    add(f"F1.1{i}", nd, q, 100 * B.loc[rg, "dwell_S30"] / B.loc[rg, "dwellings"], 0.05, S + f" region {rg}")
# ------------------------------------------------------------------ who
SC = T("seasonal_contrasts.csv"); pc = SC[(SC.group == "pooled") & (SC.metric == "S30 (dwellings)")].iloc[0]; D = T("seasonal_dose.csv")
nd = "(ACS B25004; 612 of 9,712)"; add("W.01", nd, 612, pc.n_tracts_hi, 0.5, "seasonal_contrasts.csv pooled n_tracts_hi (seasonal.py)"); add("W.02", nd, 9712, D.tracts.sum(), 0.5, "seasonal_dose.csv sum(tracts) (seasonal2.py)")
CB = T("county_boot.csv").set_index("contrast"); r = CB.loc["Resort-type (>=10% seasonal) vs other"]; S = "county_boot.csv (county_boot.py, county-clustered bootstrap)"
add("W.03", "**2.15x**", 2.15, r.ratio, 0.005, S); nd = "(19.9 % vs 9.2 %; 95 % CI 1.86-2.57, resampling 325 counties)"
add("W.04", nd, 19.9, 100 * r.share_a, 0.05, S); add("W.05", nd, 9.2, 100 * r.share_b, 0.05, S); add("W.06", nd, 1.86, r.lo, 0.005, S); add("W.07", nd, 2.57, r.hi, 0.005, S); add("W.08", nd, 325, r.counties, 0.5, S)
nd = "from 8.9 % (<2 % seasonal) to 29 % (50 %+)"; add("W.09", nd, 8.9, 100 * D.S30_share.iloc[0], 0.05, "seasonal_dose.csv"); add("W.10", nd, 29, 100 * D.S30_share.iloc[-1], 0.5, "seasonal_dose.csv")
m = CB.loc["Mobile-home share Q4 vs Q1"]; nd = "Top vs bottom mobile-home-share quartile: 2.07x (1.69-2.56)"
add("W.11", nd, 2.07, m.ratio, 0.005, S); add("W.12", nd, 1.69, m.lo, 0.005, S); add("W.13", nd, 2.56, m.hi, 0.005, S)
F = T("fac_stats_drv_A.csv"); f = T("county_boot_facilities.csv").set_index("kind").loc["mobile_home_park"]; nd = "1.77x as often as all dwellings in their tracts (23.5 % vs 13.3 %; 1.58-1.98)"; S = "county_boot_facilities.csv mobile_home_park (county_boot_facilities.py, county-clustered; point estimate = fac_stats.py pooled S30)"
add("W.14", nd, 1.77, f.ratio, 0.005, S); add("W.15", nd, 23.5, 100 * f.fac_share, 0.05, S); add("W.16", nd, 13.3, 100 * f.tract_share, 0.05, S); add("W.17", nd, 1.58, f.lo, 0.005, S); add("W.18", nd, 1.98, f.hi, 0.005, S)
v = CB.loc["SVI Q4 vs Q1"]; nd = "(top vs bottom quartile 0.60x, 0.49-0.73)"; add("W.19", nd, 0.60, v.ratio, 0.005, S.split(",")[0]); add("W.20", nd, 0.49, v.lo, 0.005, "county_boot.csv"); add("W.21", nd, 0.73, v.hi, 0.005, "county_boot.csv")
# ------------------------------------------------------------------ why the scorecard cannot see it
K = T("single_egress_km_by_class.csv").set_index("road_class"); tot = K.s30_km.sum() * 1000.0; sc4 = K.loc[[c for c in ["motorway", "trunk", "primary", "secondary"] if c in K.index]].s30_km.sum() * 1000.0; S = "single_egress_km_by_class.csv (egress_km_by_class.py from work/cb_<region>_link.parquet): length of single-egress link segments by road class"
add("S.01", "0.0 % of the 10,951 km", 10951, tot / 1000, 0.5, S); add("S.02", "0.0 % of the 10,951 km", 0.0, 100 * sc4 / tot, 0.05, S); add("S.03", "(81 % are residential)", 81, 100 * K.loc["residential"].s30_km * 1000.0 / tot, 0.5, S)
Z = T("s30_in_tracts_without_scorecard_roads.csv"); add("S.04", "97.9 % of S30 dwellings", 97.9, 100 * (1 - Z.s30_dw_in_those.sum() / Z.s30_dw.sum()), 0.05, "s30_in_tracts_without_scorecard_roads.csv (s30_scorecard_tracts.py: 1 - share of S30 dwellings in tracts with no motorway..secondary graph link)")
# ------------------------------------------------------------------ Finding 2
PP = T("persons_per_dwelling_ci.csv").iloc[0]; S = "persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap)"; nd = "**1.10 census persons per dwelling (0.97-1.24) vs 2.34 (2.28-2.39)**"
for i, (q, val) in enumerate([(1.10, PP.hi_ppd), (0.97, PP.hi_lo), (1.24, PP.hi_hi), (2.34, PP.lo_ppd), (2.28, PP.lo_lo), (2.39, PP.lo_hi)]): add(f"B.0{i+1}", nd, q, val, 0.005, S)
nd = "(ratio 0.47, 0.41-0.53; 185 counties)"
for i, (q, val, t) in enumerate([(0.47, PP.ratio, 0.005), (0.41, PP.ratio_lo, 0.005), (0.53, PP.ratio_hi, 0.005), (185, PP.counties, 0.5)]): add(f"B.0{i+7}", nd, q, val, t, S)
add("B.11", "(low 1.2, mid 2.34, high 3.5; an assumption)", 2.34, PP.lo_ppd, 0.005, "mid q = observed year-round persons per dwelling in <2 % seasonal clusters")
SL = T("seasonal_load_summary.csv").set_index("group"); g = SL.loc["tracts >=25% seasonal (allocation least biased)"]; S = "seasonal_load_summary.csv (seasonal_load.py)"; AR = T("seasonal_alloc_robust.csv").set_index("min_coverage")
add("B.12", "the 176 such links", 176, g.clusters, 0.5, S); nd = "**47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)**"
for i, (q, val, t) in enumerate([(47.9, g.census_persons / 1e3, 0.05), (70, g.peak_low / 1e3, 0.5), (91, g.peak_mid / 1e3, 0.5), (112, g.peak_high / 1e3, 0.5), (1.5, g.ratio_low, 0.05), (1.9, g.ratio_mid, 0.05), (2.3, g.ratio_high, 0.05)]): add(f"B.{13+i}", nd, q, val, t, S)
a0 = AR.loc[0.0]; add("B.20", nd, 1.73, a0.x_mid_lo, 0.005, "seasonal_alloc_robust.csv min_coverage=0 (county-clustered CI)"); add("B.21", nd, 2.10, a0.x_mid_hi, 0.005, "seasonal_alloc_robust.csv"); add("B.22", nd, 43, a0.counties, 0.5, "seasonal_alloc_robust.csv")
g5 = SL.loc["tracts >=50% seasonal"]; nd = "2.2-4.4x where seasonal housing is 50 %+"; add("B.23", nd, 2.2, g5.ratio_low, 0.05, S); add("B.24", nd, 4.4, g5.ratio_high, 0.05, S)
ga = SL.loc["all single-link clusters (>=100 dw), 5 regions"]; nd = "Across the 3,931 single-link clusters (100+ dwellings, census residents) the gap is only 3-8 %"; add("B.25", nd, 3931, ga.clusters, 0.5, S); add("B.26", nd, 3, 100 * (ga.ratio_low - 1), 0.5, S); add("B.27", nd, 8, 100 * (ga.ratio_high - 1), 0.5, S)
a25 = AR.loc[0.25]; nd = "the 18 links serving a quarter or more of their tract's housing give 1.4x / 1.8x / 2.2x"; S = "seasonal_alloc_robust.csv min_coverage=0.25 (seasonal_alloc_robust.py)"
for i, (q, val) in enumerate([(18, a25.clusters), (1.4, a25.x_low), (1.8, a25.x_mid), (2.2, a25.x_high)]): add(f"B.{28+i}", nd, q, val, 0.5 if q == 18 else 0.05, S)
# ------------------------------------------------------------------ note on q (external planning references; saved copies in ext/q_sources)
mt = f"{LANE}/ext/q_sources/mammoth_eagle_lodge_deir_s3-8.txt"; hs = f"{LANE}/ext/q_sources/collier_lee_hes1987.htm"; S = "Mammoth Lakes Eagle Lodge Draft EIR s3.8 (SOURCES.md row 9)"
has("Q.01", "4.0 persons per occupied second-home or visitor unit", mt, r"person/unit occupancy of 4\.0 was applied to all remaining visitor, second home", S)
has("Q.02", "occupied 49 % of the year", mt, r"occupied about 25\.7\s+weeks on average, or 49% of the year", S); has("Q.03", "34,265 persons", mt, r"average peak PAOT in 2004 was 34,265", S); has("Q.04", "7,259 residents", mt, r"approximately 7,259 people were\s+residents", S)
has("Q.05", "51-64 % for condominiums and 43-75 % for mobile homes", hs, r"Condominium \(Conventional\) 51\.0 64\.0 Mobile Home 43\.0 75\.0", "SW Florida RPC Hurricane Evacuation Study Update 1987 (SOURCES.md row 10)")
for i, (q, val) in enumerate([(30, 100 * 1.2 / 4.0), (59, np.floor(100 * 2.34 / 4.0 + 0.5)), (88, np.floor(100 * 3.5 / 4.0 + 0.5))]): add(f"Q.0{6+i}", "4.0 persons at 30 / 59 / 88 % occupancy", q, val, 0.5, "arithmetic: q / 4.0 persons per occupied unit")
# ------------------------------------------------------------------ named places table
R = T("seasonal_load_range.csv", dtype={"tract": str})
for i, (lab, rn, tr) in enumerate([("Walden Rd, Lake Conroe TX", "Walden Road", "48339694305"), ("Cranes Mill Rd, Canyon Lake TX", "Cranes Mill Road", "48091310608"), ("Queen Isabella Causeway, South Padre TX", "Queen Isabella Causeway", "48061012305"),
                                   ("E 310 Rd, Grand Lake OK", "East 310 Road", "40041375804"), ("Alpine Meadows Rd, Olympic Valley CA", "Alpine Meadows Road", "06061022014"), ("Mountainaire Rd, Flagstaff AZ", "Mountainaire Road", "04005001500")]):
    x = R[(R.rname == rn) & (R.tract == tr)].sort_values("load_dwell", ascending=False).iloc[0]; txt = f"|{lab}|{tr}|{x.load_dwell:,.0f}|{x.load_persons:,.0f}|{x.peak_low:,.0f}-{x.peak_high:,.0f}|"
    flag(f"N.0{i+1}", txt, txt in DRAFT, "table row regenerated from seasonal_load_range.csv", "seasonal_load_range.csv (seasonal_load.py)")
flag("N.07", "per-link lists for all regions are in `tables/<region>_drv_A_links.csv`", all(os.path.exists(f"{LANE}/tables/{r}_drv_A_links.csv") for r in ["northern-ca", "eastern-ok", "maricopa-az", "south-central-tx", "eastern-wa"]), "the five per-region link lists exist in tables/", "tables/<region>_drv_A_links.csv")
# ------------------------------------------------------------------ comparisons and controls
sr = SC[(SC.metric == "S30 (dwellings)") & (SC.group != "pooled")]; nd = "(1.6x N. California to 4.8x E. Oklahoma, all CIs above 1)"; S = "seasonal_contrasts.csv per region (seasonal.py, tract bootstrap)"
add("C.01", nd, 1.6, sr.ratio.min(), 0.05, S); add("C.02", nd, 4.8, sr.ratio.max(), 0.05, S); flag("C.03", nd, (sr.ratio_lo > 1).all(), "every region's 95 % CI above 1", S)
RU = T("seasonal_rural_urban.csv").set_index("subset"); nd = "within rural-only (1.84x, 1.62-2.06) and urban-only (2.17x, 1.89-2.47) tracts"; S = "seasonal_rural_urban.csv (seasonal2.py, default bootstrap 1000)"
for i, (q, val) in enumerate([(1.84, RU.loc["rural tracts only"].ratio), (1.62, RU.loc["rural tracts only"].ratio_lo), (2.06, RU.loc["rural tracts only"].ratio_hi), (2.17, RU.loc["urban tracts only"].ratio), (1.89, RU.loc["urban tracts only"].ratio_lo), (2.47, RU.loc["urban tracts only"].ratio_hi)]): add(f"C.0{4+i}", nd, q, val, 0.005, S)
rb = T("seasonal_robust.csv"); rb = rb[(rb.config == "drv_A") & (rb.scheme == "eq") & (rb.metric == "S30") & (rb.threshold.isin([0.05, 0.10, 0.20]))]; flag("C.10", "at 5, 10 and 20 % thresholds", len(rb) == 3 and (rb.lo > 1).all(), "ratios 1.86 / 2.38 / 2.97, CIs above 1", "seasonal_robust.csv (seasonal_robust.py)")
G = T("seasonal_regress.csv"); gg = G[(G.group == "pooled") & (G.spec == "+ controls + county FE")].iloc[0]; nd = "(+3.3 points of S30 per +10 points of seasonal share, 1.95-4.68; +3.9, 2.6-5.3 with road density)"; S = "seasonal_regress.csv pooled '+ controls + county FE' (seasonal.py)"
add("C.11", nd, 3.3, gg.pp_S30_per_10pp_seasonal, 0.05, S); add("C.12", nd, 1.95, gg.lo, 0.005, S); add("C.13", nd, 4.68, gg.hi, 0.005, S)
DR = T("density_dissoc_regress.csv"); dd = DR[(DR.group == "pooled") & (DR.spec == "with log road density") & (DR.term == "seas")].iloc[0]; S = "density_dissoc_regress.csv pooled 'with log road density' (density_dissoc.py)"
add("C.14", nd, 3.9, dd.pp, 0.05, S); add("C.15", nd, 2.6, dd.lo, 0.05, S); add("C.16", nd, 5.3, dd.hi, 0.05, S)
# ------------------------------------------------------------------ validation (parsed from the saved summaries)
tt = open(f"{OUT}/validation_tehama_summary.txt").read(); hh = open(f"{OUT}/validation_hays_summary.txt").read()
mt_ = re.search(r"matched (\d+)/(\d+)", tt); sp = re.search(r"Spearman\([^)]*\) = ([0-9.]+) \(p=([0-9.e+-]+)", tt); b20 = re.search(r">= 20 dwellings: documented [0-9.]+ \((\d+)/(\d+)\) vs base rate ([0-9.]+)", tt)
S = "validation_tehama_summary.txt (validate_tehama.py)"; nd = "27 of 32 documented single-access areas matched"; add("V.01", nd, 27, int(mt_.group(1)), 0.5, S); add("V.02", nd, 32, int(mt_.group(2)), 0.5, S)
nd = "Spearman 0.86 (p = 8e-9)"; add("V.03", nd, 0.86, float(sp.group(1)), 0.005, S); add("V.04", nd, 8e-9, float(sp.group(2)), 0.1e-8, S)
nd = "22 of 27 have 20+ dwellings behind one link vs 30.7 % of named roads"; add("V.05", nd, 22, int(b20.group(1)), 0.5, S); add("V.06", nd, 27, int(b20.group(2)), 0.5, S); add("V.07", nd, 30.7, 100 * float(b20.group(3)), 0.05, S)
S = "validation_hays_summary.txt (validate_hays.py)"; tab = re.search(r"\[\[(\d+),(\d+)\],\[(\d+),(\d+)\]\]", hh); auc = re.search(r"AUC .*? = ([0-9.]+)", hh); fp = re.search(r"Fisher exact p=([0-9.e+-]+)", hh)
nd = "AUC 0.854, Fisher p = 3e-7; one-exit areas flagged 17/26 vs multi-exit 1/31"; a, b, c, d_ = map(int, tab.groups())
add("V.08", nd, 0.854, float(auc.group(1)), 0.0005, S); add("V.09", nd, 3e-7, float(fp.group(1)), 0.1e-6, S); add("V.10", nd, 17, a, 0.5, S); add("V.11", nd, 26, a + b, 0.5, S); add("V.12", nd, 1, c, 0.5, S); add("V.13", nd, 31, c + d_, 0.5, S)
# ------------------------------------------------------------------ how much is the map's own fault
FS = T("false_single_access.csv").set_index("region"); p = FS.loc["pooled"]; reg = FS.drop(index="pooled"); S = "false_single_access.csv pooled (coverage_bridge_agg.py / sens_nearmiss2.py / run_tx_plus.sh)"
nd = "removes only 3.9 % of S30 dwellings (3-8 % by region)"; add("M.01", nd, 3.9, p.flips_with_repair25_pct, 0.05, S); add("M.02", nd, 3, reg.flips_with_repair25_pct.min(), 0.5, S); add("M.03", nd, 8, reg.flips_with_repair25_pct.max(), 0.5, S)
nd = "admitting service and track roads 25 %, either 28 %: 72 % survives both"; add("M.04", nd, 25, p.flips_with_service_track_pct, 0.5, S); add("M.05", nd, 28, p.flips_either_pct, 0.5, S); add("M.06", nd, 72, p.robust_pct, 0.5, S)
CL = T("cov_bridge_links.csv"); cl = CL[(CL.group == "pooled") & (CL.indicator == "named")].iloc[0]; CBd = T("cov_bridge_buildings.csv"); cbm = CBd[(CBd.group == "pooled") & (CBd.indicator == "ml")].iloc[0]
nd = "(96.8 % vs 88.7 % for same-class roads in the tract)"; add("M.07", nd, 96.8, 100 * cl.P_trapped, 0.05, "cov_bridge_links.csv pooled named"); add("M.08", nd, 88.7, 100 * cl.P_same_tract_others, 0.05, "cov_bridge_links.csv")
nd = "(44.7 % vs 43.1 %)"; add("M.09", nd, 44.7, 100 * cbm.P_trapped, 0.05, "cov_bridge_buildings.csv pooled ml"); add("M.10", nd, 43.1, 100 * cbm.P_same_tract_others, 0.05, "cov_bridge_buildings.csv")
# ------------------------------------------------------------------ method
SG = T("sens_grid.csv"); sg = SG[(SG.classes == "scored classes") & (SG.sink.str.startswith("A")) & (SG.repair == "none") & (SG.scheme != "ACS dwellings")]; nd = "(alternative weights give S30 of 7.3-13.1 %)"
add("T.01", nd, 7.3, 100 * sg.S30.min(), 0.05, "sens_grid.csv (sens_table.py): area-weighted and structure-count weights, scored classes, sink A, no repair, all regions"); add("T.02", nd, 13.1, 100 * sg.S30.max(), 0.05, "sens_grid.csv")
# ------------------------------------------------------------------ impact
def load(rn, tr): return R[(R.rname == rn) & (R.tract == tr)].sort_values("load_dwell", ascending=False).iloc[0]
nd = "put 4,291, 2,840 and 2,299 dwellings"; S = "seasonal_load_range.csv"; add("I.01", nd, 4291, load("Walden Road", "48339694305").load_dwell, 0.5, S); add("I.02", nd, 2840, load("Cranes Mill Road", "48091310608").load_dwell, 0.5, S); add("I.03", nd, 2299, load("Old Conroe Road", "48339690501").load_dwell, 0.5, S)
has("I.04", "927 occupied housing units per egress lane", f"{LANE}/ext/nist_tn2252.txt", r"In Paradise, the OHU/Egress Lane ratio is 927", "NIST TN 2252 (SOURCES.md row 5)")
q = load("Queen Isabella Causeway", "48061012305"); al = load("Alpine Meadows Road", "06061022014"); nd = "(724 census persons) and Alpine Meadows Rd (301) the mid-case peak load is about 5x the census count (3,441 and 1,497)"
add("I.05", nd, 724, q.load_persons, 0.5, S); add("I.06", nd, 301, al.load_persons, 0.5, S); add("I.07", nd, 3441, q.peak_mid, 0.5, S); add("I.08", nd, 1497, al.peak_mid, 0.5, S); add("I.09", nd, 5, q.peak_mid / q.load_persons, 0.3, S + " (Queen Isabella 4.75x)"); add("I.10", nd, 5, al.peak_mid / al.load_persons, 0.3, S + " (Alpine Meadows 4.98x)")
ST = T("stranded.csv").set_index("region"); add("I.11", "98.3 % of S30 dwellings have no mapped fire or EMS station", 98.3, 100 * ST.loc["pooled"].share_no_fire_ems, 0.05, "stranded.csv pooled (stranded.py; top-level clusters of 30+ dwellings, facilities from fac_clusters_*.csv)")
NP = T("named_places_stations.csv"); nd_k = "as do five of the six places above and 500 of the 527 clusters of 300+ dwellings"; S_k = "named_places_stations.csv (named_station_check.py)"
add("K.01", nd_k, 5, NP.no_fire_ems.sum(), 0.5, S_k)
tab_k = {l.split("|")[1] for l in DRAFT.splitlines() if l.startswith("|") and not l.startswith("|---") and not l.startswith("|Single link")}
flag("K.02", nd_k, len(NP) == 6 and set(NP.place) == tab_k, "the six places of the draft's evidence table are exactly the six rows of named_places_stations.csv", S_k)
add("K.03", nd_k, 500, ST.loc["pooled"].clusters_ge300_no_fire_ems, 0.5, "stranded.csv pooled (stranded.py)")
add("K.04", nd_k, 527, ST.loc["pooled"].clusters_ge300, 0.5, "stranded.csv pooled (stranded.py)")
flag("K.05", nd_k, "clusters_ge300" in ST.columns, "300+ = the cluster-size threshold of the columns clusters_ge300 / clusters_ge300_no_fire_ems", "stranded.csv")
RS = T("resp_summary.csv"); rs = RS[(RS.variant == "strict") & (RS.region == "pooled")].iloc[0]; rb_ = RS[(RS.variant == "broad") & (RS.region == "pooled")].iloc[0]; ro = RS[(RS.variant == "strict") & (RS.region == "eastern-ok")].iloc[0]; S = "resp_summary.csv (response_time.py + resp_summary.py; strict = category fire_department)"
nd = "1.65x as likely (1.54-1.77)"; add("I.12", nd, 1.65, rs.ratio, 0.005, S); add("I.13", nd, 1.54, rs.ratio_lo, 0.005, S); add("I.14", nd, 1.77, rs.ratio_hi, 0.005, S)
nd = "(189-230 k dwellings; not in Oklahoma)"; add("I.15", nd, 189, rb_.both_dwellings / 1e3, 0.5, S + " broad"); add("I.16", nd, 230, rs.both_dwellings / 1e3, 0.5, S + " strict"); flag("I.17", nd, ro.ratio_lo <= 1 <= ro.ratio_hi, "Oklahoma 95 % CI contains 1", S)
DT = T("double_trap.csv"); nd = "69.5 k car-less households sit behind S30 links, 47.6 k with no transit stop within 800 m"; S = "double_trap.csv summed over the 5 regions (double_trap.py)"
add("I.18", nd, 69.5, DT.nocar_hh_S30.sum() / 1e3, 0.05, S); add("I.19", nd, 47.6, DT.nocar_hh_S30_no_stop.sum() / 1e3, 0.05, S)
# ------------------------------------------------------------------ differences from other entries / appendix / reproduction
dsd = T("density_dissoc.csv"); dp = dsd[(dsd.group == "pooled") & (dsd.subset == "all tracts")].iloc[0]; add("D.01", "(rho with S30 -0.33)", -0.33, dp.spearman_S30_vs_km_per_100km2, 0.005, "density_dissoc.csv pooled all tracts (density_dissoc.py)")
PH = T("pinholes_summary.csv").set_index("region").loc["pooled(5)"]; nd = "For 190 of 3,933 single-link clusters (100+ dwellings)"; S = "pinholes_summary.csv pooled(5) (pinhole_summary.py)"
add("A.01", nd, 190, PH["clusters_relieved50pct_gap<=25m"], 0.5, S); add("A.02", nd, 3933, PH.clusters_ge100, 0.5, S); add("A.03", "(512 at up to 50 m)", 512, PH["clusters_relieved50pct_gap<=50m"], 0.5, S)
TC = T("pinholes_top_candidates.csv", dtype={"tract": str}); ms = TC[TC.rname.eq("Mountain Shadows Boulevard")].sort_values("load_dw", ascending=False).iloc[0]
nd = "Mountain Shadows Boulevard, Redding (399 dwellings, 4.3 m)"; S = "pinholes_top_candidates.csv"
add("A.04", nd, 399, ms.load_dw, 0.5, S); add("A.05", nd, 4.3, ms.min_gap_m, 0.05, S)
import duckdb; flag("R.01", "Python 3.12, DuckDB 1.5.4", sys.version_info[:2] == (3, 12) and duckdb.__version__.startswith("1.5.4"), f"python {sys.version.split()[0]}, duckdb {duckdb.__version__}", "runtime of this ledger run")
# ------------------------------------------------------------------ parameters quoted in the draft must be the ones the code uses
def codehas(cid, needle, path, pattern, desc):
    ok = re.search(pattern, open(path, errors="ignore").read()) is not None; rows.append(dict(id=cid, draft_text=needle, quoted=np.nan, recomputed=float(ok), tolerance=np.nan, source=f"{os.path.relpath(path, LANE)} [{desc}]", status="OK" if (needle in DRAFT and ok) else ("DRAFT-TEXT-MISSING" if needle not in DRAFT else "MISMATCH")))
E_ = f"{LANE}/egress"
codehas("P.01", "Buildings of 35 m2+ snap within 500 m", f"{E_}/pipeline.py", r"area_m2\.values >= 35\)", "building footprint >= 35 m2"); codehas("P.02", "Buildings of 35 m2+ snap within 500 m", f"{E_}/variants.py", r"S\.dist_m\.values <= 500\)", "snap distance <= 500 m")
codehas("P.03", "no transit stop within 800 m", f"{E_}/double_trap.py", r"THR = 800\.0", "transit radius"); codehas("P.04", "dwellings over 10 minutes (free-flow)", f"{E_}/resp_summary.py", r"threshold 10 min", "10 min free-flow drive time")
codehas("P.05", "circles = 40 largest links", f"{E_}/figs_regions.py", r"ntop=40", "circles drawn for the 40 largest links"); codehas("P.06", "the 12 links with most second homes", f"{E_}/seasonal_load.py", r"seas_share >= 0\.25\].sort_values\(\"seasonal_units\", ascending=False\)\.head\(12\)", "fig 3: 12 links, tracts >= 25 % seasonal, ranked by seasonal units")
codehas("P.07", "seed 20261014", f"{E_}/common.py", r"SEED = 20261014", "seed"); codehas("P.08", "Overture 2026-08-19.0", f"{LANE}/SOURCES.md", r"Overture 2026-08-19\.0", "release named in SOURCES.md")
codehas("P.09", "(IFC D107.1)", f"{LANE}/SOURCES.md", r"Section D107\.1 \(only the 30-dwelling threshold is cited", "IFC D107.1 row, 30-dwelling threshold")
codehas("P.13", "Drivable Overture roads (no service/track)", f"{E_}/common.py", r"DRV = SCORED \+ \(\"living_street\",\)", "main graph = DRV classes (the 7 scored classes + living_street); DRVPLUS adds service and track in the sensitivity run")
codehas("P.14", "(no service/track)", f"{E_}/common.py", r"DRVPLUS = DRV \+ \(\"service\", \"track\"\)", "service and track roads are only in DRVPLUS")
codehas("P.15", "tracts with roads of those classes", f"{E_}/s30_scorecard_tracts.py", r"ART = set\(ARTERIAL_A\)", "classes = ARTERIAL_A = motorway, trunk, primary, secondary (egress/common.py)")
flag("P.10", "57 neighbourhoods", len(pd.read_csv(f"{LANE}/ext/hays_table1.csv")) == 57, "ext/hays_table1.csv has 57 rows", "Ramos & Yuan 2024 Table 1")
flag("P.11", "S30", abs(ST.loc["pooled"].s30_dwellings - P.dwell_S30) < 1.0, "S30 = dwellings in top-level clusters of >= 30 dwellings (stranded.py asserts this per region)", "stranded.csv vs stats_burden_drv_A.csv")
add("M.11", "so 3.9 % bounds the gap-induced part", 3.9, p.flips_with_repair25_pct, 0.05, "false_single_access.csv pooled")
has("Q.09", "(Eagle Lodge Draft EIR, 2006)", mt, r"Draft Environmental Impact Report.{0,400}2006|September 2006|2006012041", "Mammoth EIR carries the year 2006"); has("Q.10", "A 1987 Southwest Florida hurricane evacuation study", hs, r"1987", "HES document is the 1987 update")
has("P.12", "in the 2018 Camp Fire (NIST TN 2252)", f"{LANE}/ext/nist_tn2252.txt", r"Camp Fire.{0,2000}2018|2018.{0,2000}Camp Fire", "NIST TN 2252 is the 2018 Camp Fire case study")
PF = f"{LANE}/PREFLIGHT_eastern-wa.txt"; pf_txt = open(PF).read() if os.path.exists(PF) else ""; m_ = re.search(r"region chain: (\d+) s", pf_txt)
flag("R.02", "(E. Washington about 1 minute)", bool(m_) and int(m_.group(1)) <= 90 and "PREFLIGHT PASS" in pf_txt, f"clean-room pre-flight: region chain {m_.group(1) if m_ else 'n/a'} s, PREFLIGHT PASS present: {'PREFLIGHT PASS' in pf_txt}", "PREFLIGHT_eastern-wa.txt (egress/preflight.sh)")
# ------------------------------------------------------------------ M3s: one number per contrast (text = the table behind Fig. 5), Fig. 6 panel titles, novelty counts
FT = T("effects_forest_county.csv").set_index("row"); S = "effects_forest_county.csv (figs_forest.py: the table behind Fig. 5)"
for cid, rw, nd_, qs in [("G.01", "Resort-type tracts (10%+ seasonal) vs others", "**2.15x** the S30 exposure of others (19.9 % vs 9.2 %; 95 % CI 1.86-2.57, resampling 325 counties)", (2.15, 1.86, 2.57)),
                         ("G.04", "Mobile-home share Q4/Q1 (tract)", "Top vs bottom mobile-home-share quartile: 2.07x (1.69-2.56)", (2.07, 1.69, 2.56)),
                         ("G.07", "High-SVI vs low-SVI tracts (Q4/Q1)", "(top vs bottom quartile 0.60x, 0.49-0.73)", (0.60, 0.49, 0.73)),
                         ("G.10", "Mobile-home parks vs their tract's dwellings", "1.77x as often as all dwellings in their tracts (23.5 % vs 13.3 %; 1.58-1.98)", (1.77, 1.58, 1.98))]:
    n0 = int(cid.split(".")[1])
    for k, (col, q_) in enumerate(zip(("ratio", "lo", "hi"), qs)): add(f"G.{n0 + k:02d}", nd_, q_, FT.loc[rw, col], 0.005, S)
flag("G.13", "county-clustered bootstrap 95 % CIs", bool(FT.source.str.startswith("county_boot").all()) and len(FT) == 12, "all 12 rows of the Fig. 5 table come from county-clustered tables", S)
LB = open(f"{OUT}/fig3_validation_labels.txt").read(); S = "fig3_validation_labels.txt (figs_m1.py: the panel titles of Fig. 6)"
flag("V.14", "22 of 27 have 20+ dwellings behind one link", "22 of 27 have 20+ dwellings behind one link" in LB, "the Fig. 6 Tehama title states the text's count", S)
flag("V.15", "Spearman 0.86", "Spearman 0.86 (n=27)" in LB, "the Fig. 6 Tehama title states the text's rho", S)
flag("V.16", "AUC 0.854", "AUC 0.854" in LB, "the Fig. 6 Hays title states the text's AUC", S)
NV = open(f"{LANE}/NOVELTY.md").read()
flag("N.08", "None of the 68 forum threads searched", bool(re.search(r"text of the 68 public forum posts", NV)) and all(x in NV for x in ("34925", "35030", "35033", "34910")), "NOVELTY.md records the 68-thread greps and their only hits", "NOVELTY.md")
# ------------------------------------------------------------------ output
LG = pd.DataFrame(rows); assert LG.id.is_unique, f"duplicate ledger ids: {sorted(LG.id[LG.id.duplicated()].unique())}"; CSVDIR = OUTDIR if TEST_DRAFT else OUT; LG.to_csv(f"{CSVDIR}/numbers_ledger.csv", index=False); bad = LG[~LG.status.isin(["OK", "SKIPPED-NO-SOURCE"])]; nskip = int((LG.status == "SKIPPED-NO-SOURCE").sum())
# coverage: numeric tokens of the draft that lie outside every text span a check depends on
covered = np.zeros(len(DRAFT), bool)
for nd_ in {r_["draft_text"] for r_ in rows if r_["draft_text"] in DRAFT}:
    for mm in re.finditer(re.escape(nd_), DRAFT): covered[mm.start():mm.end()] = True
skip = np.zeros(len(DRAFT), bool); pos = 0
for ln in DRAFT.split("\n"):                                                # image links, headings and the title carry no data claims
    if ln.startswith(("![](", "#")): skip[pos:pos + len(ln)] = True
    pos += len(ln) + 1
IDCTX = re.compile(r"(Fig\.\s*$|\bS\s*$|\bB\s*$|\bTN\s*$|\bD\s*$|DuckDB\s*$|Python\s*$|\bm\s*$|\(\s*$|seed\s*$|EIR,\s*$|Draft EIR\)\s*$)")
unc = []
for mm in re.finditer(r"\d[\d,]*(?:\.\d+)?", DRAFT):
    if covered[mm.start():mm.end()].any() or skip[mm.start()]: continue
    pre = DRAFT[max(0, mm.start() - 14):mm.start()]; post = DRAFT[mm.end():mm.end() + 8]
    kind = "id/citation/parameter" if (IDCTX.search(pre) or re.match(r"\s*(m2\b|/\d{5}|\)\s*$)", post) or re.match(r"[./]\d", post)) else "REVIEW"
    unc.append((mm.group(), kind, DRAFT[max(0, mm.start() - 38):mm.end() + 30].replace("\n", " ")))
ntok = len(list(re.finditer(r"\d[\d,]*(?:\.\d+)?", DRAFT))); nrev = sum(1 for u in unc if u[1] == "REVIEW")
md = ["# NUMBERS_LEDGER.md (generated by egress/numbers_ledger.py - do not edit)", "", f"Every number quoted in DISCOVERY_DRAFT.md, re-derived from the saved tables or source documents. {len(LG)} checks, {int((LG.status == 'OK').sum())} OK, {nskip} skipped (source document not distributed), {len(bad)} not OK. Tolerance = half a unit of the last printed digit.", "",
      "| id | text in the draft | quoted | recomputed | source | status |", "|---|---|---|---|---|---|"]
for r_ in LG.itertuples():
    q_ = "-" if pd.isna(r_.quoted) else f"{r_.quoted:g}"; md.append(f"| {r_.id} | {r_.draft_text[:70].replace('|', '/')} | {q_} | {r_.recomputed:.4g} | {r_.source[:95].replace('|', '/')} | {r_.status} |")
open(f"{OUTDIR}/NUMBERS_LEDGER.md", "w").write("\n".join(md + ["", f"## Numbers in the draft not covered by any check ({len(unc)} of {len(list(re.finditer(r'[0-9][0-9,]*(?:[.][0-9]+)?', DRAFT)))} numeric tokens; {nrev} flagged REVIEW)", "",
      "Tokens outside every checked text span, with context. 'id/citation/parameter' = figure numbers, identifiers (S30, B25004, TN 2252, forum ids), software versions, units; REVIEW = anything else.", ""] + [f"- {t} [{k}] ...{c}..." for t, k, c in unc]) + "\n")
print(f"LEDGER: {len(LG)} checks | OK {int((LG.status == 'OK').sum())} | DRAFT-TEXT-MISSING {int((LG.status == 'DRAFT-TEXT-MISSING').sum())} | MISMATCH {int((LG.status == 'MISMATCH').sum())} | SKIPPED-NO-SOURCE {nskip} | numeric tokens in the draft {ntok}, uncovered {len(unc)} (REVIEW {nrev})")
for r_ in bad.itertuples(): print(f"  {r_.status:18s} {r_.id}: '{r_.draft_text[:70]}' quoted {r_.quoted} recomputed {r_.recomputed:.5g} tol {r_.tolerance}  [{r_.source[:60]}]")
sys.exit(1 if len(bad) else 0)
