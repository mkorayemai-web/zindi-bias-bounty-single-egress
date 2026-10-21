"""Self-test of numbers_ledger.py: proves text and value corruption FAIL.

Usage: python ledger_selftest.py -> SELFTEST PASS; exit 1 on any discrepancy.
Only scratch copies are corrupted. Undistributed source documents remain explicit
SKIPPED-NO-SOURCE, not failures. The unmodified baseline must have no failures.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_ROOT

SCRIPT = Path(REPO_ROOT) / 'egress' / 'numbers_ledger.py'
orig = (Path(REPO_ROOT) / 'DISCOVERY_DRAFT.md').read_text()
MUT = [
    ('17.0 M dwellings', '17.1 M dwellings', ['F1.01']),
    ('**2.15x**', '**2.16x**', ['W.03', 'G.01', 'G.02', 'G.03']),
    ('95 % CI 1.86-2.57, resampling', '95 % CI 1.86-2.58, resampling',
     ['W.04', 'W.05', 'W.06', 'W.07', 'W.08', 'G.01', 'G.02', 'G.03']),
    ('98.3 % of S30 dwellings', '98.9 % of S30 dwellings', ['I.11']),
    ('Buildings of 35 m2+', 'Buildings of 50 m2+', ['P.01', 'P.02']),
    ('(E. Washington about 1 minute)', '(E. Washington about 5 minutes)', ['R.02']),
]


def run(tmp, draft_text, script=SCRIPT, tag='x'):
    d = tmp / tag
    d.mkdir()
    p = d / 'draft.md'
    p.write_text(draft_text)
    # The corrupted ledger lives outside egress/. Preserve both module imports
    # and the actual data/repository root, rather than deriving them from TMP.
    env = dict(os.environ, LEDGER_TEST_DRAFT=str(p), LEDGER_TEST_OUT=str(d), EGRESS_ROOT=REPO_ROOT)
    env['PYTHONPATH'] = str(Path(REPO_ROOT) / 'egress') + os.pathsep + env.get('PYTHONPATH', '')
    proc = subprocess.run([sys.executable, str(script)], env=env, capture_output=True, text=True)
    if proc.returncode not in (0, 1) or not (d / 'numbers_ledger.csv').exists():
        raise RuntimeError(f'ledger subprocess failed ({tag}): {proc.stdout}\n{proc.stderr}')
    table = pd.read_csv(d / 'numbers_ledger.csv')
    failures = {r.id: r.status for r in table.itertuples() if r.status not in ('OK', 'SKIPPED-NO-SOURCE')}
    if (proc.returncode != 0) != bool(failures):
        raise AssertionError(f'ledger exit status disagrees with reported failures ({tag})')
    return failures, set(table.loc[table.status == 'SKIPPED-NO-SOURCE', 'id'])


def main():
    with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as tmp_name:
        tmp = Path(tmp_name)
        base, base_skips = run(tmp, orig, tag='base')
        assert not base, f'unmodified baseline has failing checks: {base}'
        mutated, expected = orig, set()
        for a, b, ids in MUT:
            assert orig.count(a) == 1, f'mutation anchor not unique: {a!r}'
            mutated = mutated.replace(a, b)
            expected.update(ids)
        got, mut_skips = run(tmp, mutated, tag='mut')
        ok1 = set(got) == expected and all(v == 'DRAFT-TEXT-MISSING' for v in got.values()) and mut_skips == base_skips
        print(f'text corruption: {len(MUT)} edits -> expected failing checks {sorted(expected)}')
        print(f'  observed: {sorted(got)} => {"detected exactly" if ok1 else "MISMATCH"}')
        src = SCRIPT.read_text()
        a = 'add("F1.03", "21.3 % reach the arterial network", 21.3,'
        assert src.count(a) == 1
        wrong = tmp / 'ledger_wrong_value.py'
        wrong.write_text(src.replace(a, a.replace('21.3,', '21.4,')))
        got2, wrong_skips = run(tmp, orig, script=wrong, tag='wrong')
        ok2 = got2 == {'F1.03': 'MISMATCH'} and wrong_skips == base_skips
        print(f'value corruption: quoted 21.4 instead of 21.3 -> {got2} => {"detected" if ok2 else "NOT DETECTED"}')
        print(f'baseline failures: {base}; explicitly skipped (undistributed sources): {sorted(base_skips)}')
        print('SELFTEST PASS' if ok1 and ok2 else 'SELFTEST FAIL')
        return 0 if ok1 and ok2 else 1


if __name__ == '__main__':
    raise SystemExit(main())
