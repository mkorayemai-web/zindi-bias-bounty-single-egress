# Every printed-number ledger check: Linux full rebuild

Same draft and original tolerances. PASS means OK; FAIL is a real failed check; UNVERIFIED is SKIPPED-NO-SOURCE, NOT a pass.
Checks: 193/202 PASS, 0 FAIL, 9 UNVERIFIED.
Computed primary tables start empty and are all rebuilt. Documented shipped ACS extracts remain external INPUTS when raw national files are absent; see input_provenance.json and rebuild_state.json.

| Check | Status | Printed value | Linux value | Original tolerance | Text / source |
|---|---|---:|---:|---:|---|
| F1.01 | PASS | 17 | 17.0086478397077 | 0.05 | 17.0 M dwellings / stats_burden_drv_A.csv (pooled row; stats.py) |
| F1.02 | PASS | 39.9 | 39.9043663179194 | 0.05 | 39.9 M people / stats_burden_drv_A.csv (pooled row; stats.py) |
| F1.03 | PASS | 21.3 | 21.2951450769041 | 0.05 | 21.3 % reach the arterial network / stats_burden_drv_A.csv (pooled row; stats.py) |
| F1.04 | PASS | 9.9 | 9.88111604974808 | 0.05 | **9.9 % (1.68 M dwellings / stats_burden_drv_A.csv (pooled row; stats.py) |
| F1.05 | PASS | 1.68 | 1.68064423153449 | 0.005 | 1.68 M dwellings / stats_burden_drv_A.csv (pooled row; stats.py) |
| F1.06 | PASS | 3.76 | 3.76202702352381 | 0.005 | 3.76 M people / stats_burden_drv_A.csv (pooled row; stats.py) |
| F1.07 | PASS | 806 | 805.996529533142 | 0.5 | 806 k behind links / stats_burden_drv_A.csv (pooled row; stats.py) |
| F1.08 | PASS | 277 | 277.172247094957 | 0.5 | 277 k 300+ / stats_burden_drv_A.csv (pooled row; stats.py) |
| F1.10 | PASS | 10.7 | 10.6531367291005 | 0.05 | N. California 10.7 % / stats_burden_drv_A.csv (pooled row; stats.py) region northern-ca |
| F1.11 | PASS | 6.5 | 6.49859668503273 | 0.05 | E. Oklahoma 6.5 % / stats_burden_drv_A.csv (pooled row; stats.py) region eastern-ok |
| F1.12 | PASS | 9.8 | 9.78244008262691 | 0.05 | Maricopa 9.8 % / stats_burden_drv_A.csv (pooled row; stats.py) region maricopa-az |
| F1.13 | PASS | 10.5 | 10.5465140741613 | 0.05 | S-C Texas 10.5 % / stats_burden_drv_A.csv (pooled row; stats.py) region south-central-tx |
| F1.14 | PASS | 7.5 | 7.5167960101607 | 0.05 | E. Washington 7.5 % / stats_burden_drv_A.csv (pooled row; stats.py) region eastern-wa |
| W.01 | PASS | 612 | 612 | 0.5 | (ACS B25004; 612 of 9,712) / seasonal_contrasts.csv pooled n_tracts_hi (seasonal.py) |
| W.02 | PASS | 9712 | 9712 | 0.5 | (ACS B25004; 612 of 9,712) / seasonal_dose.csv sum(tracts) (seasonal2.py) |
| W.03 | PASS | 2.15 | 2.15428736021411 | 0.005 | **2.15x** / county_boot.csv (county_boot.py, county-clustered bootstrap) |
| W.04 | PASS | 19.9 | 19.8598678237767 | 0.05 | (19.9 % vs 9.2 %; 95 % CI 1.86-2.57, resampling 325 counties) / county_boot.csv (county_boot.py, county-clustered bootstrap) |
| W.05 | PASS | 9.2 | 9.21876449286826 | 0.05 | (19.9 % vs 9.2 %; 95 % CI 1.86-2.57, resampling 325 counties) / county_boot.csv (county_boot.py, county-clustered bootstrap) |
| W.06 | PASS | 1.86 | 1.85689971851637 | 0.005 | (19.9 % vs 9.2 %; 95 % CI 1.86-2.57, resampling 325 counties) / county_boot.csv (county_boot.py, county-clustered bootstrap) |
| W.07 | PASS | 2.57 | 2.5733251210976 | 0.005 | (19.9 % vs 9.2 %; 95 % CI 1.86-2.57, resampling 325 counties) / county_boot.csv (county_boot.py, county-clustered bootstrap) |
| W.08 | PASS | 325 | 325 | 0.5 | (19.9 % vs 9.2 %; 95 % CI 1.86-2.57, resampling 325 counties) / county_boot.csv (county_boot.py, county-clustered bootstrap) |
| W.09 | PASS | 8.9 | 8.85134925451039 | 0.05 | from 8.9 % (<2 % seasonal) to 29 % (50 %+) / seasonal_dose.csv |
| W.10 | PASS | 29 | 29.1658611309178 | 0.5 | from 8.9 % (<2 % seasonal) to 29 % (50 %+) / seasonal_dose.csv |
| W.11 | PASS | 2.07 | 2.07388482343918 | 0.005 | Top vs bottom mobile-home-share quartile: 2.07x (1.69-2.56) / county_boot.csv (county_boot.py, county-clustered bootstrap) |
| W.12 | PASS | 1.69 | 1.68871928128059 | 0.005 | Top vs bottom mobile-home-share quartile: 2.07x (1.69-2.56) / county_boot.csv (county_boot.py, county-clustered bootstrap) |
| W.13 | PASS | 2.56 | 2.55993617048217 | 0.005 | Top vs bottom mobile-home-share quartile: 2.07x (1.69-2.56) / county_boot.csv (county_boot.py, county-clustered bootstrap) |
| W.14 | PASS | 1.77 | 1.76699845110927 | 0.005 | 1.77x as often as all dwellings in the same tracts (23.5 % vs 13.3 %; 1.58-1.98) / county_boot_facilities.csv mobile_home_park (county_boot_facilities.py, county-clustered; point estimate = fac_stats.py pooled S30) |
| W.15 | PASS | 23.5 | 23.4534330387492 | 0.05 | 1.77x as often as all dwellings in the same tracts (23.5 % vs 13.3 %; 1.58-1.98) / county_boot_facilities.csv mobile_home_park (county_boot_facilities.py, county-clustered; point estimate = fac_stats.py pooled S30) |
| W.16 | PASS | 13.3 | 13.2730354257106 | 0.05 | 1.77x as often as all dwellings in the same tracts (23.5 % vs 13.3 %; 1.58-1.98) / county_boot_facilities.csv mobile_home_park (county_boot_facilities.py, county-clustered; point estimate = fac_stats.py pooled S30) |
| W.17 | PASS | 1.58 | 1.58137339080463 | 0.005 | 1.77x as often as all dwellings in the same tracts (23.5 % vs 13.3 %; 1.58-1.98) / county_boot_facilities.csv mobile_home_park (county_boot_facilities.py, county-clustered; point estimate = fac_stats.py pooled S30) |
| W.18 | PASS | 1.98 | 1.97922046660292 | 0.005 | 1.77x as often as all dwellings in the same tracts (23.5 % vs 13.3 %; 1.58-1.98) / county_boot_facilities.csv mobile_home_park (county_boot_facilities.py, county-clustered; point estimate = fac_stats.py pooled S30) |
| W.19 | PASS | 0.6 | 0.603173839642339 | 0.005 | (top vs bottom quartile 0.60x, 0.49-0.73) / county_boot.csv SVI Q4 vs Q1 |
| W.20 | PASS | 0.49 | 0.490226136360535 | 0.005 | (top vs bottom quartile 0.60x, 0.49-0.73) / county_boot.csv |
| W.21 | PASS | 0.73 | 0.726391432300835 | 0.005 | (top vs bottom quartile 0.60x, 0.49-0.73) / county_boot.csv |
| S.01 | PASS | 10951 | 10951.1395619705 | 0.5 | the 10,951 km of single-egress segments / single_egress_km_by_class.csv (egress_km_by_class.py from work/cb_<region>_link.parquet): length of single-egress link segments by road class |
| S.02 | PASS | - | 1 | - | By construction of the egress search / single_egress_km_by_class.csv (egress_km_by_class.py from work/cb_<region>_link.parquet): length of single-egress link segments by road class [zero scored-class single-egress length follows from the arterial sink definition; not an independent measurement] |
| S.03 | PASS | 81 | 81.0729730027836 | 0.5 | (81 % are residential) / single_egress_km_by_class.csv (egress_km_by_class.py from work/cb_<region>_link.parquet): length of single-egress link segments by road class |
| S.04 | PASS | 97.9 | 97.9270315564858 | 0.05 | 97.9 % of S30 dwellings / s30_in_tracts_without_scorecard_roads.csv (s30_scorecard_tracts.py: 1 - share of S30 dwellings in tracts with no motorway..secondary graph link) |
| B.01 | PASS | 1.1 | 1.09931689857367 | 0.005 | **1.10 census persons per dwelling (0.97-1.24) vs 2.34 (2.28-2.39)** / persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap) |
| B.02 | PASS | 0.97 | 0.968285024903324 | 0.005 | **1.10 census persons per dwelling (0.97-1.24) vs 2.34 (2.28-2.39)** / persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap) |
| B.03 | PASS | 1.24 | 1.2372798721793 | 0.005 | **1.10 census persons per dwelling (0.97-1.24) vs 2.34 (2.28-2.39)** / persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap) |
| B.04 | PASS | 2.34 | 2.33544260576409 | 0.005 | **1.10 census persons per dwelling (0.97-1.24) vs 2.34 (2.28-2.39)** / persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap) |
| B.05 | PASS | 2.28 | 2.2805156255511 | 0.005 | **1.10 census persons per dwelling (0.97-1.24) vs 2.34 (2.28-2.39)** / persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap) |
| B.06 | PASS | 2.39 | 2.38616442294761 | 0.005 | **1.10 census persons per dwelling (0.97-1.24) vs 2.34 (2.28-2.39)** / persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap) |
| B.07 | PASS | 0.47 | 0.47071030384581 | 0.005 | (ratio 0.47, 0.41-0.53; 185 counties) / persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap) |
| B.08 | PASS | 0.41 | 0.412575144827397 | 0.005 | (ratio 0.47, 0.41-0.53; 185 counties) / persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap) |
| B.09 | PASS | 0.53 | 0.531607001667 | 0.005 | (ratio 0.47, 0.41-0.53; 185 counties) / persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap) |
| B.010 | PASS | 185 | 185 | 0.5 | (ratio 0.47, 0.41-0.53; 185 counties) / persons_per_dwelling_ci.csv (persons_per_dwelling_ci.py, county-clustered bootstrap) |
| B.11 | PASS | 2.34 | 2.33544260576409 | 0.005 | (low 1.2, mid 2.34, high 3.5; an assumption) / mid q = observed year-round persons per dwelling in <2 % seasonal clusters |
| B.12 | PASS | 176 | 176 | 0.5 | the 176 such links / seasonal_load_summary.csv (seasonal_load.py) |
| B.13 | PASS | 47.9 | 47.9389439143334 | 0.05 | **47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)** / seasonal_load_summary.csv (seasonal_load.py) |
| B.14 | PASS | 70 | 69.9842073280665 | 0.5 | **47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)** / seasonal_load_summary.csv (seasonal_load.py) |
| B.15 | PASS | 91 | 90.927207571113 | 0.5 | **47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)** / seasonal_load_summary.csv (seasonal_load.py) |
| B.16 | PASS | 112 | 112.237628871055 | 0.5 | **47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)** / seasonal_load_summary.csv (seasonal_load.py) |
| B.17 | PASS | 1.5 | 1.45986126546984 | 0.05 | **47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)** / seasonal_load_summary.csv (seasonal_load.py) |
| B.18 | PASS | 1.9 | 1.89672946766619 | 0.05 | **47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)** / seasonal_load_summary.csv (seasonal_load.py) |
| B.19 | PASS | 2.3 | 2.34126202428704 | 0.05 | **47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)** / seasonal_load_summary.csv (seasonal_load.py) |
| B.20 | PASS | 1.73 | 1.7294730233342 | 0.005 | **47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)** / seasonal_alloc_robust.csv min_coverage=0 (county-clustered CI) |
| B.21 | PASS | 2.1 | 2.10190688832278 | 0.005 | **47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)** / seasonal_alloc_robust.csv |
| B.22 | PASS | 43 | 43 | 0.5 | **47.9 k census persons but 70 k / 91 k / 112 k at peak (1.5x / 1.9x / 2.3x; mid-case CI 1.73-2.10, 43 counties)** / seasonal_alloc_robust.csv |
| B.23 | PASS | 2.2 | 2.17330565973693 | 0.05 | 2.2-4.4x where seasonal housing is 50 %+ / seasonal_load_summary.csv (seasonal_load.py) |
| B.24 | PASS | 4.4 | 4.42214150756605 | 0.05 | 2.2-4.4x where seasonal housing is 50 %+ / seasonal_load_summary.csv (seasonal_load.py) |
| B.25 | PASS | 3931 | 3931 | 0.5 | Across the 3,931 single-link clusters (100+ dwellings, census residents) the gap is only 3-8 % / seasonal_load_summary.csv (seasonal_load.py) |
| B.26 | PASS | 3 | 2.74339480421115 | 0.5 | Across the 3,931 single-link clusters (100+ dwellings, census residents) the gap is only 3-8 % / seasonal_load_summary.csv (seasonal_load.py) |
| B.27 | PASS | 8 | 8.00156817894924 | 0.5 | Across the 3,931 single-link clusters (100+ dwellings, census residents) the gap is only 3-8 % / seasonal_load_summary.csv (seasonal_load.py) |
| B.28 | PASS | 18 | 18 | 0.5 | the 18 links serving a quarter or more of their tract's housing give 1.4x / 1.8x / 2.2x / seasonal_alloc_robust.csv min_coverage=0.25 (seasonal_alloc_robust.py) |
| B.29 | PASS | 1.4 | 1.40701426478839 | 0.05 | the 18 links serving a quarter or more of their tract's housing give 1.4x / 1.8x / 2.2x / seasonal_alloc_robust.csv min_coverage=0.25 (seasonal_alloc_robust.py) |
| B.30 | PASS | 1.8 | 1.79367781633737 | 0.05 | the 18 links serving a quarter or more of their tract's housing give 1.4x / 1.8x / 2.2x / seasonal_alloc_robust.csv min_coverage=0.25 (seasonal_alloc_robust.py) |
| B.31 | PASS | 2.2 | 2.18712493896615 | 0.05 | the 18 links serving a quarter or more of their tract's housing give 1.4x / 1.8x / 2.2x / seasonal_alloc_robust.csv min_coverage=0.25 (seasonal_alloc_robust.py) |
| Q.01 | UNVERIFIED | - | - | - | 4.0 persons per occupied second-home or visitor unit / Mammoth Lakes Eagle Lodge Draft EIR s3.8 (SOURCES.md row 9) [source document not distributed with the repository: fetch it as listed in SOURCES.md] |
| Q.02 | UNVERIFIED | - | - | - | occupied 49 % of the year / Mammoth Lakes Eagle Lodge Draft EIR s3.8 (SOURCES.md row 9) [source document not distributed with the repository: fetch it as listed in SOURCES.md] |
| Q.03 | UNVERIFIED | - | - | - | 34,265 persons / Mammoth Lakes Eagle Lodge Draft EIR s3.8 (SOURCES.md row 9) [source document not distributed with the repository: fetch it as listed in SOURCES.md] |
| Q.04 | UNVERIFIED | - | - | - | 7,259 residents / Mammoth Lakes Eagle Lodge Draft EIR s3.8 (SOURCES.md row 9) [source document not distributed with the repository: fetch it as listed in SOURCES.md] |
| Q.05 | UNVERIFIED | - | - | - | 51-64 % for condominiums and 43-75 % for mobile homes / SW Florida RPC Hurricane Evacuation Study Update 1987 (SOURCES.md row 10) [source document not distributed with the repository: fetch it as listed in SOURCES.md] |
| Q.06 | PASS | 30 | 30 | 0.5 | 4.0 persons at 30 / 59 / 88 % occupancy / arithmetic: q / 4.0 persons per occupied unit |
| Q.07 | PASS | 59 | 59 | 0.5 | 4.0 persons at 30 / 59 / 88 % occupancy / arithmetic: q / 4.0 persons per occupied unit |
| Q.08 | PASS | 88 | 88 | 0.5 | 4.0 persons at 30 / 59 / 88 % occupancy / arithmetic: q / 4.0 persons per occupied unit |
| N.01 | PASS | - | 1 | - | /Walden Rd, Lake Conroe TX/48339694305/4,291/8,264/8,943-10,244/ / seasonal_load_range.csv (seasonal_load.py) [table row regenerated from seasonal_load_range.csv] |
| N.02 | PASS | - | 1 | - | /Cranes Mill Rd, Canyon Lake TX/48091310608/2,840/5,620/5,884-6,392/ / seasonal_load_range.csv (seasonal_load.py) [table row regenerated from seasonal_load_range.csv] |
| N.03 | PASS | - | 1 | - | /Queen Isabella Causeway, South Padre TX/48061012305/1,736/724/2,117-4,788/ / seasonal_load_range.csv (seasonal_load.py) [table row regenerated from seasonal_load_range.csv] |
| N.04 | PASS | - | 1 | - | /E 310 Rd, Grand Lake OK/40041375804/1,072/1,102/1,848-3,277/ / seasonal_load_range.csv (seasonal_load.py) [table row regenerated from seasonal_load_range.csv] |
| N.05 | PASS | - | 1 | - | /Alpine Meadows Rd, Olympic Valley CA/06061022014/679/301/914-2,090/ / seasonal_load_range.csv (seasonal_load.py) [table row regenerated from seasonal_load_range.csv] |
| N.06 | PASS | - | 1 | - | /Mountainaire Rd, Flagstaff AZ/04005001500/538/253/725-1,630/ / seasonal_load_range.csv (seasonal_load.py) [table row regenerated from seasonal_load_range.csv] |
| N.07 | PASS | - | 1 | - | per-link lists for all regions are in `tables/<region>_drv_A_links.csv` / tables/<region>_drv_A_links.csv [the five per-region link lists exist in tables/] |
| C.01 | PASS | 1.6 | 1.63435150185861 | 0.05 | (1.6x N. California to 4.8x E. Oklahoma, all CIs above 1) / seasonal_contrasts.csv per region (seasonal.py, tract bootstrap) |
| C.02 | PASS | 4.8 | 4.82785624257399 | 0.05 | (1.6x N. California to 4.8x E. Oklahoma, all CIs above 1) / seasonal_contrasts.csv per region (seasonal.py, tract bootstrap) |
| C.03 | PASS | - | 1 | - | (1.6x N. California to 4.8x E. Oklahoma, all CIs above 1) / seasonal_contrasts.csv per region (seasonal.py, tract bootstrap) [every region's 95 % CI above 1] |
| C.04 | PASS | 1.84 | 1.8411035904169 | 0.005 | within rural-only (1.84x, 1.62-2.06) and urban-only (2.17x, 1.89-2.47) tracts / seasonal_rural_urban.csv (seasonal2.py, default bootstrap 1000) |
| C.05 | PASS | 1.62 | 1.62186147922151 | 0.005 | within rural-only (1.84x, 1.62-2.06) and urban-only (2.17x, 1.89-2.47) tracts / seasonal_rural_urban.csv (seasonal2.py, default bootstrap 1000) |
| C.06 | PASS | 2.06 | 2.06373968600879 | 0.005 | within rural-only (1.84x, 1.62-2.06) and urban-only (2.17x, 1.89-2.47) tracts / seasonal_rural_urban.csv (seasonal2.py, default bootstrap 1000) |
| C.07 | PASS | 2.17 | 2.17036659762986 | 0.005 | within rural-only (1.84x, 1.62-2.06) and urban-only (2.17x, 1.89-2.47) tracts / seasonal_rural_urban.csv (seasonal2.py, default bootstrap 1000) |
| C.08 | PASS | 1.89 | 1.89317846078992 | 0.005 | within rural-only (1.84x, 1.62-2.06) and urban-only (2.17x, 1.89-2.47) tracts / seasonal_rural_urban.csv (seasonal2.py, default bootstrap 1000) |
| C.09 | PASS | 2.47 | 2.47397301124432 | 0.005 | within rural-only (1.84x, 1.62-2.06) and urban-only (2.17x, 1.89-2.47) tracts / seasonal_rural_urban.csv (seasonal2.py, default bootstrap 1000) |
| C.10 | PASS | - | 1 | - | at 5, 10 and 20 % thresholds / seasonal_robust.csv (seasonal_robust.py) [ratios 1.86 / 2.38 / 2.97, CIs above 1] |
| C.11 | PASS | 3.3 | 3.31581427786678 | 0.05 | (+3.3 points of S30 per +10 points of seasonal share, 1.95-4.68; +3.9, 2.6-5.3 with road density) / seasonal_regress.csv pooled '+ controls + county FE' (seasonal.py) |
| C.12 | PASS | 1.95 | 1.94965733847424 | 0.005 | (+3.3 points of S30 per +10 points of seasonal share, 1.95-4.68; +3.9, 2.6-5.3 with road density) / seasonal_regress.csv pooled '+ controls + county FE' (seasonal.py) |
| C.13 | PASS | 4.68 | 4.68197121725932 | 0.005 | (+3.3 points of S30 per +10 points of seasonal share, 1.95-4.68; +3.9, 2.6-5.3 with road density) / seasonal_regress.csv pooled '+ controls + county FE' (seasonal.py) |
| C.14 | PASS | 3.9 | 3.9422690257591 | 0.05 | (+3.3 points of S30 per +10 points of seasonal share, 1.95-4.68; +3.9, 2.6-5.3 with road density) / density_dissoc_regress.csv pooled 'with log road density' (density_dissoc.py) |
| C.15 | PASS | 2.6 | 2.58354030182273 | 0.05 | (+3.3 points of S30 per +10 points of seasonal share, 1.95-4.68; +3.9, 2.6-5.3 with road density) / density_dissoc_regress.csv pooled 'with log road density' (density_dissoc.py) |
| C.16 | PASS | 5.3 | 5.30099774969547 | 0.05 | (+3.3 points of S30 per +10 points of seasonal share, 1.95-4.68; +3.9, 2.6-5.3 with road density) / density_dissoc_regress.csv pooled 'with log road density' (density_dissoc.py) |
| V.01 | PASS | 27 | 27 | 0.5 | 27 of 32 documented single-access areas matched / validation_tehama_summary.txt (validate_tehama.py) |
| V.02 | PASS | 32 | 32 | 0.5 | 27 of 32 documented single-access areas matched / validation_tehama_summary.txt (validate_tehama.py) |
| V.03 | PASS | 0.86 | 0.86 | 0.005 | Spearman 0.86 (p = 8e-9) / validation_tehama_summary.txt (validate_tehama.py) |
| V.04 | PASS | 8e-09 | 8.2e-09 | 1e-09 | Spearman 0.86 (p = 8e-9) / validation_tehama_summary.txt (validate_tehama.py) |
| V.05 | PASS | 22 | 22 | 0.5 | 22 of 27 have 20+ dwellings behind one link vs 30.7 % of named roads / validation_tehama_summary.txt (validate_tehama.py) |
| V.06 | PASS | 27 | 27 | 0.5 | 22 of 27 have 20+ dwellings behind one link vs 30.7 % of named roads / validation_tehama_summary.txt (validate_tehama.py) |
| V.07 | PASS | 30.7 | 30.7 | 0.05 | 22 of 27 have 20+ dwellings behind one link vs 30.7 % of named roads / validation_tehama_summary.txt (validate_tehama.py) |
| V.08 | PASS | 0.854 | 0.854 | 0.0005 | AUC 0.854, Fisher p = 3e-7; one-exit areas flagged 17/26 vs multi-exit 1/31 / validation_hays_summary.txt (validate_hays.py) |
| V.09 | PASS | 3e-07 | 3.17e-07 | 1e-07 | AUC 0.854, Fisher p = 3e-7; one-exit areas flagged 17/26 vs multi-exit 1/31 / validation_hays_summary.txt (validate_hays.py) |
| V.10 | PASS | 17 | 17 | 0.5 | AUC 0.854, Fisher p = 3e-7; one-exit areas flagged 17/26 vs multi-exit 1/31 / validation_hays_summary.txt (validate_hays.py) |
| V.11 | PASS | 26 | 26 | 0.5 | AUC 0.854, Fisher p = 3e-7; one-exit areas flagged 17/26 vs multi-exit 1/31 / validation_hays_summary.txt (validate_hays.py) |
| V.12 | PASS | 1 | 1 | 0.5 | AUC 0.854, Fisher p = 3e-7; one-exit areas flagged 17/26 vs multi-exit 1/31 / validation_hays_summary.txt (validate_hays.py) |
| V.13 | PASS | 31 | 31 | 0.5 | AUC 0.854, Fisher p = 3e-7; one-exit areas flagged 17/26 vs multi-exit 1/31 / validation_hays_summary.txt (validate_hays.py) |
| M.01 | PASS | 3.9 | 3.91982255033995 | 0.05 | removes only 3.9 % of S30 dwellings (3-8 % by region) / false_single_access.csv pooled (coverage_bridge_agg.py / sens_nearmiss2.py / run_tx_plus.sh) |
| M.02 | PASS | 3 | 3.23232084114013 | 0.5 | removes only 3.9 % of S30 dwellings (3-8 % by region) / false_single_access.csv pooled (coverage_bridge_agg.py / sens_nearmiss2.py / run_tx_plus.sh) |
| M.03 | PASS | 8 | 7.79736845462916 | 0.5 | removes only 3.9 % of S30 dwellings (3-8 % by region) / false_single_access.csv pooled (coverage_bridge_agg.py / sens_nearmiss2.py / run_tx_plus.sh) |
| M.04 | PASS | 25 | 25.2311295963685 | 0.5 | admitting service and track roads 25 %, either 28 %: 72 % survives both / false_single_access.csv pooled (coverage_bridge_agg.py / sens_nearmiss2.py / run_tx_plus.sh) |
| M.05 | PASS | 28 | 27.970258597949 | 0.5 | admitting service and track roads 25 %, either 28 %: 72 % survives both / false_single_access.csv pooled (coverage_bridge_agg.py / sens_nearmiss2.py / run_tx_plus.sh) |
| M.06 | PASS | 72 | 72.029741402051 | 0.5 | admitting service and track roads 25 %, either 28 %: 72 % survives both / false_single_access.csv pooled (coverage_bridge_agg.py / sens_nearmiss2.py / run_tx_plus.sh) |
| M.07 | PASS | 96.8 | 96.8441619460322 | 0.05 | (96.8 % vs 88.7 % for same-class roads in the tract) / cov_bridge_links.csv pooled named |
| M.08 | PASS | 88.7 | 88.6560669349517 | 0.05 | (96.8 % vs 88.7 % for same-class roads in the tract) / cov_bridge_links.csv |
| M.09 | PASS | 44.7 | 44.7258804234038 | 0.05 | (44.7 % vs 43.1 %) / cov_bridge_buildings.csv pooled ml |
| M.10 | PASS | 43.1 | 43.1202478301928 | 0.05 | (44.7 % vs 43.1 %) / cov_bridge_buildings.csv |
| T.01 | PASS | 7.3 | 7.26431767793188 | 0.05 | (alternative weights give S30 of 7.3-13.1 %) / sens_grid.csv (sens_table.py): area-weighted and structure-count weights, scored classes, sink A, no repair, all regions |
| T.02 | PASS | 13.1 | 13.0727449204449 | 0.05 | (alternative weights give S30 of 7.3-13.1 %) / sens_grid.csv |
| I.01 | PASS | 4291 | 4290.65013351135 | 0.5 | put 4,291, 2,840 and 2,299 dwellings / seasonal_load_range.csv |
| I.02 | PASS | 2840 | 2840.31792077507 | 0.5 | put 4,291, 2,840 and 2,299 dwellings / seasonal_load_range.csv |
| I.03 | PASS | 2299 | 2298.52363111459 | 0.5 | put 4,291, 2,840 and 2,299 dwellings / seasonal_load_range.csv |
| I.04 | UNVERIFIED | - | - | - | 927 occupied housing units per egress lane / NIST TN 2252 (SOURCES.md row 5) [source document not distributed with the repository: fetch it as listed in SOURCES.md] |
| I.05 | PASS | 724 | 724.021401449776 | 0.5 | (724 census persons) and Alpine Meadows Rd (301) the assumed mid-case peak load is about 5x the census count (3,441 and 1,497; low case 2,117 and 914) / seasonal_load_range.csv |
| I.06 | PASS | 301 | 300.60162601626 | 0.5 | (724 census persons) and Alpine Meadows Rd (301) the assumed mid-case peak load is about 5x the census count (3,441 and 1,497; low case 2,117 and 914) / seasonal_load_range.csv |
| I.07 | PASS | 3441 | 3440.95929582327 | 0.5 | (724 census persons) and Alpine Meadows Rd (301) the assumed mid-case peak load is about 5x the census count (3,441 and 1,497; low case 2,117 and 914) / seasonal_load_range.csv |
| I.08 | PASS | 1497 | 1496.71692535107 | 0.5 | (724 census persons) and Alpine Meadows Rd (301) the assumed mid-case peak load is about 5x the census count (3,441 and 1,497; low case 2,117 and 914) / seasonal_load_range.csv |
| I.09 | PASS | 5 | 4.75256572379368 | 0.3 | (724 census persons) and Alpine Meadows Rd (301) the assumed mid-case peak load is about 5x the census count (3,441 and 1,497; low case 2,117 and 914) / seasonal_load_range.csv (Queen Isabella 4.75x) |
| I.10 | PASS | 5 | 4.97907128842381 | 0.3 | (724 census persons) and Alpine Meadows Rd (301) the assumed mid-case peak load is about 5x the census count (3,441 and 1,497; low case 2,117 and 914) / seasonal_load_range.csv (Alpine Meadows 4.98x) |
| I.11 | PASS | 98.3 | 98.3391215348788 | 0.05 | 98.3 % of S30 dwellings no mapped fire or EMS station lies on their side / stranded.csv pooled (stranded.py; top-level clusters of 30+ dwellings, facilities from fac_clusters_*.csv) |
| K.01 | PASS | 5 | 5 | 0.5 | This also applies to five of the six places above and 500 of the 527 clusters of 300+ dwellings / named_places_stations.csv (named_station_check.py) |
| K.02 | PASS | - | 1 | - | This also applies to five of the six places above and 500 of the 527 clusters of 300+ dwellings / named_places_stations.csv (named_station_check.py) [the six places of the draft's evidence table are exactly the six rows of named_places_stations.csv] |
| K.03 | PASS | 500 | 500 | 0.5 | This also applies to five of the six places above and 500 of the 527 clusters of 300+ dwellings / stranded.csv pooled (stranded.py) |
| K.04 | PASS | 527 | 527 | 0.5 | This also applies to five of the six places above and 500 of the 527 clusters of 300+ dwellings / stranded.csv pooled (stranded.py) |
| K.05 | PASS | - | 1 | - | This also applies to five of the six places above and 500 of the 527 clusters of 300+ dwellings / stranded.csv [300+ = the cluster-size threshold of the columns clusters_ge300 / clusters_ge300_no_fire_ems] |
| I.12 | PASS | 1.65 | 1.64883043715827 | 0.005 | 1.65x as likely (1.54-1.77) / resp_summary.csv (response_time.py + resp_summary.py; strict = category fire_department) |
| I.13 | PASS | 1.54 | 1.54085104718309 | 0.005 | 1.65x as likely (1.54-1.77) / resp_summary.csv (response_time.py + resp_summary.py; strict = category fire_department) |
| I.14 | PASS | 1.77 | 1.76642711480988 | 0.005 | 1.65x as likely (1.54-1.77) / resp_summary.csv (response_time.py + resp_summary.py; strict = category fire_department) |
| I.15 | PASS | 189 | 188.995244755834 | 0.5 | (189-230 k dwellings; not in Oklahoma) / resp_summary.csv (response_time.py + resp_summary.py; strict = category fire_department) broad |
| I.16 | PASS | 230 | 229.806094319835 | 0.5 | (189-230 k dwellings; not in Oklahoma) / resp_summary.csv (response_time.py + resp_summary.py; strict = category fire_department) strict |
| I.17 | PASS | - | 1 | - | (189-230 k dwellings; not in Oklahoma) / resp_summary.csv (response_time.py + resp_summary.py; strict = category fire_department) [Oklahoma 95 % CI contains 1] |
| I.18 | PASS | 69.5 | 69.5300379713743 | 0.05 | 69.5 k car-less households sit behind S30 links, 47.6 k with no transit stop within 800 m / double_trap.csv summed over the 5 regions (double_trap.py) |
| I.19 | PASS | 47.6 | 47.5896961204832 | 0.05 | 69.5 k car-less households sit behind S30 links, 47.6 k with no transit stop within 800 m / double_trap.csv summed over the 5 regions (double_trap.py) |
| D.01 | PASS | -0.33 | -0.331813164011091 | 0.005 | (rho with S30 -0.33) / density_dissoc.csv pooled all tracts (density_dissoc.py) |
| A.01 | PASS | 190 | 190 | 0.5 | For 190 of 3,933 single-link clusters (100+ dwellings) / pinholes_summary.csv pooled(5) (pinhole_summary.py) |
| A.02 | PASS | 3933 | 3933 | 0.5 | For 190 of 3,933 single-link clusters (100+ dwellings) / pinholes_summary.csv pooled(5) (pinhole_summary.py) |
| A.03 | PASS | 512 | 512 | 0.5 | (512 at up to 50 m) / pinholes_summary.csv pooled(5) (pinhole_summary.py) |
| A.04 | PASS | 399 | 399.256383112038 | 0.5 | Mountain Shadows Boulevard, Redding (399 dwellings, 4.3 m) / pinholes_top_candidates.csv |
| A.05 | PASS | 4.3 | 4.28868860515707 | 0.05 | Mountain Shadows Boulevard, Redding (399 dwellings, 4.3 m) / pinholes_top_candidates.csv |
| R.01 | PASS | - | 1 | - | Python 3.12, DuckDB 1.5.4 / runtime of this ledger run [python 3.12.3, duckdb 1.5.4] |
| P.01 | PASS | - | 1 | - | Buildings of 35 m2+ snap within 500 m / egress/pipeline.py [building footprint >= 35 m2] |
| P.02 | PASS | - | 1 | - | Buildings of 35 m2+ snap within 500 m / egress/variants.py [snap distance <= 500 m] |
| P.03 | PASS | - | 1 | - | no transit stop within 800 m / egress/double_trap.py [transit radius] |
| P.04 | PASS | - | 1 | - | dwellings over 10 minutes (free-flow) / egress/resp_summary.py [10 min free-flow drive time] |
| P.05 | PASS | - | 1 | - | circles = 40 largest links / egress/figs_regions.py [circles drawn for the 40 largest links] |
| P.06 | PASS | - | 1 | - | the 12 links with most second homes / egress/seasonal_load.py [fig 3: 12 links, tracts >= 25 % seasonal, ranked by seasonal units] |
| P.07 | PASS | - | 1 | - | seed 20261014 / egress/common.py [seed] |
| P.08 | PASS | - | 1 | - | Overture 2026-08-19.0 / SOURCES.md [release named in SOURCES.md] |
| P.09 | PASS | - | 1 | - | (IFC D107.1) / SOURCES.md [IFC D107.1 row, 30-dwelling threshold] |
| P.13 | PASS | - | 1 | - | Drivable Overture roads (no service/track) / egress/common.py [main graph = DRV classes (the 7 scored classes + living_street); DRVPLUS adds service and track in the sensitivity run] |
| P.14 | PASS | - | 1 | - | (no service/track) / egress/common.py [service and track roads are only in DRVPLUS] |
| P.15 | PASS | - | 1 | - | tracts with roads of those classes / egress/s30_scorecard_tracts.py [classes = ARTERIAL_A = motorway, trunk, primary, secondary (egress/common.py)] |
| P.10 | PASS | - | 1 | - | 57 neighbourhoods / Ramos & Yuan 2024 Table 1 [ext/hays_table1.csv has 57 rows] |
| P.11 | PASS | - | 1 | - | S30 / stranded.csv vs stats_burden_drv_A.csv [S30 = dwellings in top-level clusters of >= 30 dwellings (stranded.py asserts this per region)] |
| M.11 | PASS | 3.9 | 3.91982255033995 | 0.05 | so 3.9 % bounds the gap-induced part / false_single_access.csv pooled |
| Q.09 | UNVERIFIED | - | - | - | (Eagle Lodge Draft EIR, 2006) / Mammoth EIR carries the year 2006 [source document not distributed with the repository: fetch it as listed in SOURCES.md] |
| Q.10 | UNVERIFIED | - | - | - | A 1987 Southwest Florida hurricane evacuation study / HES document is the 1987 update [source document not distributed with the repository: fetch it as listed in SOURCES.md] |
| P.12 | UNVERIFIED | - | - | - | in the 2018 Camp Fire (NIST TN 2252) / NIST TN 2252 is the 2018 Camp Fire case study [source document not distributed with the repository: fetch it as listed in SOURCES.md] |
| R.02 | PASS | - | 1 | - | (E. Washington about 1 minute) / <repo>/verification/linux_aarch64_full_rebuild/steps.jsonl [measured Linux step-1 commands 5/5, 49.228 s; same <=90 s approximation bound] |
| G.01 | PASS | 2.15 | 2.15428736021411 | 0.005 | **2.15x** the S30 exposure of others (19.9 % vs 9.2 %; 95 % CI 1.86-2.57, resampling 325 counties) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.02 | PASS | 1.86 | 1.85689971851637 | 0.005 | **2.15x** the S30 exposure of others (19.9 % vs 9.2 %; 95 % CI 1.86-2.57, resampling 325 counties) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.03 | PASS | 2.57 | 2.5733251210976 | 0.005 | **2.15x** the S30 exposure of others (19.9 % vs 9.2 %; 95 % CI 1.86-2.57, resampling 325 counties) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.04 | PASS | 2.07 | 2.07388482343918 | 0.005 | Top vs bottom mobile-home-share quartile: 2.07x (1.69-2.56) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.05 | PASS | 1.69 | 1.68871928128059 | 0.005 | Top vs bottom mobile-home-share quartile: 2.07x (1.69-2.56) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.06 | PASS | 2.56 | 2.55993617048217 | 0.005 | Top vs bottom mobile-home-share quartile: 2.07x (1.69-2.56) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.07 | PASS | 0.6 | 0.603173839642339 | 0.005 | (top vs bottom quartile 0.60x, 0.49-0.73) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.08 | PASS | 0.49 | 0.490226136360535 | 0.005 | (top vs bottom quartile 0.60x, 0.49-0.73) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.09 | PASS | 0.73 | 0.726391432300835 | 0.005 | (top vs bottom quartile 0.60x, 0.49-0.73) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.10 | PASS | 1.77 | 1.76699845110927 | 0.005 | 1.77x as often as all dwellings in the same tracts (23.5 % vs 13.3 %; 1.58-1.98) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.11 | PASS | 1.58 | 1.58137339080463 | 0.005 | 1.77x as often as all dwellings in the same tracts (23.5 % vs 13.3 %; 1.58-1.98) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.12 | PASS | 1.98 | 1.97922046660292 | 0.005 | 1.77x as often as all dwellings in the same tracts (23.5 % vs 13.3 %; 1.58-1.98) / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) |
| G.13 | PASS | - | 1 | - | county-clustered bootstrap 95 % CIs / effects_forest_county.csv (figs_forest.py: the table behind Fig. 5) [all 12 rows of the Fig. 5 table come from county-clustered tables] |
| V.14 | PASS | - | 1 | - | 22 of 27 have 20+ dwellings behind one link / fig3_validation_labels.txt (figs_m1.py: the panel titles of Fig. 6) [the Fig. 6 Tehama title states the text's count] |
| V.15 | PASS | - | 1 | - | Spearman 0.86 / fig3_validation_labels.txt (figs_m1.py: the panel titles of Fig. 6) [the Fig. 6 Tehama title states the text's rho] |
| V.16 | PASS | - | 1 | - | AUC 0.854 / fig3_validation_labels.txt (figs_m1.py: the panel titles of Fig. 6) [the Fig. 6 Hays title states the text's AUC] |
| N.08 | PASS | - | 1 | - | None of the public forum entries we read / NOVELTY.md [NOVELTY.md records the read public-entry corpus and its search hits; no claim about unseen/form-only entries] |
| H.01 | PASS | 1.77 | 1.76699845110927 | 0.005 | Exposure is 1.77x for mapped mobile-home parks / effects_forest_county.csv mobile-home parks row |
| H.02 | PASS | 2.15 | 2.15428736021411 | 0.005 | 2.15x in seasonal communities / effects_forest_county.csv resort-type row; defined in Who paragraph |
| H.03 | PASS | 0.6 | 0.603173839642339 | 0.005 | high-SVI tracts are less exposed (0.60x) / effects_forest_county.csv SVI row |
| H.04 | PASS | 3.9 | 3.91982255033995 | 0.05 | gap repair removes 3.9 % / false_single_access.csv pooled |
| H.05 | PASS | 69.5 | 69.5300379713743 | 0.05 | Also exposed: 69.5 k car-less households, 47.6 k with no transit stop within 800 m / double_trap.csv summed over the five regions |
| H.06 | PASS | 47.6 | 47.5896961204832 | 0.05 | Also exposed: 69.5 k car-less households, 47.6 k with no transit stop within 800 m / double_trap.csv summed over the five regions |
| H.07 | PASS | 4291 | 4290.65013351135 | 0.5 | Walden Rd, Lake Conroe TX: 4,291 dwellings / seasonal_load_range.csv |
| I.20 | PASS | 2117 | 2117.32288574387 | 0.5 | low case 2,117 and 914 / seasonal_load_range.csv Queen Isabella Causeway, peak_low |
| I.21 | PASS | 914 | 913.9940872136 | 0.5 | low case 2,117 and 914 / seasonal_load_range.csv Alpine Meadows Road, peak_low |
| M.12 | PASS | - | 1 | - | their recent-edit share is no lower / cov_bridge_links.csv pooled recent row [pooled recent-edit share is not lower than same-tract, same-class neighbours (including county-bootstrap lower difference bound)] |
