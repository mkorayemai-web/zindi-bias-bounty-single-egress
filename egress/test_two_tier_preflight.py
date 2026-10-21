"""Two-tier preflight regression tests (small fixtures; no graph rebuild)."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import pandas as pd

from preflight_verdicts import verdicts
from quick_preflight import guard_scratch
from region_ledger import build_plan, printed_tolerance, run_region

QUOTED_SKIP = dict(total=9, passed=0, failed=0, unverified=9, all_pass=False)

ROOT = Path(__file__).resolve().parent.parent


class TwoTierTests(unittest.TestCase):
    def test_strict_differences_and_quoted_skips_do_not_fail_headline(self):
        lines, rc = verdicts(dict(total=3,passed=3,all_pass=True),dict(bytes_identical=0,files_compared=7),'/some/report.md',QUOTED_SKIP)
        self.assertEqual(rc,0)
        self.assertEqual(len(lines),3)
        self.assertEqual(lines[0],'HEADLINE (every printed number computed from the data): PASS 3/3')
        self.assertTrue(lines[1].startswith('FULL INTERMEDIATES (strict, informational): 0 of 7 files identical;'))
        self.assertEqual(lines[2],'QUOTED SOURCES (not shipped; verify at the SOURCES.md URLs, or pass --sources DIR): 9 checks SKIPPED')

    def test_region_label_does_not_claim_pooled_values(self):
        lines, rc = verdicts(dict(total=3,passed=3,all_pass=True),dict(bytes_identical=0,files_compared=7),'/some/report.md',QUOTED_SKIP,region='eastern-wa')
        self.assertEqual(rc,0)
        self.assertEqual(lines[0],'HEADLINE (printed numbers for eastern-wa): PASS 3/3')

    def test_failed_or_skipped_computed_check_controls_exit(self):
        for extra in ({'failed':1,'unverified':0},{'failed':0,'unverified':1}):
            lines, rc = verdicts(dict(total=3,passed=2,all_pass=False,**extra),dict(bytes_identical=7,files_compared=7),'/some/report.md',QUOTED_SKIP)
            self.assertEqual(rc,1)
            self.assertEqual(lines[0],'HEADLINE (every printed number computed from the data): FAIL 1/3')

    def test_supplied_source_passes_and_failures_count_separately(self):
        for passed in (0,9):
            sources=dict(total=9,passed=passed,failed=9-passed,unverified=0,all_pass=passed==9)
            lines, rc=verdicts(dict(total=3,passed=3,all_pass=True),dict(bytes_identical=0,files_compared=7),'/some/report.md',sources)
            self.assertEqual(rc,0)
            self.assertIn(f'{passed} PASS; {9-passed} FAIL; 0 SKIPPED (9 checks)',lines[2])

    def test_empty_does_not_pass(self):
        self.assertEqual(verdicts(dict(total=0,passed=0,all_pass=False),dict(bytes_identical=0,files_compared=0),'/some/report.md',QUOTED_SKIP)[1],1)

    def test_printed_precision(self):
        self.assertEqual(printed_tolerance('21.71%'),0.005)
        self.assertEqual(printed_tolerance('52,721'),0.5)
        self.assertEqual(printed_tolerance('7.5%'),0.05)

    def test_all_shipped_region_cells_and_required_configuration_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for r in ('northern-ca','eastern-ok','maricopa-az','south-central-tx','eastern-wa'):
                with contextlib.redirect_stdout(io.StringIO()):
                    result = run_region(ROOT,ROOT,r,out/r)
                self.assertTrue(result['all_pass'],r)
                self.assertIn(f'{r}_drv_A_r25',build_plan(ROOT,r))
                self.assertIn(f'{r}_drvplus_A',build_plan(ROOT,r))

    def test_corrupt_last_configuration_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            s = Path(tmp); (s/'tables').mkdir()
            for tag in build_plan(ROOT,'eastern-wa'):
                shutil.copy2(ROOT/'tables'/f'{tag}_summary.csv',s/'tables'/f'{tag}_summary.csv')
            p = s/'tables'/'eastern-wa_drvplus_B_summary.csv'
            d = pd.read_csv(p); d.loc[d.scheme=='str','s300'] += 0.01; d.to_csv(p,index=False)
            with contextlib.redirect_stdout(io.StringIO()):
                result = run_region(ROOT,s,'eastern-wa',s/'out')
            self.assertFalse(result['all_pass'])
            self.assertGreater(result['failed'],0)

    def test_missing_outputs_and_command_failure_not_hidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            s = Path(tmp); (s/'tables').mkdir()
            with contextlib.redirect_stdout(io.StringIO()):
                missing = run_region(ROOT,s,'eastern-wa',s/'out')
                failed = run_region(ROOT,ROOT,'eastern-wa',s/'failed',command_rc=2)
            self.assertFalse(missing['all_pass'])
            self.assertFalse(failed['all_pass'])

    def test_guard_never_erases_source_or_unmarked_directory(self):
        with self.assertRaises(ValueError):
            guard_scratch(ROOT,ROOT,ROOT.parent)
        with self.assertRaises(ValueError):
            guard_scratch(ROOT.parent,ROOT,ROOT.parent)
        with tempfile.TemporaryDirectory() as tmp:
            s = Path(tmp)
            with self.assertRaises(ValueError):
                guard_scratch(s,ROOT,ROOT.parent)
            (s/'quick_preflight_source.json').write_text(json.dumps({'source':str(ROOT)}))
            self.assertEqual(guard_scratch(s,ROOT,ROOT.parent),s)


if __name__ == '__main__':
    unittest.main()
