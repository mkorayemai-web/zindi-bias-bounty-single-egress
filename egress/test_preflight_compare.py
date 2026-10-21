"""Regression tests: python -m unittest discover -s egress -p 'test_preflight_compare.py'."""
import tempfile
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from preflight_compare import array_result, compare_file


class ValueComparisonTests(unittest.TestCase):
    def test_float_tolerance(self):
        self.assertTrue(array_result('weighted_load', [1.0], [1.0 + 5e-10])['ok'])
        self.assertFalse(array_result('weighted_load', [1.0], [1.0 + 2e-9])['ok'])
        self.assertTrue(array_result('distance', [0.0], [5e-13])['ok'])
        self.assertFalse(array_result('distance', [0.0], [2e-12])['ok'])

    def test_integer_and_float_stored_counts_exact(self):
        self.assertFalse(array_result('count', [10**12], [10**12 + 1])['ok'])
        self.assertFalse(array_result('top_str', [1e12], [1e12 + 1])['ok'])
        self.assertFalse(array_result('load_struct', [1e12], [1e12 + 1])['ok'])
        self.assertFalse(array_result('structure_den_exact', [1e12], [1e12 + 1])['ok'])

    def test_missing_nonfinite_and_schema(self):
        self.assertTrue(array_result('x', [np.nan, np.inf], [np.nan, np.inf])['ok'])
        self.assertFalse(array_result('x', [np.nan], [1.0])['ok'])
        self.assertFalse(array_result('x', [np.inf], [-np.inf])['ok'])
        self.assertFalse(array_result('x', np.array([1.0], dtype='f4'), np.array([1.0], dtype='f8'))['ok'])
        self.assertFalse(array_result('x', [1.0], [1.0, 2.0])['ok'])

    def test_bytes_informational_and_missing_identifiers_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a.csv', Path(tmp) / 'b.csv'
            a.write_text('tract,value\n06067005803,1.0\n')
            b.write_text('tract,value\n06067005803,1.0000000001\n')
            r = compare_file(a, b)
            self.assertFalse(r['bytes_equal'])
            self.assertTrue(r['values_equal'])
            b.write_text('tract,value\n,1.0\n')
            self.assertFalse(compare_file(a, b)['values_equal'])

    def test_parquet_index_and_npz_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a.parquet', Path(tmp) / 'b.parquet'
            pd.DataFrame({'x': [1.0]}, index=['a']).to_parquet(a)
            pd.DataFrame({'x': [1.0]}, index=['b']).to_parquet(b)
            self.assertFalse(compare_file(a, b)['values_equal'])
            a, b = Path(tmp) / 'a.npz', Path(tmp) / 'b.npz'
            np.savez(a, top_str=np.array([0.0], dtype='f4'))
            np.savez(b, top_str=np.array([1.0], dtype='f4'))
            self.assertFalse(compare_file(a, b)['values_equal'])


if __name__ == '__main__':
    unittest.main()
