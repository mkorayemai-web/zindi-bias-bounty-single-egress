"""The new 193/9 inventory figures are coverage metadata, not measured rows."""
from pathlib import Path
import unittest
import pandas as pd
from ledger_metadata import coverage_metadata, platform_identifier_spans

ROOT=Path(__file__).resolve().parent.parent
SENTENCE='Second platform: rebuilt from empty work folders on Linux aarch64, all 193 offline ledger checks of printed numbers pass at their printed precision (the other 9 quote external documents); x86 untested.'


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.ids=list(pd.read_csv(ROOT/'tables/numbers_ledger.csv').id)

    def test_counts_are_metadata_not_new_measured_rows(self):
        before=list(self.ids)
        rows=coverage_metadata(SENTENCE,self.ids)
        self.assertEqual([r['token'] for r in rows],['193','9'])
        self.assertEqual([r['registered_count'] for r in rows],[193,9])
        self.assertTrue(all(r['matches'] and 'not a measured value' in r['kind'] for r in rows))
        self.assertEqual(self.ids,before)
        for r in rows: self.assertEqual(SENTENCE[r['start']:r['end']],r['token'])

    def test_wrong_inventory_count_is_detected(self):
        rows=coverage_metadata(SENTENCE.replace('all 193','all 194'),self.ids)
        self.assertFalse(rows[0]['matches'])
        self.assertTrue(rows[1]['matches'])

    def test_platform_digits_are_identifier_metadata(self):
        spans=platform_identifier_spans(SENTENCE)
        self.assertEqual([SENTENCE[a:b] for a,b in spans],['64','86'])
        self.assertEqual(platform_identifier_spans('64 dwellings and 86 people'),[])

    def test_unrelated_measurement_is_not_reclassified(self):
        self.assertEqual(coverage_metadata('There are 193 dwellings and 9 people.',self.ids),[])


if __name__=='__main__': unittest.main()
