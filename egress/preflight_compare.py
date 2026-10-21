"""Value-level companion to preflight.sh (stdlib, numpy, pandas).

Byte identity is informational. Values pass only with identical shape/schema/order,
exact identifiers/booleans/integer counts, and float agreement at rtol=1e-9,
atol=1e-12. No platform-specific exclusions or relaxed tolerances are applied.
Every changed column/array and its maximum absolute difference is reported.
Usage: python preflight_compare.py --repo REPO --scratch COPY --region REGION
       [--command-rc RC] [--validations 0|1]
The copy must contain deleted.txt, produced BEFORE rebuilding by preflight.sh.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

RTOL, ATOL = 1e-9, 1e-12
# These may be stored as floats but are counts/identifiers, not weighted estimates.
EXACT_FIELDS = {'top_str', 'sub_str', 'load_struct', 'n_cand', 'HU', 'POP', 'POP_eff', 'structure_den_exact',
                'tract', 'GEOID', 'bidx', 'tract_i', 'child', 'edge', 'cluster',
                'node', 'piece', 'upd_year', 'postcode'}
CSV_STRINGS = {'id': str, 'tract': str, 'GEOID': str, 'postcode': str}


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def array_result(name, expected, computed):
    x, y = np.asarray(expected), np.asarray(computed)
    r = dict(column=str(name), expected_dtype=str(x.dtype), computed_dtype=str(y.dtype),
             expected_shape=list(x.shape), computed_shape=list(y.shape))
    if x.shape != y.shape or x.dtype != y.dtype:
        return dict(r, ok=False, different=None, max_abs_diff=None, reason='shape/dtype differs')
    missing_x, missing_y = pd.isna(x), pd.isna(y)
    numeric = x.dtype.kind in 'biuf'
    if numeric:
        same = (x == y) | (missing_x & missing_y)
        exact = name in EXACT_FIELDS or x.dtype.kind in 'biu'
        if exact:
            close = same
        else:
            close = np.isclose(x, y, rtol=RTOL, atol=ATOL, equal_nan=True)
        finite = np.isfinite(x) & np.isfinite(y)
        delta = np.abs(x[finite].astype(np.longdouble) - y[finite].astype(np.longdouble))
        maxabs = float(delta.max()) if delta.size else 0.0
        if np.any((~finite) & ~same):
            maxabs = None  # missing/nonfinite mismatch; zero is not a valid distance
        r.update(mode='exact' if exact else 'float', max_abs_diff=maxabs)
    else:
        same = np.asarray(pd.Series(x.ravel()).eq(pd.Series(y.ravel())).fillna(False)).reshape(x.shape) | (missing_x & missing_y)
        close = same
        r.update(mode='exact', max_abs_diff=None)
    bad = np.flatnonzero(~same)
    r.update(ok=bool(np.all(close)), different=int(np.count_nonzero(~same)),
             outside_tolerance=int(np.count_nonzero(~close)),
             examples=[dict(position=int(i), expected=str(x.ravel()[i]), computed=str(y.ravel()[i])) for i in bad[:3]])
    return r


def compare_file(a, b):
    result = dict(bytes_equal=digest(a) == digest(b), columns=[])
    if a.suffix == '.npz':
        with np.load(a) as x, np.load(b) as y:
            schema = x.files == y.files
            result['schema_equal'] = schema
            if schema:
                result['columns'] = [array_result(k, x[k], y[k]) for k in x.files]
    elif a.suffix in ('.csv', '.parquet'):
        if a.suffix == '.csv':
            x, y = (pd.read_csv(p, dtype=CSV_STRINGS, float_precision='round_trip') for p in (a, b))
        else:
            x, y = pd.read_parquet(a), pd.read_parquet(b)
        result['schema_equal'] = x.shape == y.shape and x.columns.equals(y.columns) and x.index.equals(y.index)
        result['expected_shape'], result['computed_shape'] = list(x.shape), list(y.shape)
        if result['schema_equal']:
            result['columns'] = [array_result(k, x[k].to_numpy(), y[k].to_numpy()) for k in x.columns]
            # Structure-weighted summary denominators are integer counts, despite a float dtype.
            if a.name.endswith('_summary.csv') and {'scheme', 'den'}.issubset(x.columns):
                ix = x.scheme == 'str'
                result['columns'].append(array_result('structure_den_exact', x.loc[ix, 'den'].to_numpy(), y.loc[ix, 'den'].to_numpy()))
                result['columns'][-1]['ok'] = bool(x.loc[ix, 'den'].equals(y.loc[ix, 'den']))
    else:
        # Text summaries retain the previous byte-exact gate; no numbers are silently discarded.
        result['schema_equal'] = True
        result['columns'] = [dict(column='<raw text>', ok=result['bytes_equal'], different=int(not result['bytes_equal']), max_abs_diff=None, mode='exact')]
    result['values_equal'] = result['schema_equal'] and all(c['ok'] for c in result['columns'])
    return result


def headline(repo, scratch, region):
    rel = Path('tables') / f'{region}_drv_A_summary.csv'
    a, b = (pd.read_csv(root / rel, float_precision='round_trip').set_index('scheme').loc['eq'] for root in (repo, scratch))
    fields = [('dwellings', 'den', 1, ',.0f'), ('islands %', 'isl', 100, '.2f'),
              ('single route %', 'spof', 100, '.2f'), ('S10 %', 's10', 100, '.2f'),
              ('S30 %', 's30', 100, '.2f'), ('S30 dwellings', 'dwell_s30', 1, ',.0f'),
              ('S30 persons', 'persons_s30', 1, ',.0f'), ('S100 %', 's100', 100, '.2f'),
              ('S300 %', 's300', 100, '.2f')]
    print('Headline values (expected = committed summary, eq; also REPRODUCE.md step 1 for Eastern WA):')
    result = []
    for label, col, scale, fmt in fields:
        expected, computed = float(a[col]) * scale, float(b[col]) * scale
        ok = bool(np.isclose(computed, expected, rtol=RTOL, atol=ATOL))
        print(f'  {label:18s} expected {expected:{fmt}} | computed {computed:{fmt}} | abs diff {abs(expected-computed):.12g} | {"PASS" if ok else "FAIL"}')
        result.append(dict(label=label, expected=expected, computed=computed, ok=ok))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--region', required=True)
    p.add_argument('--command-rc', type=int, default=0)
    p.add_argument('--validations', type=int, choices=(0, 1), default=0)
    args = p.parse_args()
    L, S, R = args.repo, args.scratch, args.region
    deleted = (S / 'deleted.txt').read_text().splitlines()
    core = {f'tables/{R}_drv_A_summary.csv', f'tables/{R}_drv_A_links.csv',
            f'tables/fac_{R}_drv_A.csv', f'tables/fac_clusters_{R}_drv_A.csv'}
    core |= {w for w in (f'work/{R}_drv_snap.parquet', f'work/{R}_drv_A_tract.parquet', f'work/{R}_drv_A_nodes.npz') if (L / w).exists()}
    if R == 'south-central-tx':
        core |= {w for w in (f'work/{R}_drv_A_r25_bres.parquet', f'work/{R}_nm50_bld.parquet', f'work/{R}_nm100_bld.parquet', f'work/{R}_nm250_bld.parquet') if (L / w).exists()}
    if args.validations:
        core |= {d for d in deleted if Path(d).name.startswith('validation_')}
    report = dict(region=R, rtol=RTOL, atol=ATOL, integer_counts='exact', command_rc=args.command_rc,
                  validations='run' if args.validations else 'skipped: northern-ca / south-central-tx building files unavailable', files=[], missing=[], later=[])
    print(f'Value policy: integer counts / identifiers exact; floats rel {RTOL:g} / abs {ATOL:g}; no relaxed tolerances.')
    for rel in sorted(core - set(deleted)):
        report['missing'].append(rel)
        print(f'  {rel}: FAIL (not deleted / baseline missing)')
    for rel in deleted:
        a, b = L / rel, S / rel
        if not b.exists():
            if rel in core:
                report['missing'].append(rel)
                print(f'  {rel}: FAIL (not re-written)')
            else:
                report['later'].append(rel)
            continue
        r = dict(file=rel, **compare_file(a, b))
        report['files'].append(r)
        print(f'  {rel}: bytes {"IDENTICAL" if r["bytes_equal"] else "DIFFERENT (informational)"}; values {"PASS" if r["values_equal"] else "FAIL"}')
        for c in r['columns']:
            if c.get('different') or not c['ok']:
                print(f'    {c["column"]}: {c.get("mode", "schema")}; changed={c.get("different")}; outside tolerance={c.get("outside_tolerance")}; max abs diff={c["max_abs_diff"]}; {"PASS" if c["ok"] else "FAIL"}')
                if not c['ok']:
                    for example in c.get('examples', []):
                        print(f'      row/index {example["position"]}: expected {example["expected"]}; computed {example["computed"]}')
    if (S / f'tables/{R}_drv_A_summary.csv').exists():
        report['headlines'] = headline(L, S, R)
    report['bytes_identical'] = sum(f['bytes_equal'] for f in report['files'])
    report['values_pass'] = sum(f['values_equal'] for f in report['files'])
    report['ok'] = not args.command_rc and not report['missing'] and len(report['files']) >= len(core) and all(f['values_equal'] for f in report['files'])
    print(f'Deleted {len(deleted)}; re-written and compared {len(report["files"])}; bytes identical {report["bytes_identical"]}; values PASS {report["values_pass"]}; missing {len(report["missing"])}; commands failed {bool(args.command_rc)}')
    print(f'Not produced by this chain, explicitly not compared ({len(report["later"])}): ' + ', '.join(report['later']))
    (S / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PREFLIGHT PASS' if report['ok'] else 'PREFLIGHT FAIL')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
