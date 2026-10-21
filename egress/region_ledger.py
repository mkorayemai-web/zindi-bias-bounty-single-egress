"""Region-scoped extension of the printed-number ledger for the quick preflight.

Checks the region's draft S30 value, REPRODUCE.md printed values, and EVERY
printed percentage in that region's sensitivity-table rows. Uses half a unit of
the last printed digit, like numbers_ledger.py; strict intermediates are separate.
Pooled/other-region findings are NOT claimed by a single-region quick check.
Usage: python egress/region_ledger.py --baseline REPO --candidate SCRATCH
       --region REGION --out DIR
"""
import argparse
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

REGION_CHECK = {'northern-ca':'F1.10', 'eastern-ok':'F1.11', 'maricopa-az':'F1.12',
                'south-central-tx':'F1.13', 'eastern-wa':'F1.14'}
SCHEME = {'ACS dwellings':'eq', 'area-weighted dwellings':'ar', 'structure count':'str'}


def printed_tolerance(token):
    value = token.rstrip('%').replace(',', '')
    decimals = len(value.split('.',1)[1]) if '.' in value else 0
    return 0.5 * 10**(-decimals)


def sensitivity_rows(root, region):
    rows = []
    for line in (root / 'tables' / 'sens_grid.md').read_text().splitlines():
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if cells and cells[0] == region:
            if len(cells) != 9:
                raise ValueError('malformed sensitivity row: '+line)
            rows.append(cells)
    if not rows:
        raise ValueError(f'no printed sensitivity rows for {region}')
    return rows


def summary_tag(cells):
    region, classes, sink, repair = cells[:4]
    if classes not in ('scored classes','+service+track') or not sink.startswith(('A:','B:')) or repair not in ('none','snap dead ends <=25 m'):
        raise ValueError('unsupported sensitivity configuration: '+str(cells[:4]))
    cset = 'drv' if classes == 'scored classes' else 'drvplus'
    variant = 'A' if sink.startswith('A:') else 'B'
    return f'{region}_{cset}_{variant}' + ('_r25' if repair != 'none' else '')


def build_plan(root, region):
    return sorted({summary_tag(cells) for cells in sensitivity_rows(root,region)})


def run_region(baseline, candidate, region, out, command_rc=0):
    if region not in REGION_CHECK:
        raise ValueError('unknown region')
    rows, cache = [], {}
    def get(tag, scheme, col):
        try:
            if tag not in cache:
                d = pd.read_csv(candidate / 'tables' / f'{tag}_summary.csv', float_precision='round_trip')
                if not d.scheme.is_unique or not (d.tag == tag).all():
                    raise ValueError('summary schema/tag mismatch')
                cache[tag] = d.set_index('scheme')
            return float(cache[tag].loc[scheme, col])
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            return np.nan
    def add(cid, printed, actual, tolerance, source, text):
        ok = np.isfinite(actual) and abs(printed-actual) <= tolerance + 1e-9
        rows.append(dict(id=cid, printed=printed, recomputed=actual, tolerance=tolerance,
                         status='OK' if ok else ('MISSING-REBUILD' if not np.isfinite(actual) else 'MISMATCH'),
                         source=source, draft_text=text))
    eq = f'{region}_drv_A'
    ledger = pd.read_csv(baseline / 'tables' / 'numbers_ledger.csv').set_index('id')
    r = ledger.loc[REGION_CHECK[region]]
    if r.draft_text not in (baseline / 'DISCOVERY_DRAFT.md').read_text():
        raise ValueError('draft/ledger anchor mismatch')
    actual_s30 = 100 * get(eq,'eq','dwell_s30') / get(eq,'eq','den')
    add(REGION_CHECK[region], float(r.quoted), actual_s30, float(r.tolerance), f'tables/{eq}_summary.csv (eq)', r.draft_text)
    reproduce = (baseline / 'REPRODUCE.md').read_text()
    if region == 'eastern-wa':
        line = next(l for l in reproduce.splitlines() if l.startswith('Expected (tables/eastern-wa_drv_A_summary.csv'))
        fields = [('den',r'dwellings ([\d,]+)',1), ('isl',r'islands ([\d.]+)%',100),
                  ('spof',r'single route ([\d.]+)%',100), ('s10',r'S10 ([\d.]+)%',100),
                  ('s30',r'S30 ([\d.]+)%',100), ('dwell_s30',r'S30 [\d.]+% \(([\d,]+) dwellings',1),
                  ('persons_s30',r'/ ([\d,]+) persons',1), ('s100',r'S100 ([\d.]+)%',100), ('s300',r'S300 ([\d.]+)%',100)]
        for col, pattern, scale in fields:
            token = re.search(pattern,line).group(1)
            add('REPRO.'+col, float(token.replace(',','')), scale*get(eq,'eq',col), printed_tolerance(token),
                f'tables/{eq}_summary.csv (eq)', token+' in REPRODUCE.md step 1')
    else:
        short = {'northern-ca':'N-CA','eastern-ok':'E-OK','maricopa-az':'Maricopa','south-central-tx':'S-C Texas'}[region]
        token = re.search(re.escape(short)+r'(?: S30)? ([\d.]+)%', next(l for l in reproduce.splitlines() if l.startswith('Other regions ('))).group(1)
        add('REPRO.s30', float(token), 100*get(eq,'eq','s30'), printed_tolerance(token), f'tables/{eq}_summary.csv (eq)', short+' S30 '+token+'%')
    for i, cells in enumerate(sensitivity_rows(baseline,region),1):
        tag, scheme = summary_tag(cells), SCHEME[cells[4]]
        for label, col, token in zip(('single route','S30','S100','S300'), ('spof','s30','s100','s300'), cells[5:]):
            add(f'SENS.{i:02d}.{col}', float(token.rstrip('%')), 100*get(tag,scheme,col), printed_tolerance(token),
                f'tables/{tag}_summary.csv ({scheme})', ' | '.join(cells[:5])+' | '+label+' '+token)
    # Like the full ledger's code/metadata flags, retain an explicit execution
    # gate so surviving outputs cannot greenwash a failed required command.
    add('EXEC.required_steps', 0, float(command_rc), 0, 'quick rebuild command status', 'all required commands exited zero')
    out.mkdir(parents=True,exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out / 'region_numbers_ledger.csv', index=False)
    summary = dict(scope=f'quick {region}: printed region draft / REPRODUCE / sensitivity cells ONLY; no pooled or other-region claim',
                   region=region, total=len(df), passed=int((df.status=='OK').sum()),
                   failed=int((df.status!='OK').sum()), unverified=0, all_pass=bool((df.status=='OK').all()),
                   required_configurations=build_plan(baseline,region))
    (out / 'HEADLINE_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(summary['scope'])
    for r in df.itertuples():
        print(f'{r.id}: {"PASS" if r.status == "OK" else "FAIL"} printed={r.printed:.15g} Linux={r.recomputed:.15g} tolerance={r.tolerance:.15g} [{r.source}]')
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','candidate','out'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--region',required=True,choices=tuple(REGION_CHECK))
    a = p.parse_args()
    result = run_region(a.baseline,a.candidate,a.region,a.out)
    return 0 if result['all_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
