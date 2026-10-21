"""Instrument each Python invocation made by a serial full-rebuild runner.
Not an analysis step: forwards stdout/stderr and exit status unchanged, records
UTC start/end, wall seconds, command, cwd and changed files in JSONL.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def stamp():
    return subprocess.check_output(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], text=True).strip()


def main():
    root = Path(__file__).resolve().parent.parent
    ledger = Path(os.environ['REBUILD_STEP_LOG'])
    started, t0 = stamp(), time.monotonic()
    before = {str(p.relative_to(root)): (p.stat().st_mtime_ns, p.stat().st_size)
              for top in ('work', 'tables', 'figs', 'ext') for p in (root / top).rglob('*') if p.is_file()}
    command = [os.environ['REBUILD_REAL_PY'], *sys.argv[1:]]
    rc = subprocess.run(command).returncode
    after = {str(p.relative_to(root)): (p.stat().st_mtime_ns, p.stat().st_size)
             for top in ('work', 'tables', 'figs', 'ext') for p in (root / top).rglob('*') if p.is_file()}
    record = dict(started_utc=started, ended_utc=stamp(), wall_seconds=time.monotonic()-t0,
                  command=command, cwd=os.getcwd(), exit_code=rc,
                  rewritten=[p for p in sorted(after) if before.get(p) != after[p]])
    with ledger.open('a') as f:
        f.write(json.dumps(record) + '\n')
    print(f'REBUILD STEP exit={rc} seconds={record["wall_seconds"]:.3f} command={" ".join(sys.argv[1:])}', flush=True)
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
