"""Tests for printed-number audit accounting and informational raster diffs."""
from pathlib import Path
import tempfile
import unittest

import pandas as pd
from PIL import Image

from finding_audit import pixel_diff, required_tables, tally


class FindingAuditTests(unittest.TestCase):
    def test_skipped_is_not_passed(self):
        r = tally(pd.DataFrame({'status': ['OK', 'SKIPPED-NO-SOURCE', 'MISMATCH']}))
        self.assertEqual((r['passed'], r['unverified'], r['failed'], r['total']), (1, 1, 1, 3))
        self.assertFalse(r['all_pass'])

    def test_all_ok_pass(self):
        self.assertTrue(tally(pd.DataFrame({'status': ['OK', 'OK']}))['all_pass'])

    def test_one_changed_pixel(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a.png', Path(d)/'b.png'
            im = Image.new('RGBA', (2, 2), 'white'); im.save(a)
            im.putpixel((0, 0), (0, 0, 0, 255)); im.save(b)
            self.assertEqual(pixel_diff(a,b)['different_pixels'], 1)

    def test_size_mismatch_not_identical(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a.png', Path(d)/'b.png'
            Image.new('RGBA', (1, 1), (0,0,0,0)).save(a)
            Image.new('RGBA', (2, 1), (0,0,0,0)).save(b)
            self.assertEqual(pixel_diff(a,b)['different_pixels'], 1)

    def test_dependency_inventory(self):
        got = required_tables('a = T("one.csv"); b = T("two.csv", dtype=str)')
        self.assertIn('tables/one.csv', got)
        self.assertIn('tables/two.csv', got)
        self.assertIn('tables/validation_hays_summary.txt', got)


if __name__ == '__main__':
    unittest.main()
