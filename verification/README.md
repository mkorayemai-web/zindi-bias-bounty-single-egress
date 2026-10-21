# Verification records

This release preserves the author's macOS arm64 and Linux aarch64 verification records. x86 is untested. These files are records of actual executions, not newly generated model results.

Locations are normalised: <repo> denotes the checkout and <scratch> a temporary build/audit directory. Historical shorthand naming the checkout directory is also rendered as <repo>. Apart from this location normalisation, retained evidence is unchanged: verdict lines, counts, measurements, tolerances, timestamps and recorded differences are preserved. Normalised paths are provenance placeholders, not executable commands.

## File index

- macos_arm64/: original region and robustness preflight transcripts. These use the historical byte/content gate and record the author's macOS checks.
- linux_aarch64_initial/: the initial Eastern Washington/Northern California strict comparisons. Rounded headlines agree but strict intermediate checks fail; these failures remain visible.
- linux_aarch64_full_rebuild/: environment, empty-output provenance, every completed Python invocation and runtime, per-region main-chain timings, input hashes, rebuild state, and the actual missing-raw-ACS traceback. The journal includes an explicit failed extraction and documented shipped-extract input fallback.
- linux_aarch64_analysis/: every original ledger check, named evidence rows, all strict file/column differences and maxima, and every rebuilt PNG's pixel comparison. Historical total-ledger/source accounting is retained as recorded.
- linux_aarch64_initial_preflight/: earlier quick/full transcripts, regional ledgers and regression-test records. Their broader source-gating policy is historical, not the current exit policy.
- ledger/: the standalone ledger and corruption self-test records, plus test output.
- preflight/: current scoped quick/full transcripts, computational/source accounting, source-check rows, regression results and audit-origin metadata. The full audit reused the recorded clean rebuild; it is not another five-region benchmark. NEGATIVE_* files are clearly labelled deliberate test fixtures, not scientific source evidence.

## Current verdicts

The quick scope is one region's printed values and sensitivity rows; it makes no pooled claim:

    HEADLINE (printed numbers for eastern-wa): PASS 71/71
    FULL INTERMEDIATES (strict, informational): 3 of 20 files identical; differences explained in <scratch>/FULL_INTERMEDIATES.md
    QUOTED SOURCES (not shipped; verify at the SOURCES.md URLs, or pass --sources DIR): 9 checks SKIPPED

The full computational label is `HEADLINE (every printed number computed from the data): PASS 193/193`; its strict line reports 44 of 206 files identical. Only computational HEADLINE controls exit. A computational failure/skip fails; the nine quoted-document checks stay explicit and separate. Supplying local documents runs and counts them without changing the computational exit. SKIPPED never means PASS.

The strict comparator's exact count/identifier policy and float rel 1e-9 / abs 1e-12 remain intact. PNG pixel differences are informational; seven of 13 rebuilt PNGs are pixel-identical. The raw national Census files and nine external-document quotations are not independently verified by an offline run using the shipped extracts.

The author preserves both historical and current verdicts rather than rewriting unsuccessful checks. REPRODUCE.md gives the runnable commands; CHANGELOG.md describes the release changes without introducing new measured numbers.
