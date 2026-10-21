"""Quoted-source policy tests. Document strings below are SYNTHETIC fixtures,
not downloaded documents or production evidence. All temporary files are removed.
"""
from pathlib import Path
import tempfile
import unittest
import pandas as pd

from quoted_sources import CHECKS, SOURCE_IDS, evaluate_sources, split_ledger, summarize

ROOT=Path(__file__).resolve().parent.parent
DRAFT=(ROOT/'DISCOVERY_DRAFT.md').read_text()
FIXTURES={
    'mammoth_eagle_lodge_deir_s3-8.txt': 'SYNTHETIC UNIT TEST FIXTURE. person/unit occupancy of 4.0 was applied to all remaining visitor, second home. occupied about 25.7 weeks on average, or 49% of the year. average peak PAOT in 2004 was 34,265. approximately 7,259 people were residents. Draft Environmental Impact Report September 2006.',
    'collier_lee_hes1987.htm': '<p>SYNTHETIC UNIT TEST FIXTURE. 1987 Condominium (Conventional) 51.0 64.0 Mobile Home 43.0 75.0</p>',
    'nist_tn2252.txt': 'SYNTHETIC UNIT TEST FIXTURE. Camp Fire 2018. In Paradise, the OHU/Egress Lane ratio is 927.',
}


class QuotedSourcesTests(unittest.TestCase):
    def test_missing_stays_skipped_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            rows=evaluate_sources(DRAFT,ROOT/'ext',Path(d))
            self.assertEqual({r['status'] for r in rows},{'SKIPPED-NO-SOURCE'})
            self.assertEqual(summarize(rows),dict(total=9,passed=0,failed=0,unverified=9,all_pass=False))

    def test_supplied_flat_documents_actually_run_and_count(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for name,text in FIXTURES.items(): (p/name).write_text(text)
            rows=evaluate_sources(DRAFT,ROOT/'ext',p)
            self.assertEqual(summarize(rows),dict(total=9,passed=9,failed=0,unverified=0,all_pass=True))
            (p/'nist_tn2252.txt').write_text('SYNTHETIC WRONG TEXT, no expected quotation')
            changed=evaluate_sources(DRAFT,ROOT/'ext',p)
            self.assertEqual(summarize(changed)['failed'],2)
            self.assertEqual({r['id'] for r in changed if r['status']=='MISMATCH'},{'I.04','P.12'})

    def test_nested_layout_partial_sources_and_text_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'q_sources').mkdir()
            (p/'q_sources/mammoth_eagle_lodge_deir_s3-8.txt').write_text(FIXTURES['mammoth_eagle_lodge_deir_s3-8.txt'])
            rows=evaluate_sources(DRAFT,ROOT/'ext',p)
            self.assertEqual((summarize(rows)['passed'],summarize(rows)['unverified']),(5,4))
            wrong=evaluate_sources(DRAFT.replace('34,265 persons','34,266 persons'),ROOT/'ext',p)
            self.assertEqual(next(r['status'] for r in wrong if r['id']=='Q.03'),'DRAFT-TEXT-MISSING')

    def test_partition_is_by_explicit_id_not_skip_or_q_prefix(self):
        rows=[dict(id=cid,status='SKIPPED-NO-SOURCE') for cid in sorted(SOURCE_IDS)]
        rows += [dict(id='Q.06',status='OK'),dict(id='F1.06',status='MISMATCH'),dict(id='COMPUTED.MISSING',status='SKIPPED-NO-SOURCE')]
        computed,quoted=split_ledger(pd.DataFrame(rows))
        self.assertEqual(set(quoted.id),SOURCE_IDS)
        self.assertEqual(set(computed.id),{'Q.06','F1.06','COMPUTED.MISSING'})
        self.assertFalse(summarize(computed.to_dict('records'))['all_pass'])
        self.assertEqual(summarize(quoted.to_dict('records'))['passed'],0)

    def test_missing_or_duplicate_source_id_cannot_disappear(self):
        rows=[dict(id=cid,status='OK') for cid in SOURCE_IDS]
        for bad in (rows[:-1],rows+[rows[0]]):
            with self.assertRaises(ValueError): split_ledger(pd.DataFrame(bad))


if __name__=='__main__': unittest.main()
