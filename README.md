# Who has only one way out? Second-home, resort and mobile-home communities, invisible to SVI and to census person counts

Entry for the Zindi "Bias Bounty: Mapping Equity Challenge", prize "Best Bias Discovery". This repository holds the write-up, the code, every table and figure it quotes, and the sources behind it.

## What is here

| path | content |
|---|---|
| `DISCOVERY_DRAFT.md` | the write-up (1,500 words or fewer, figures in `figs/`) |
| `SOURCES.md` | every public source used beyond the challenge package: URL, retrieval date, licence |
| `REPRODUCE.md` | commands, expected values, method in one paragraph |
| `NUMBERS_LEDGER.md` | every number in the write-up re-derived from the tables, source documents and code parameters (`egress/numbers_ledger.py`; self-test `egress/ledger_selftest.py`) |
| `PREFLIGHT_<region>.txt` (five files) | records of the clean-room re-run of each region plus the validations (`egress/preflight.sh <region>`); all five end in PREFLIGHT PASS |
| `PREFLIGHT_bridge_<region>.txt` (five files) | records of the clean-room re-run of the robustness chain (service and track roads, 25 m gap repair, latent-connection sweeps, coverage bridge; `egress/preflight_bridge.sh <region>`); all five end in BRIDGE-PREFLIGHT PASS |
| `NOVELTY.md`, `CALIBRATION.md`, `PINHOLES.md` | supporting notes (how this differs from other entries; how far map repairs can be trusted; unverified leads) |
| `egress/` | the code: Python 3.12, DuckDB 1.5.4, seed 20261014, at most 4 threads |
| `validation/` | checks against two independent published documents: Tehama County CA evacuation study, Hays County TX (Ramos and Yuan 2024) |
| `tables/`, `figs/`, `ext/` | every output the write-up quotes; small public inputs |
| `work/` | small intermediates (per-region tract tables, link and node arrays; about 80 MB) that `egress/preflight_stats.sh` needs to re-derive the statistics without rebuilding the graph; the large graph and building files are not shipped |
| `MANIFEST.sha256` | SHA-256 of every file listed above |

## Reproduce one region in about a minute

1. Get the challenge data package in the layout of the challenge README (`aws s3 sync`) into `data/` inside this repository (`data/reference/<region>/...`, `data/strata/<region>/...`), or anywhere else and then `export BIAS_BOUNTY_ROOT=<DATA_ROOT>`, the directory that contains `data/`.
2. Check the download: `shasum -a 256 -c MANIFEST.sha256`.
3. Nothing to configure: no script contains an absolute path, each derives its paths from its own location and finds the data in `./data` (or in `$BIAS_BOUNTY_ROOT`).
4. Rebuild Eastern Washington and compare with the shipped tables: `PY="$(command -v python)" sh egress/preflight.sh eastern-wa`. It works on a scratch copy, deletes the region's outputs first, and prints `PREFLIGHT PASS` only if every re-written file is identical to the shipped one. Expected: single-link share S30 = 7.52 % (52,721 dwellings, 112,860 people). The other four regions work the same way (`preflight.sh northern-ca`, `eastern-ok`, `maricopa-az`, `south-central-tx`): under 2.5 minutes each, Texas about 14 minutes. All four were also run inside a fresh clone of this repository; there only the region chain is compared and the validations are skipped, because the clone has no building files (step 6).
5. Re-derive the statistics and the tables, documents and figures they feed (65 files, among them 10 of the 13 files in `figs/` and 6 of the write-up's 7 figures) from the shipped intermediates, with no graph build (about 5 minutes on the author's laptop): `PY="$(command -v python)" sh egress/preflight_stats.sh`. It works on a scratch copy and prints `PREFLIGHT-STATS PASS` only if every re-written file is byte-identical to the shipped one. Not re-derived this way: the per-region link tables, the validation tables, the pinhole lists and the pinhole and resort-cluster figures (they need the graph and building files; see 6 and the paragraph below).
6. The other regions from scratch and the four validation scripts follow `REPRODUCE.md` (Texas is the long one: about 8 minutes for the main graph and about 10 for the +service/track variant on an otherwise idle laptop); the validations need northern-ca and south-central-tx to be built first.

Checks run on the author's host, where the building and graph files exist (the repository does not ship them; the records are in this repository): `egress/preflight.sh <region>` with the four validations for all five regions (`PREFLIGHT_<region>.txt`; Texas about 15 minutes, because it also rebuilds the latent-connection variants that the Hays validation reads); `egress/preflight_bridge.sh <region>` for the robustness chain behind the sensitivity numbers and the pinhole counts (service and track roads, 25 m gap repair, latent-connection sweeps, coverage bridge; `PREFLIGHT_bridge_<region>.txt`); `figs_resort.py` and `figs_pinholes.py` for the three figures that step 5 cannot re-derive (fig6, fig7, fig9: byte-identical to the shipped PNGs); `acs_ext.py` and `seasonal.py` from the raw Census files (the two ACS extracts come out content-identical; checksums in `SOURCES.md` rows 3 and 8).

Python 3.12 and the packages pinned in `requirements.txt` (the tested set), plus DuckDB's spatial extension (`python -c "import duckdb; duckdb.sql('INSTALL spatial')"`, needs internet once).

## Licence

Code: MIT (`LICENSE`). Tables, figures and text are derived from the challenge package (Overture Maps extracts, release 2026-08-19.0, US Census Bureau tables) and from the public sources in `SOURCES.md`; they carry the terms of those inputs, which each row of `SOURCES.md` states (row 0 for the package). In particular the Overture transportation and buildings themes are ODbL 1.0: reuse of tables and figures derived from them needs the attribution "(c) OpenStreetMap contributors, Overture Maps Foundation", and ODbL share-alike terms may apply to derived databases. The challenge page also lists "Data Sharing: CC-BY SA 4.0 license" for the package (`SOURCES.md` row 0). Check before reuse.

## How the code was written

Code was drafted with the help of AI coding assistants (permitted by the challenge rules); every step runs with open-source tools only.
