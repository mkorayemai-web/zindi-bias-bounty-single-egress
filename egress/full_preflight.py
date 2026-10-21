"""Full computational HEADLINE, strict information and separate quoted sources.
Usage: PY=python sh egress/preflight_all.sh [--existing-rebuild ABSOLUTE_DIR]
       [--sources ABSOLUTE_DIR]
Existing rebuilds require completed clean-start provenance. Quoted documents are
checked separately and never change the computational HEADLINE exit status.
"""
import argparse
import contextlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from common import ROOT as DATA_ROOT
from finding_audit import full_audit
from preflight_verdicts import verdicts
from quoted_sources import evaluate_sources, summarize

BASE = Path(__file__).resolve().parent.parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--existing-rebuild', type=Path)
    p.add_argument('--data-root', type=Path, default=Path(DATA_ROOT))
    p.add_argument('--sources', type=Path, help='local quoted-document directory (no network)')
    a = p.parse_args()
    if a.sources is not None and not a.sources.is_dir():
        p.error('--sources must be an existing directory')
    if a.existing_rebuild:
        candidate = a.existing_rebuild
        resolved = candidate.resolve()
        if not candidate.is_absolute() or resolved == BASE or resolved.is_relative_to(BASE) or BASE.is_relative_to(resolved):
            raise ValueError('existing rebuild must be an absolute scratch path outside the source checkout and cannot contain it')
    else:
        candidate = Path(os.environ.get('PREFLIGHT_DIR', str(Path(tempfile.gettempdir()) / f'preflight_all_{os.getpid()}')))
        print(f'Full rebuild: {candidate}; all regions serial, at most four computational threads.', flush=True)
        rc = subprocess.run([sys.executable, str(BASE/'egress'/'full_rebuild.py'),
                             '--scratch',str(candidate),'--data-root',str(a.data_root)]).returncode
        if rc:
            print('Full rebuild failed; no computational PASS is possible.', flush=True)
            quoted = summarize(evaluate_sources((BASE/'DISCOVERY_DRAFT.md').read_text(),BASE/'ext',a.sources))
            output, status = verdicts(dict(total=1,passed=0,all_pass=False),
                                      dict(bytes_identical=0,files_compared=0),candidate/'rebuild_state.json',quoted)
            for line in output: print(line,flush=True)
            return status
    out = candidate/'finding_audit'
    out.mkdir(parents=True,exist_ok=True)
    print('Full scope: every printed number computed from the data; quoted external documents are counted separately, never silently passed.',flush=True)
    with (out/'audit_stdout.txt').open('w') as f, contextlib.redirect_stdout(f):
        result = full_audit(BASE,candidate,out,sources=a.sources)
    print(f'Computed checks: {result["passed"]} PASS; {result["failed"]} FAIL; {result["unverified"]} UNVERIFIED. Every check: {out / "EVERY_LEDGER_CHECK.md"}',flush=True)
    print(f'Quoted-document checks: {out / "QUOTED_SOURCE_CHECKS.csv"}; PNG pixel differences: {out / "FIGURE_PIXEL_DIFFS.csv"}',flush=True)
    output, status = verdicts(result,result['full_intermediates'],out/'FULL_INTERMEDIATES.md',result['quoted_sources'])
    for line in output: print(line,flush=True)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
