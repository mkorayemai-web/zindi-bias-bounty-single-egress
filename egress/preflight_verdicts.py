"""Scoped computational verdict, strict information and separate source checks.

Only HEADLINE controls exit. A skipped computational check still fails; quoted
sources keep their real PASS/FAIL/SKIPPED statuses but do not affect this exit.
"""
from pathlib import Path


def verdicts(headline, strict, explanation, quoted_sources, region=None):
    n, passed = int(headline['total']), int(headline['passed'])
    okay = bool(n) and passed == n and headline.get('all_pass', False)
    scope = f'printed numbers for {region}' if region else 'every printed number computed from the data'
    first = (f'HEADLINE ({scope}): ' +
             (f'PASS {passed}/{n}' if okay else f'FAIL {n-passed}/{n}'))
    second = (f'FULL INTERMEDIATES (strict, informational): {strict["bytes_identical"]} of '
              f'{strict["files_compared"]} files identical; differences explained in {Path(explanation).resolve()}')
    q = quoted_sources
    if q['unverified'] == q['total'] and q['total']:
        details = f'{q["total"]} checks SKIPPED'
    else:
        details = f'{q["passed"]} PASS; {q["failed"]} FAIL; {q["unverified"]} SKIPPED ({q["total"]} checks)'
    third = ('QUOTED SOURCES (not shipped; verify at the SOURCES.md URLs, or pass --sources DIR): ' + details)
    return (first, second, third), 0 if okay else 1
