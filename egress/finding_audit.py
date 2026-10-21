"""Audit every existing ledger check against a clean full rebuild; PNG differences
and strict intermediates are informational. Does not alter the draft/tolerances.
Usage: python egress/finding_audit.py --baseline REPO --candidate SCRATCH --out DIR
A skipped external-document check is explicit and separate from computational HEADLINE.
"""
import argparse
import ast
import csv
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from typing import Any

import numpy as np
import pandas as pd
from PIL import Image

from preflight_compare import compare_file
from quoted_sources import SOURCE_IDS, split_ledger


def pixel_diff(expected, computed):
    with Image.open(expected) as a, Image.open(computed) as b:
        a, b = np.asarray(a.convert('RGBA')), np.asarray(b.convert('RGBA'))
    h, w = max(a.shape[0], b.shape[0]), max(a.shape[1], b.shape[1])
    aa, bb = np.zeros((h, w, 4), dtype='uint8'), np.zeros((h, w, 4), dtype='uint8')
    ma, mb = np.zeros((h, w), bool), np.zeros((h, w), bool)
    aa[:a.shape[0], :a.shape[1]], bb[:b.shape[0], :b.shape[1]] = a, b
    ma[:a.shape[0], :a.shape[1]], mb[:b.shape[0], :b.shape[1]] = True, True
    changed = np.any(aa != bb, axis=2) | (ma != mb)
    return dict(expected_size=[a.shape[1], a.shape[0]], computed_size=[b.shape[1], b.shape[0]],
                different_pixels=int(changed.sum()), compared_canvas_pixels=h*w,
                max_channel_abs_diff=int(np.abs(aa.astype('int16')-bb.astype('int16')).max()))


def tally(table) -> dict[str, Any]:
    statuses = table.status.value_counts().to_dict()
    passed = int((table.status == 'OK').sum())
    unknown = int((table.status == 'SKIPPED-NO-SOURCE').sum())
    return dict(total=len(table), passed=passed, failed=len(table)-passed-unknown,
                unverified=unknown, all_pass=bool(len(table)) and passed == len(table), statuses=statuses)


def required_tables(script):
    names = {n.args[0].value for n in ast.walk(ast.parse(script)) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == 'T' and n.args
             and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)}
    names |= {'validation_tehama_summary.txt', 'validation_hays_summary.txt', 'fig3_validation_labels.txt'}
    return {f'tables/{name}' for name in names}


