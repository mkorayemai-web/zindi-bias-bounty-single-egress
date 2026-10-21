# One way out: 3.76 M people depend on a single local road link the coverage score never measures. Mobile-home parks and second-home communities are most exposed; SVI points the other way.

Entry for the Zindi "Bias Bounty: Mapping Equity Challenge", prize "Best Bias Discovery". This release contains the author's write-up, code, quoted tables and figures, sources and verification records.

## Summary

The scorecard credits arterial kilometres, not whether homes have a second route upstream. Across five regions, 9.9 % of dwellings (1.68 M dwellings, 3.76 M people) sit behind one road link serving at least 30 dwellings, the model-code benchmark (IFC D107.1). Exposure is 1.77x for mapped mobile-home parks and 2.15x in seasonal communities; high-SVI tracts are less exposed (0.60x). County evacuation studies confirm the classification; gap repair removes 3.9 %. The coverage-definition gap matters for evacuation, outside responders and car-less households; second-home occupancy scenarios also expose census-based planning undercounts.

## How this differs from related entries

- 34995 examines reference-based coverage gaps in mobile-home-park tracts; this release measures route redundancy around parks that are mapped.
- 35081/35157 measure road density; this release asks whether each dwelling has a second route to an arterial.
- 35033 examines closures at listed Texas low-water crossings; this release ranks single links across five regions without a hazard list, weighted by dwellings and persons.
- 35360 examines missing urban arterial geometry; this release studies local links upstream of arterials that are present.
- 35333/34972 examine phantom or stale road geometry; this release checks naming and edit recency as safeguards for its topology analysis.
- 35000 examines road-score construction and station coverage; this release addresses route redundancy below the scored arterial classes.

These are complementary questions. NOVELTY.md records the comparisons and the limitations of the public-entry search.

## Contents

- DISCOVERY_DRAFT.md: the final write-up; figures are in figs/.
- SOURCES.md: public-source URLs, retrieval dates and licence terms.
- REPRODUCE.md: commands, expected values, software environment and method.
- NUMBERS_LEDGER.md and tables/numbers_ledger.csv: per-check numeric evidence and explicit missing-source statuses.
- verification/: macOS arm64 and Linux aarch64 records, per-step runtimes, per-check values, strict differences, PNG comparisons and current preflight transcripts. verification/README.md explains their scope and normalised location placeholders.
- egress/ and validation/: the analysis, preflight and independent validation code.
- tables/, figs/, ext/: quoted outputs and small public inputs.
- work/: shipped small intermediates; large graph/building files are rebuilt from challenge data.
- CHANGELOG.md: changes from release 1 to this release; no new measured results.
- MANIFEST.sha256: sorted SHA-256 inventory of release files.

## Reproduce

Use Python 3.12, the packages pinned in requirements.txt and an installed DuckDB spatial extension. The analysis loads the extension and, if it is missing, installs it once (needs internet on first use).

1. Verify the checkout: `sha256sum -c MANIFEST.sha256` (macOS: `shasum -a 256 -c MANIFEST.sha256`).
2. Put the challenge package in the documented data/reference and data/strata layout, or set BIAS_BOUNTY_ROOT to the directory containing data/.
3. Run a clean region check: `PY=<python> sh egress/preflight.sh eastern-wa`. All printed regional sensitivity configurations are rebuilt in scratch; committed results are not overwritten. Expected S30: 7.52 %, 52,721 dwellings and 112,860 persons.
4. For pooled findings use `PY=<python> sh egress/preflight_all.sh`. A completed clean rebuild can instead be audited with `--existing-rebuild <scratch>`. REPRODUCE.md gives the detailed commands and prerequisites.

The quick command ends with:

    HEADLINE (printed numbers for eastern-wa): PASS 71/71
    FULL INTERMEDIATES (strict, informational): 3 of 20 files identical; differences explained in <scratch>/FULL_INTERMEDIATES.md
    QUOTED SOURCES (not shipped; verify at the SOURCES.md URLs, or pass --sources DIR): 9 checks SKIPPED

The full computational label is `HEADLINE (every printed number computed from the data): PASS 193/193`. Only HEADLINE controls the preflight exit. A computed failure or skip still fails; quoted documents remain separate and are never silently counted as passes. Both commands accept `--sources DIR`; matching, mismatching and missing local text files are counted on the third line. See REPRODUCE.md for filenames. n counts ledger checks, including parameter/whole-row checks, not distinct empirical quantities.

## Verification limits

The author verified macOS arm64 and Linux aarch64; x86 is untested. Across the full Linux rebuild, 44 of 206 artifacts are byte-identical and seven of 13 PNGs have identical pixels. Strict differences remain visible with exact counts/IDs and float rel 1e-9 / abs 1e-12; no numerical tolerances were relaxed. Earlier transcripts use the historical single-gate policy; verification/README.md distinguishes them from current computational verdicts.

Raw national ACS extraction failed because the source files were absent. Hashed shipped public ACS extracts remain documented INPUTS, not newly extracted results. Nine external-document checks remain SKIPPED until their real text is supplied. Runtime, input provenance, pixel counts and every differing column are retained in verification/.

## Licence

Code: MIT (LICENSE). Data-derived outputs and text carry the source terms in SOURCES.md, including Overture/OSM attribution and applicable ODbL share-alike requirements. The challenge page also states CC-BY SA 4.0 for the package. Check the source-specific terms before reuse.

Code was drafted with AI coding assistants, as permitted by the challenge rules. This release uses open-source tools only.
