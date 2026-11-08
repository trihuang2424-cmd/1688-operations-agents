"""Regression tests for stock warning decisions and evidence handling."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from normalize_stock_warning import NoCandidates, ReceiptError, normalize, normalize_row


def row(**overrides):
    result = {
        '商品ID': 826779734412, 'SKU ID': 5552498005668,
        '预警等级': '已断货', '可用库存(离线)': 0,
        '建议库存': 12, '库存缺口': 12,
        '实时可售库存': 9902893, '实时库存口径': '该SKU的可售库存',
    }
    result.update(overrides)
    return result


def receipt(rows):
    return {'success': True, 'data': {
        '库存预警列表': rows, '预警总数': 25, '页码': 2, '每页条数': 20,
    }}


class StockWarningTests(unittest.TestCase):
    def test_resolved_old_warning_preserves_offline_evidence(self):
        raw = row()
        original = copy.deepcopy(raw)
        result = normalize_row(raw)
        self.assertEqual(raw, original)
        self.assertEqual(result['离线预警等级'], '已断货')
        self.assertEqual(result['当前预警状态'], '已达建议库存')
        self.assertEqual(result['当前库存缺口'], 0)
        self.assertIs(result['列入当前库存风险'], False)

    def test_exact_threshold_is_sufficient(self):
        self.assertIs(normalize_row(row(实时可售库存=12))['列入当前库存风险'], False)

    def test_current_shortage_is_recalculated(self):
        result = normalize_row(row(实时可售库存=5))
        self.assertEqual(result['当前预警状态'], '低于建议库存')
        self.assertEqual(result['当前库存缺口'], 7)
        self.assertIs(result['列入当前库存风险'], True)

    def test_actual_zero_is_not_missing(self):
        result = normalize_row(row(实时可售库存=0))
        self.assertEqual(result['当前预警状态'], '当前可售为0')
        self.assertEqual(result['当前库存缺口'], 12)
        self.assertIs(result['列入当前库存风险'], True)

    def test_invalid_realtime_never_means_zero(self):
        for value in [None, '', ' ', False, True, 'abc', 'NaN', float('nan'), float('inf'), -1]:
            with self.subTest(value=value):
                result = normalize_row(row(实时可售库存=value))
                self.assertEqual(result['当前预警状态'], '待核验')
                self.assertIsNone(result['列入当前库存风险'])
                self.assertIsNone(result['当前库存缺口'])
        raw = row()
        del raw['实时可售库存']
        self.assertIsNone(normalize_row(raw)['列入当前库存风险'])

    def test_missing_recommendation_not_assumed_sufficient(self):
        for value in [None, '', False, -1, 'NaN']:
            with self.subTest(value=value):
                self.assertIsNone(normalize_row(row(建议库存=value))['列入当前库存风险'])

    def test_zero_without_recommendation_keeps_unknown_gap(self):
        result = normalize_row(row(实时可售库存=0, 建议库存=None))
        self.assertEqual(result['当前预警状态'], '当前可售为0')
        self.assertIsNone(result['当前库存缺口'])

    def test_product_scope_cannot_resolve_a_sku_warning(self):
        for scope in ['该商品的可售库存', None, '', '非SKU级库存']:
            with self.subTest(scope=scope):
                result = normalize_row(row(实时库存口径=scope))
                self.assertIsNone(result['列入当前库存风险'])

    def test_identity_is_required(self):
        for field in ['商品ID', 'SKU ID']:
            for value in [None, '', False, 0, -1]:
                with self.subTest(field=field, value=value):
                    self.assertIsNone(normalize_row(row(**{field: value}))['列入当前库存风险'])

    def test_numeric_strings_and_fractional_gap(self):
        result = normalize_row(row(实时可售库存='5.5', 建议库存='12'))
        self.assertEqual(result['当前库存缺口'], 6.5)

    def test_counts_are_recomputed_and_page_scoped(self):
        result = normalize(receipt([row(), row(**{'SKU ID': 5552498005669, '实时可售库存': 5}),
                                    row(**{'SKU ID': 5552498005667, '实时可售库存': None})]))
        self.assertEqual(result['离线预警总数'], 25)
        self.assertEqual(result['本页当前有效预警数'], 1)
        self.assertEqual(result['本页已解除预警数'], 1)
        self.assertEqual(result['本页待核验记录数'], 1)
        self.assertEqual(result['页码'], 2)

    def test_duplicate_or_conflicting_identity_is_rejected(self):
        for rows in [[row(), row()], [row(), row(实时可售库存=0)]]:
            with self.subTest(rows=rows), self.assertRaises(ReceiptError):
                normalize(receipt(rows))

    def test_error_codes_override_embedded_data(self):
        for code in ['INVALID_PARAM', 'PROVIDER_ERROR', 'INTERNAL_ERROR']:
            for field in ['code', 'errorCode']:
                with self.subTest(code=code, field=field), self.assertRaises(ReceiptError):
                    normalize({field: code, 'data': receipt([row()])['data']})

    def test_no_data_is_distinct_from_empty_success(self):
        for rows in [[], [row()]]:
            with self.subTest(rows=rows), self.assertRaises(NoCandidates):
                normalize({'code': 'NO_DATA', 'data': receipt(rows)['data']})

    def test_malformed_content_is_a_receipt_error(self):
        for content in [None, '', {}, 0]:
            with self.subTest(content=content), self.assertRaises(ReceiptError):
                normalize({'content': content})

    def test_wrapped_receipt_keeps_attribution_and_query_time(self):
        raw = {
            'queriedAt': '2026-10-26T02:54:57Z',
            'storeAttribution': {'shop': 'test-shop'},
            'result': {'content': [{'type': 'text', 'text': json.dumps(receipt([row()]))}]},
        }
        result = normalize(raw, 'receipt.json')
        self.assertEqual(result['storeAttribution'], raw['storeAttribution'])
        self.assertEqual(result['queriedAt'], raw['queriedAt'])
        self.assertEqual(result['证据文件'], 'receipt.json')

    def test_missing_time_is_not_fabricated(self):
        self.assertIsNone(normalize(receipt([row()]))['queriedAt'])

    def test_conflicting_attribution_is_rejected(self):
        raw = {'storeAttribution': {'shop': 'a'}, 'result': {
            'storeAttribution': {'shop': 'b'}, **receipt([row()]),
        }}
        with self.assertRaises(ReceiptError):
            normalize(raw)

    def test_failed_or_unrecognized_receipts_do_not_become_zero_warnings(self):
        for raw in [
            {'success': False, 'data': receipt([row()])['data']},
            {'isError': True, 'structuredContent': receipt([row()])},
            {'success': False, 'code': 'NO_DATA'},
            {'success': True, 'data': {}},
            {'库存预警列表': None},
        ]:
            with self.subTest(raw=raw), self.assertRaises(ReceiptError):
                normalize(raw)

    def test_explicit_empty_success_has_no_checked_rows(self):
        result = normalize(receipt([]))
        self.assertEqual(result['本页校验记录数'], 0)
        self.assertEqual(result['本页当前有效预警数'], 0)
        self.assertEqual(result['离线预警总数'], 25)

    def test_cli_preserves_raw_input_and_does_not_publish_failed_result(self):
        script = Path(__file__).with_name('normalize_stock_warning.py')
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / 'raw.json'
            raw.write_text(json.dumps(receipt([row()])))
            original = raw.read_bytes()
            output = Path(directory) / 'normalized.json'
            success = subprocess.run([sys.executable, str(script), str(raw), '--output', str(output)], capture_output=True)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertEqual(raw.read_bytes(), original)
            overwrite = subprocess.run([sys.executable, str(script), str(raw), '--output', str(raw)], capture_output=True)
            self.assertNotEqual(overwrite.returncode, 0)
            self.assertEqual(raw.read_bytes(), original)
            raw.write_text(json.dumps({'success': False}))
            failed_output = Path(directory) / 'failed.json'
            failure = subprocess.run([sys.executable, str(script), str(raw), '--output', str(failed_output)], capture_output=True)
            self.assertNotEqual(failure.returncode, 0)
            self.assertFalse(failed_output.exists())


if __name__ == '__main__':
    unittest.main()
