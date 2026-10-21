"""Serial clean rebuild of ALL finding dependencies, using the repository runners.

Usage: python egress/full_rebuild.py --scratch ABSOLUTE_DIR --data-root ROOT
       [--resume] [--acs-raw-dir LOCAL_DIR]
No network; never writes analysis outputs in the source checkout. work/, tables/
and figs/ start EMPTY. Only documented ext/ inputs are copied, with provenance.
Every Python invocation (including inside shell runners) is timed in steps.jsonl.
Missing raw national ACS files cause a recorded acs_ext failure and an explicit
shipped-extract input fallback, NOT a claim of raw-Census re-extraction.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
REGIONS = ('northern-ca', 'eastern-ok', 'maricopa-az', 'south-central-tx', 'eastern-wa')


def utc():
    return subprocess.check_output(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], text=True).strip()


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def prepare(scratch, data_root, raw_dir):
    if not scratch.is_absolute():
        raise ValueError('scratch must be absolute')
    scratch = scratch.resolve()
    protected_data = (data_root / 'data').resolve()
    if scratch == ROOT or ROOT.is_relative_to(scratch) or scratch.is_relative_to(ROOT) or protected_data.is_relative_to(scratch) or scratch.is_relative_to(protected_data):
        raise ValueError('scratch must be outside, and cannot contain, the source checkout or data')
    if scratch.exists():
        raise FileExistsError(f'refusing to erase existing scratch directory: {scratch}; use --resume')
    for r in REGIONS:
        for layer in ('overture-roads-unfiltered', 'overture-buildings', 'overture-pois', 'overture-infrastructure', 'census-acs-housing'):
            assert (data_root / 'data' / 'reference' / r / f'{r}-{layer}.parquet').is_file(), (r, layer)
        for layer in ('census-tracts', 'strata-tract-table'):
            assert (data_root / 'data' / 'strata' / r / f'{r}-{layer}.parquet').is_file(), (r, layer)
    scratch.mkdir(parents=True)
    for d in ('egress', 'validation', 'ext', 'verification'):
        shutil.copytree(ROOT / d, scratch / d, ignore=shutil.ignore_patterns('__pycache__'))
    for p in ROOT.iterdir():
        if p.is_file() and (p.suffix == '.md' or p.name == 'requirements.txt'):
            shutil.copy2(p, scratch / p.name)
    for d in ('work', 'tables', 'figs', 'logs', 'tmp'):
        (scratch / d).mkdir()
    if raw_dir:
        for name in ('acsdt5y2024-b25024.dat', 'acsdt5y2024-b25044.dat', 'acsdt5y2024-b25004.dat'):
            if (raw_dir / name).is_file():
                shutil.copy2(raw_dir / name, scratch / 'ext' / name)
    provenance = dict(prepared_utc=utc(), source_checkout=str(ROOT), data_root=str(data_root),
                      empty_output_dirs=['work', 'tables', 'figs'], serial=True,
                      numerical_pool_threads=1, duckdb_threads=4,
                      copied_ext_inputs={p.name: sha(p) for p in (scratch / 'ext').iterdir() if p.is_file()})
    (scratch / 'input_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--data-root', type=Path, required=True, help='directory containing data/')
    p.add_argument('--resume', action='store_true')
    p.add_argument('--acs-raw-dir', type=Path)
    args = p.parse_args()
    if not args.scratch.is_absolute():
        raise ValueError('scratch must be absolute')
    S = args.scratch.resolve()
    protected_data = (args.data_root / 'data').resolve()
    if S == ROOT or ROOT.is_relative_to(S) or S.is_relative_to(ROOT) or protected_data.is_relative_to(S) or S.is_relative_to(protected_data):
        raise ValueError('scratch must be outside, and cannot contain, the source checkout or data')
    if not args.resume:
        prepare(S, args.data_root, args.acs_raw_dir)
    elif not (S / 'input_provenance.json').is_file():
        raise ValueError('resume requires an existing prepared rebuild')
    env = dict(os.environ)
    for key in ('EGRESS_ROOT', 'LEDGER_TEST_DRAFT', 'LEDGER_TEST_OUT'):
        env.pop(key, None)
    env.update(BIAS_BOUNTY_ROOT=str(args.data_root), PYTHONDONTWRITEBYTECODE='1',
               TMPDIR=str(S / 'tmp'), MPLCONFIGDIR=str(S / 'tmp' / 'matplotlib'),
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               NUMEXPR_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', ARROW_IO_THREADS='1',
               PROJ_NETWORK='OFF', REBUILD_REAL_PY=sys.executable,
               REBUILD_STEP_LOG=str(S / 'steps.jsonl'))
    shim = S / 'timed-python'
    shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{S / "egress" / "rebuild_step.py"}" "$@"\n')
    shim.chmod(0o755)
    env['PY'] = str(shim)
    state_path = S / 'rebuild_state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {'started_utc': utc(), 'finished': [], 'fallbacks': []}
    def run(label, command, allow_missing_raw=False):
        if label in state['finished']:
            print(f'RESUME completed: {label}', flush=True)
            return
        started, t0 = utc(), time.monotonic()
        log = S / 'logs' / f'{label}.log'
        print(f'START {started} {label}: {" ".join(command)}', flush=True)
        with log.open('w') as f:
            rc = subprocess.run(command, cwd=S / 'egress', env=env, stdout=f, stderr=subprocess.STDOUT).returncode
        elapsed = time.monotonic() - t0
        print(f'END {utc()} {label}: exit={rc} seconds={elapsed:.3f} log={log}', flush=True)
        with (S / 'runner_times.jsonl').open('a') as f:
            f.write(json.dumps(dict(label=label, started_utc=started, ended_utc=utc(), seconds=elapsed, command=command, exit_code=rc, log=str(log))) + '\n')
        if rc and allow_missing_raw:
            text = log.read_text(errors='replace')
            assert 'FileNotFoundError' in text and 'acsdt5y2024-b250' in text, text
            state['fallbacks'].append(dict(step=label, reason='raw national ACS files absent; use documented shipped ACS extract as an INPUT, not a rebuilt output', log=str(log)))
        elif rc:
            state_path.write_text(json.dumps(state, indent=2) + '\n')
            raise RuntimeError(f'{label} failed (exit {rc}); see {log}')
        state['finished'].append(label)
        state_path.write_text(json.dumps(state, indent=2) + '\n')
    def py(label, script, *a):
        run(label, [str(shim), script, *map(str, a)])
    # Use the existing serial region runners; their PY invocations are instrumented.
    run('acs_ext', [str(shim), 'acs_ext.py'], allow_missing_raw=True)
    run('stage_all', ['sh', str(S / 'egress' / 'run_stage_all.sh')])
    run('stage_wa', ['sh', str(S / 'egress' / 'run_stage_wa.sh')])
    run('finalize_m1', ['sh', str(S / 'egress' / 'finalize_m1.sh')])
    py('validate_tehama', '../validation/validate_tehama.py')
    py('validate_hays', '../validation/validate_hays.py')
    # Complete all additional source tables read by numbers_ledger.py, rather
    # than accidentally testing a mixture of rebuilt and shipped result tables.
    for r in REGIONS:
        py('coverage_' + r, 'coverage_bridge.py', r)
        py('latent_' + r, 'sens_nearmiss2.py', r, 50, 100, 250)
    # The queued TX runner now has both prerequisite markers, no wait/poll job.
    for name in ('nm2.done', 'cb.done'):
        (S / 'work' / name).write_text(utc() + '\n')
    run('tx_plus', ['sh', str(S / 'egress' / 'run_tx_plus.sh')])
    py('stats_drvplus_complete', 'stats.py', 'drvplus_A', 2000, 'eq')
    py('sens_table_complete', 'sens_table.py')
    for r in REGIONS:
        py('named_' + r, 'named_lists.py', r, 'drv_A')
        py('pinholes_' + r, 'pinhole_list.py', r, 50)
        py('response_strict_' + r, 'response_time.py', r)
        py('response_broad_' + r, 'response_time.py', r, '--broad')
    for script in ('seasonal.py', 'seasonal2.py', 'seasonal_robust.py', 'county_boot.py',
                   'county_boot_facilities.py', 'density_dissoc.py', 'persons_per_dwelling_ci.py',
                   'seasonal_load.py', 'seasonal_alloc_robust.py', 'stranded.py', 'named_station_check.py',
                   's30_scorecard_tracts.py', 'egress_km_by_class.py', 'coverage_bridge_agg.py',
                   'resp_summary.py', 'double_trap.py', 'latent_sweep_table.py', 'pinhole_summary.py'):
        py(Path(script).stem, script)
    py('validate_hays_repair', '../validation/validate_hays_repair.py')
    py('validate_tehama_repair', '../validation/validate_tehama_repair.py')
    for script in ('pinhole_md.py', 'calibration_md.py', 'figs_m1.py', 'figs_forest.py',
                   'figs_regions.py', 'figs_m2.py', 'figs_pinholes.py', 'figs_resort.py'):
        py(Path(script).stem, script)
    state['ended_utc'] = utc()
    state['analysis_outputs_started_empty'] = True
    state_path.write_text(json.dumps(state, indent=2) + '\n')
    print(f'FULL REBUILD FINISHED {state["ended_utc"]}; raw-input fallbacks={len(state["fallbacks"])}; tables/work/figures are in {S}', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
