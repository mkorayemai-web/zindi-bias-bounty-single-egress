"""Quick one-region two-tier preflight. Safe scratch copy; no committed writes.
Rebuilds all configurations printed in the region's sensitivity table, not just
main sink A. Pooled findings require preflight_all.sh. Strict comparator is used
UNCHANGED and logged separately. Exit status follows the printed-number ledger.
"""
import argparse
import contextlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from common import ROOT as DATA_ROOT
from preflight_verdicts import verdicts
from region_ledger import REGION_CHECK, build_plan, run_region
from quoted_sources import evaluate_sources, summarize

BASE = Path(__file__).resolve().parent.parent


def guard_scratch(scratch, baseline, data_root):
    s, b, d = scratch.resolve(), baseline.resolve(), (data_root / 'data').resolve()
    if not scratch.is_absolute() or s == b or b.is_relative_to(s) or s.is_relative_to(b) or d.is_relative_to(s) or s.is_relative_to(d):
        raise ValueError('scratch must be absolute and outside the repository/data, and cannot contain either')
    if s.exists():
        marker = s / 'quick_preflight_source.json'
        if not marker.is_file() or json.loads(marker.read_text()).get('source') != str(b):
            raise ValueError(f'refusing to erase unmarked/nonmatching scratch: {s}')
    return s


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('region', nargs='?', default='eastern-wa', choices=tuple(REGION_CHECK))
    p.add_argument('--sources', type=Path, help='local quoted-document directory; never changes computational exit')
    a = p.parse_args()
    if a.sources is not None and not a.sources.is_dir():
        p.error('--sources must be an existing directory')
    R = a.region
    data_root = Path(os.environ.get('BIAS_BOUNTY_ROOT', DATA_ROOT))
    S = guard_scratch(Path(os.environ.get('PREFLIGHT_DIR', str(Path(tempfile.gettempdir()) / f'preflight_{R}'))), BASE, data_root)
    if S.exists():
        shutil.rmtree(S)
    S.mkdir(parents=True)
    (S / 'quick_preflight_source.json').write_text(json.dumps({'source':str(BASE),'region':R})+'\n')
    for d in ('egress','validation','ext','work','tables'):
        shutil.copytree(BASE / d, S / d, ignore=shutil.ignore_patterns('__pycache__','duck_tmp'))
    for d in ('figs','logs','tmp','headline'):
        (S / d).mkdir()
    deleted = sorted(str(p.relative_to(S)) for d in ('work','tables') for p in (S / d).iterdir() if p.is_file() and R in p.name)
    (S / 'deleted.txt').write_text('\n'.join(deleted)+'\n')
    for rel in deleted:
        (S / rel).unlink()
    assert not any(p.is_file() and R in p.name for d in ('work','tables') for p in (S / d).iterdir())
    env = dict(os.environ, BIAS_BOUNTY_ROOT=str(data_root), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', ARROW_IO_THREADS='1',
               PROJ_NETWORK='OFF', PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(S/'tmp'),
               REBUILD_REAL_PY=sys.executable, REBUILD_STEP_LOG=str(S/'steps.jsonl'))
    for key in ('EGRESS_ROOT','LEDGER_TEST_DRAFT','LEDGER_TEST_OUT','LEDGER_REBUILD_LOG'):
        env.pop(key,None)
    print(f'Quick ledger scope: {R} printed region values and sensitivity-table cells only; use preflight_all.sh for pooled/full-entry checks.',flush=True)
    print(f'Clean slate: deleted {len(deleted)} region artifacts; scratch {S}',flush=True)
    steps = [['build_edges.py',R,'drv'], ['buildings_prep.py',R], ['pipeline.py',R,'drv','--force']]
    tags = build_plan(BASE,R)
    main_tags = [t for t in tags if '_drvplus_' not in t]
    plus_tags = [t for t in tags if '_drvplus_' in t]
    def variants(tag,cset):
        sink = 'B' if f'_{cset}_B' in tag else 'A'
        return ['variants.py',R,cset,sink] + (['--repair','25'] if tag.endswith('_r25') else ['--minload','20' if sink == 'A' else '100'])
    steps += [variants(t,'drv') for t in main_tags]
    steps += [['facilities2.py',R,'drv','A']]
    if plus_tags:
        steps += [['build_edges.py',R,'drvplus'], ['pipeline.py',R,'drvplus','--force']]
        steps += [variants(t,'drvplus') for t in plus_tags]
        if (BASE/'tables'/f'fac_{R}_drvplus_A.csv').exists():
            steps += [['facilities2.py',R,'drvplus','A']]
    rc = 0
    for i, step in enumerate(steps,1):
        log = S/'logs'/f'{i:02d}_{step[0]}.txt'
        print(f'Step {i}/{len(steps)}: {" ".join(step)}; log {log}',flush=True)
        with log.open('w') as f:
            rc = subprocess.run([sys.executable,str(S/'egress'/'rebuild_step.py'),*step],cwd=S/'egress',env=env,stdout=f,stderr=subprocess.STDOUT).returncode
        if rc:
            print(f'Required step failed: exit {rc}; remaining steps not run.',flush=True)
            break
    # The full-entry validators are deliberately not claimed by a region-only run.
    strict_log = S/'strict_comparator.log'
    with strict_log.open('w') as f:
        strict_rc = subprocess.run([sys.executable,str(BASE/'egress'/'preflight_compare.py'),
                                   '--repo',str(BASE),'--scratch',str(S),'--region',R,
                                   '--command-rc',str(rc),'--validations','0'],env=env,stdout=f,stderr=subprocess.STDOUT).returncode
    if (S/'comparison.json').exists():
        strict_raw: dict[str, Any] = json.loads((S/'comparison.json').read_text())
        strict = dict(bytes_identical=strict_raw['bytes_identical'], files_compared=len(strict_raw['files']))
    else:
        strict_raw = dict(files=[], later=[], missing=[], comparator_error=f'strict comparator exit {strict_rc}; see {strict_log}')
        strict = dict(bytes_identical=0, files_compared=0)
    explanation = S/'FULL_INTERMEDIATES.md'
    lines = ['# Strict intermediate differences (informational)', '',
             'Unchanged preflight_compare.py: counts/identifiers exact; floats rel 1e-9 / abs 1e-12. Identical in the verdict means BYTE-identical, not rounded agreement.',
             f'Comparator exit: {strict_rc}; full log: {strict_log}. This does not determine the preflight exit.',
             'Geometry rounding, snap/endpoint/boundary choices and float32/internal loads may differ. All differing fields remain exposed; causes not individually traced are not asserted as proven.', '',
             '| File | Column | Changed | Max abs diff | Outside strict tolerance |', '|---|---|---:|---:|---:|']
    for f in strict_raw['files']:
        for c in f['columns']:
            if c.get('different') or not c['ok']:
                lines.append(f'| {f["file"]} | {c["column"]} | {c.get("different")} | {c.get("max_abs_diff")} | {c.get("outside_tolerance")} |')
    if strict_raw.get('comparator_error'):
        lines += ['',strict_raw['comparator_error']]
    lines += ['', 'Not rebuilt / not compared by this quick chain: '+', '.join(strict_raw.get('later',[]))]
    explanation.write_text('\n'.join(lines)+'\n')
    with (S/'headline'/'ledger_stdout.txt').open('w') as f, contextlib.redirect_stdout(f):
        headline = run_region(BASE,S,R,S/'headline',command_rc=rc)
    print(f'Printed-number ledger: {S / "headline" / "region_numbers_ledger.csv"}; strict comparison: {strict_log}',flush=True)
    print('No full-entry or validation claim is made by the quick scope.',flush=True)
    quoted_rows = evaluate_sources((BASE/'DISCOVERY_DRAFT.md').read_text(), BASE/'ext', a.sources)
    import pandas as pd
    pd.DataFrame(quoted_rows).to_csv(S/'headline'/'quoted_source_checks.csv',index=False)
    quoted = summarize(quoted_rows)
    output, exit_code = verdicts(headline,strict,explanation,quoted,region=R)
    for line in output:
        print(line,flush=True)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