def full_audit(baseline, candidate, out, sources=None):
    out.mkdir(parents=True, exist_ok=True)
    if (baseline / 'DISCOVERY_DRAFT.md').read_bytes() != (candidate / 'DISCOVERY_DRAFT.md').read_bytes():
        raise ValueError('candidate draft differs; audit requires the SAME printed entry')
    state = json.loads((candidate / 'rebuild_state.json').read_text())
    if not state.get('analysis_outputs_started_empty') or not state.get('ended_utc'):
        raise ValueError('candidate is not a completed clean rebuild')
    steps = [json.loads(s) for s in (candidate / 'steps.jsonl').read_text().splitlines()]
    fresh = {f for s in steps if s['exit_code'] == 0 for f in s['rewritten']}
    script = Path(__file__).with_name('numbers_ledger.py')
    missing_sources = sorted(required_tables(script.read_text()) - fresh)
    if missing_sources:
        raise ValueError(f'ledger inputs were not freshly rebuilt: {missing_sources}')
    env = dict(os.environ, EGRESS_ROOT=str(candidate), LEDGER_TEST_DRAFT=str(candidate / 'DISCOVERY_DRAFT.md'),
               LEDGER_TEST_OUT=str(out), LEDGER_REBUILD_LOG=str(candidate / 'steps.jsonl'),
               PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               MKL_NUM_THREADS='1', ARROW_IO_THREADS='1')
    if sources is None:
        env.pop('LEDGER_SOURCES_DIR', None)
    else:
        env['LEDGER_SOURCES_DIR'] = str(Path(sources).resolve())
    # Never read a stale prior audit CSV if this ledger invocation crashes.
    for name in ('numbers_ledger.csv', 'NUMBERS_LEDGER.md'):
        (out / name).unlink(missing_ok=True)
    with (out / 'ledger_stdout.txt').open('w') as f:
        proc = subprocess.run([sys.executable, str(script)], env=env, stdout=f, stderr=subprocess.STDOUT)
    if not (out / 'numbers_ledger.csv').is_file():
        raise RuntimeError(f'ledger crashed (exit {proc.returncode}); see {out / "ledger_stdout.txt"}')
    ledger = pd.read_csv(out / 'numbers_ledger.csv', float_precision='round_trip')
    real_failures = ~ledger.status.isin(['OK','SKIPPED-NO-SOURCE'])
    if proc.returncode not in (0,1) or bool(proc.returncode) != bool(real_failures.any()):
        raise RuntimeError('ledger process exit disagrees with its newly generated check statuses')
    original = pd.read_csv(baseline / 'tables' / 'numbers_ledger.csv', float_precision='round_trip').set_index('id')
    pd.testing.assert_frame_equal(original[['quoted', 'tolerance']], ledger.set_index('id')[['quoted', 'tolerance']])
    overall = tally(ledger)
    computed, quoted = split_ledger(ledger)
    result = tally(computed)
    result.update(scope='every printed number computed from the data', ledger_exit=proc.returncode,
                  quoted_sources=tally(quoted), all_ledger_checks=overall,
                  sources_dir=str(Path(sources).resolve()) if sources is not None else None,
                  fresh_ledger_source_tables=len(required_tables(script.read_text())),
                  raw_input_fallbacks=state.get('fallbacks', []))
    quoted.to_csv(out / 'QUOTED_SOURCE_CHECKS.csv', index=False)
    report = ledger.copy()
    report['check_scope'] = report.id.map(lambda cid: 'quoted source' if cid in SOURCE_IDS else 'computed')
    report['baseline_recomputed'] = [original.loc[i, 'recomputed'] for i in report.id]
    report['linux_minus_baseline'] = report.recomputed - report.baseline_recomputed
    report['tier_status'] = report.status.map(lambda x: 'PASS' if x == 'OK' else ('UNVERIFIED' if x == 'SKIPPED-NO-SOURCE' else 'FAIL'))
    report['cause'] = [
        ('External citation document not distributed; no network access; not a recomputed analysis value.' if r.status == 'SKIPPED-NO-SOURCE'
         else ('Existing source/parameter/qualitative check agrees.' if pd.isna(r.quoted)
               else ('At original printed precision/tolerance.' if r.status == 'OK'
                     else 'Recomputed source table differs beyond the unchanged printed tolerance; see source and strict differences.')))
        for r in report.itertuples()]
    report.to_csv(out / 'EVERY_LEDGER_CHECK.csv', index=False)
    # Named evidence rows are whole-row flags in the ledger: preserve the actual
    # Linux row text too, so a changed GEOID/count cannot hide behind a Boolean.
    ranges = pd.read_csv(candidate / 'tables' / 'seasonal_load_range.csv', dtype={'tract': str})
    named = []
    for road, tract in [('Walden Road','48339694305'), ('Cranes Mill Road','48091310608'),
                        ('Queen Isabella Causeway','48061012305'), ('East 310 Road','40041375804'),
                        ('Alpine Meadows Road','06061022014'), ('Mountainaire Road','04005001500')]:
        r = ranges[(ranges.rname == road) & (ranges.tract == tract)].sort_values('load_dwell', ascending=False).iloc[0]
        named.append(dict(road=road, tract=tract, dwellings=float(r.load_dwell), persons=float(r.load_persons),
                          low=float(r.peak_low), mid=float(r.peak_mid), high=float(r.peak_high)))
    (out / 'NAMED_ROWS_LINUX.json').write_text(json.dumps(named, indent=2) + '\n')
    lines = ['# Every printed-number ledger check: Linux full rebuild', '',
             'Same draft and original tolerances. PASS means OK; FAIL is a real failed check; UNVERIFIED is SKIPPED-NO-SOURCE, NOT a pass.',
             f'Computed checks: {result["passed"]}/{result["total"]} PASS, {result["failed"]} FAIL, {result["unverified"]} UNVERIFIED.',
             f'Quoted sources (separate, not computational): {result["quoted_sources"]["passed"]} PASS, {result["quoted_sources"]["failed"]} FAIL, {result["quoted_sources"]["unverified"]} SKIPPED; all {overall["total"]} ledger rows remain below.',
             'Computed primary tables start empty and are all rebuilt. Documented shipped ACS extracts remain external INPUTS when raw national files are absent; see input_provenance.json and rebuild_state.json.', '',
             '| Check | Status | Printed value | Linux value | Original tolerance | Text / source |', '|---|---|---:|---:|---:|---|']
    for r in report.itertuples():
        fmt = lambda v: '-' if pd.isna(v) else f'{v:.15g}'
        text = (r.draft_text + ' / ' + r.source).replace('|','/')
        lines.append(f'| {r.id} | {r.tier_status} | {fmt(r.quoted)} | {fmt(r.recomputed)} | {fmt(r.tolerance)} | {text} |')
    (out / 'EVERY_LEDGER_CHECK.md').write_text('\n'.join(lines) + '\n')
    strict = []
    expected_release = subprocess.check_output(['git', '-C', str(baseline), 'ls-files', '-z']).decode().split('\0')
    for rel in sorted(set(expected_release) & fresh):
        if not rel or not rel.startswith(('tables/', 'work/', 'figs/', 'ext/')):
            continue
        a, b = baseline / rel, candidate / rel
        if not a.is_file() or not b.is_file():
            continue
        try:
            item = dict(file=rel, **compare_file(a,b))
        except Exception as e:
            item = dict(file=rel, bytes_equal=False, values_equal=False, error=f'{type(e).__name__}: {e}', columns=[])
        strict.append(item)
    strict_summary = dict(files_compared=len(strict), bytes_identical=sum(f['bytes_equal'] for f in strict),
                          strict_values_pass=sum(f['values_equal'] for f in strict), files=strict,
                          policy='unchanged preflight_compare.py; exact counts/IDs; float rel 1e-9 / abs 1e-12; informational')
    (out / 'FULL_INTERMEDIATES.json').write_text(json.dumps(strict_summary, indent=2) + '\n')
    diff_lines = ['# Strict intermediate differences (informational)', '', strict_summary['policy'],
                  f'{strict_summary["bytes_identical"]} of {len(strict)} files byte-identical; {strict_summary["strict_values_pass"]} pass strict value comparison.', '',
                  'The comparator is unchanged. Numeric rounding differences, discrete snap/boundary assignments and raster rendering differences are exposed, not waived. Unlocalized causes are not asserted as proven.', '',
                  '| File | Column / array | Different cells | Max abs diff | Outside strict tolerance |', '|---|---|---:|---:|---:|']
    for f in strict:
        for c in f['columns']:
            if c.get('different') or not c['ok']:
                diff_lines.append(f'| {f["file"]} | {c["column"]} | {c.get("different")} | {c.get("max_abs_diff")} | {c.get("outside_tolerance")} |')
        if not f['values_equal'] and not f['columns']:
            diff_lines.append(f'| {f["file"]} | schema / exception | - | - | {f.get("error", "schema/order mismatch")} |')
    (out / 'FULL_INTERMEDIATES.md').write_text('\n'.join(diff_lines) + '\n')
    pixels = []
    for a in sorted((baseline / 'figs').glob('*.png')):
        b = candidate / 'figs' / a.name
        if not b.is_file() or 'figs/' + a.name not in fresh:
            pixels.append(dict(file=a.name, status='NOT REBUILT', different_pixels=None))
        else:
            pixels.append(dict(file=a.name, status='REBUILT', **pixel_diff(a,b)))
    pd.DataFrame(pixels).to_csv(out / 'FIGURE_PIXEL_DIFFS.csv', index=False)
    result.update(figures=pixels, full_intermediates={k:v for k,v in strict_summary.items() if k != 'files'})
    (out / 'HEADLINE_RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'figures'}, indent=2))
    print(f'Per-check report: {out / "EVERY_LEDGER_CHECK.md"}')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('baseline', 'candidate', 'out'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--sources', type=Path, help='local quoted-document directory (not computational HEADLINE)')
    args = p.parse_args()
    if args.sources is not None and not args.sources.is_dir():
        p.error('--sources must be an existing directory')
    result = full_audit(args.baseline, args.candidate, args.out, sources=args.sources)
    return 0 if result['all_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
