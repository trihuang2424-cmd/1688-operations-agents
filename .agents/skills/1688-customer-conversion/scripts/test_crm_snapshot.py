#!/usr/bin/env python3
"""Synthetic behavior tests; never contact a service or load account credentials."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from crm_snapshot import MAX_INPUT_BYTES, build_snapshot, render_html


def stats():
    return {"totalCount": 87, "site1688CustomerCount": 80,
            "wecomImportedCustomerCount": 7, "recent7dNewCount": 4}


def plan(identifier="p1", count=10):
    return {"planId": identifier, "planName": "合成策略", "planType": "system",
            "strategyCode": "inquiry_convert", "status": "not_started",
            "customerCnt": count, "pendingReachCnt": count, "reachedCnt": 0,
            "pendingReplyCnt": 0, "repliedCnt": 0, "orderedCnt": 0,
            "currentGroupList": [{"planId": identifier, "customerCnt": count, "ds": "2026-10-28"}]}


def payload():
    return {"storeAttribution": "合成测试店铺", "observedAt": "2026-10-28T12:00:00+08:00",
            "stats": stats(), "plans": [plan()]}


def warning_codes(snapshot):
    return {item["code"] for item in snapshot["warnings"]}


class SnapshotTests(unittest.TestCase):
    def test_multilayer_mcp_text_wrapper_and_string_array(self):
        data = payload()
        data["stats"] = {"isError": False, "content": [{"type": "text", "text": json.dumps(
            [{"type": "text", "text": json.dumps({"success": True, "data": stats()})}])}]}
        data["plans"] = {"content": [{"type": "text", "text": json.dumps(
            {"success": True, "data": json.dumps([plan(), plan("p2", 9)])})}]}
        result = build_snapshot(data)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["customerStats"]["totalCount"], 87)
        self.assertEqual(len(result["plans"]), 2)
        self.assertEqual(result["planCoverage"]["summedCustomerCnt"], 19)
        self.assertIsNone(result["planCoverage"]["uniqueCustomerCount"])

    def test_groups_never_count_as_plans_and_history_is_not_current(self):
        data = payload()
        data["plans"][0]["currentGroupList"].append({"planId": "p3", "planType": "system", "ds": "20261028"})
        data["plans"][0]["historyGroupList"] = [{"planId": "p4", "planType": "system", "ds": "2026-01-01"}]
        result = build_snapshot(data)
        self.assertEqual(result["planCoverage"]["listedPlanCount"], 1)
        self.assertEqual(result["plans"][0]["groupDates"], ["2026-10-28"])

    def test_duplicate_id_dedup_and_conflict_is_not_silent(self):
        data = payload()
        data["plans"] += [copy.deepcopy(data["plans"][0]), plan("p2", 8)]
        result = build_snapshot(data)
        self.assertEqual(len(result["plans"]), 2)
        self.assertIn("DUPLICATE_PLAN", warning_codes(result))
        self.assertEqual(result["planCoverage"]["summedCustomerCnt"], 18)
        data["plans"].append(plan("p1", 11))
        result = build_snapshot(data)
        self.assertIn("CONFLICTING_PLAN", warning_codes(result))
        self.assertIsNone(result["plans"][0]["customerCnt"])
        self.assertIsNone(result["planCoverage"]["summedCustomerCnt"])
        self.assertEqual(result["status"], "partial")

    def test_privacy_fields_and_raw_errors_are_never_copied(self):
        data = payload()
        secret = "PRIVATE_SENTINEL_DO_NOT_COPY"
        data["storeAttribution"] = {"label": "测试店铺", "loginId": secret, "auth": secret}
        data["stats"].update({"ownerLoginId": secret, "wikiCount": 91})
        data["plans"][0].update({"selectedLoginIds": [secret], "buyerInfoList": [{"phone": secret}],
                                  "contact": secret, "auth": {"token": secret}, "user_config": secret})
        data["plans"][0]["currentGroupList"][0]["buyerLoginIds"] = [secret]
        result = build_snapshot(data)
        serialized = json.dumps(result)
        self.assertNotIn(secret, serialized)
        self.assertNotIn("wikiCount", serialized)
        self.assertNotIn("selectedLoginIds", serialized)
        data["plans"] = {"success": False, "message": secret, "error": {"cookie": secret}}
        result = build_snapshot(data)
        self.assertNotIn(secret, json.dumps(result))
        self.assertNotIn(secret, render_html(result))

    def test_null_missing_metrics_and_actual_zero_are_distinct(self):
        data = payload()
        del data["stats"]["totalCount"]
        data["stats"]["recent7dNewCount"] = None
        del data["plans"][0]["reachedCnt"]
        result = build_snapshot(data)
        self.assertIsNone(result["customerStats"]["totalCount"])
        self.assertIsNone(result["customerStats"]["recent7dNewCount"])
        self.assertIsNone(result["plans"][0]["reachedCnt"])
        self.assertEqual(result["plans"][0]["orderedCnt"], 0)
        self.assertIn("MISSING_METRIC", warning_codes(result))

    def test_bad_numeric_values_do_not_become_counts(self):
        data = payload()
        data["stats"].update({"totalCount": True, "site1688CustomerCount": -1,
                              "wecomImportedCustomerCount": 1.2, "recent7dNewCount": "4"})
        result = build_snapshot(data)
        self.assertIsNone(result["customerStats"]["totalCount"])
        self.assertIsNone(result["customerStats"]["site1688CustomerCount"])
        self.assertIsNone(result["customerStats"]["wecomImportedCustomerCount"])
        self.assertEqual(result["customerStats"]["recent7dNewCount"], 4)

    def test_failed_source_suppresses_incidental_data_and_html_success(self):
        for marker in ({"success": False}, {"isError": True}, {"code": 500}, {"errorCode": "ERROR"}):
            with self.subTest(marker=marker):
                data = payload()
                data["stats"] = dict(marker, data=stats())
                data["plans"] = dict(marker, data=[plan()])
                result = build_snapshot(data)
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["plans"], [])
                self.assertTrue(all(v is None for v in result["customerStats"].values()))
                page = render_html(result)
                self.assertIn("不能视为查询成功", page)
                self.assertNotIn("已解析快照", page)

    def test_unknown_schema_or_empty_transport_is_not_business_success(self):
        for raw in ({"success": True}, {"isError": False, "content": []}, {"data": {"newSchema": 123}}):
            with self.subTest(raw=raw):
                data = payload()
                data["plans"] = raw
                result = build_snapshot(data)
                self.assertEqual(result["sources"]["plans"]["status"], "unknown")
                self.assertIsNone(result["planCoverage"]["listedPlanCount"])
                self.assertIn("UNRECOGNIZED_RESPONSE", warning_codes(result))

    def test_explicit_empty_plan_list_is_valid_but_no_unique_coverage_claim(self):
        data = payload()
        data["plans"] = {"data": {"plans": []}}
        result = build_snapshot(data)
        self.assertEqual(result["sources"]["plans"]["status"], "available")
        self.assertEqual(result["planCoverage"]["listedPlanCount"], 0)
        self.assertEqual(result["planCoverage"]["summedCustomerCnt"], 0)
        self.assertIsNone(result["planCoverage"]["uniqueCustomerCount"])

    def test_explicit_list_keeps_missing_type_with_warning(self):
        data = payload()
        del data["plans"][0]["planType"]
        result = build_snapshot(data)
        self.assertEqual(len(result["plans"]), 1)
        self.assertIsNone(result["plans"][0]["planType"])
        self.assertIn("PLAN_TYPE_MISSING", warning_codes(result))

    def test_arbitrary_nested_customer_records_are_not_scanned(self):
        data = payload()
        data["plans"] = {"buyerInfoList": [plan()], "currentGroupList": [plan()]}
        result = build_snapshot(data)
        self.assertEqual(result["plans"], [])
        self.assertEqual(result["sources"]["plans"]["status"], "unknown")

    def test_conflicting_stats_and_unknown_status(self):
        data = payload()
        data["stats"] = [stats(), dict(stats(), totalCount=88)]
        data["plans"][0]["status"] = "new-status"
        result = build_snapshot(data)
        self.assertIsNone(result["customerStats"]["totalCount"])
        self.assertIn("CONFLICTING_STATS", warning_codes(result))
        self.assertIn("UNKNOWN_STATUS", warning_codes(result))

    def test_timezone_required_and_input_not_mutated(self):
        data = payload()
        data["observedAt"] = "2026-10-28T12:00:00"
        original = copy.deepcopy(data)
        result = build_snapshot(data)
        self.assertIsNone(result["observedAt"])
        self.assertIn("OBSERVED_AT_INVALID", warning_codes(result))
        self.assertEqual(data, original)
        data["observedAt"] = "2020-01-02T03:04:05Z"
        self.assertEqual(build_snapshot(data)["observedAt"], "2020-01-02T03:04:05+00:00")

    def test_html_escapes_all_dynamic_text_and_has_no_actions(self):
        data = payload()
        attack = '<script>alert("x")</script><img src=x onerror="alert(1)">'
        data["storeAttribution"] = attack
        data["plans"][0]["planName"] = attack
        result = build_snapshot(data)
        page = render_html(result)
        self.assertNotIn(attack, page)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script", page.lower())
        self.assertNotIn("<button", page.lower())
        self.assertNotIn("<form", page.lower())
        self.assertNotIn('src="http', page.lower())
        self.assertIn("不会自动刷新", page)

    def test_parse_depth_limit_is_reported(self):
        data = payload()
        wrapped = stats()
        for _ in range(30):
            wrapped = {"data": wrapped}
        data["stats"] = wrapped
        result = build_snapshot(data)
        self.assertIn("LIMIT_EXCEEDED", warning_codes(result))
        self.assertEqual(result["sources"]["stats"]["status"], "unknown")

    def test_visibility_scope_defaults_to_unknown_without_claiming_all_store(self):
        result = build_snapshot(payload())
        self.assertEqual(result["visibilityScope"], "unknown")
        self.assertEqual(result["status"], "complete")
        page = render_html(result)
        self.assertIn("当前授权可见客户", page)
        self.assertIn("主/子账号可见范围未核验，不据此断言全店", page)
        self.assertNotIn("全部客户", page)

    def test_visibility_scope_known_enums_and_invalid_values(self):
        for scope, label in (("all_store", "全店客户范围（调用方已提供主账号全店可见依据）"),
                             ("assigned", "当前账号名下客户范围，不代表全店客户")):
            with self.subTest(scope=scope):
                data = payload()
                data["visibilityScope"] = scope
                result = build_snapshot(data)
                self.assertEqual(result["visibilityScope"], scope)
                self.assertIn(label, render_html(result))
                self.assertNotIn("主/子账号可见范围未核验", render_html(result))
        for invalid in ("PRIVATE_SCOPE_SECRET", {"token": "PRIVATE_SCOPE_SECRET"}, None, []):
            with self.subTest(invalid=invalid):
                data = payload()
                data["visibilityScope"] = invalid
                result = build_snapshot(data)
                self.assertEqual(result["visibilityScope"], "unknown")
                self.assertIn("INVALID_VISIBILITY_SCOPE", warning_codes(result))
                self.assertNotIn("PRIVATE_SCOPE_SECRET", json.dumps(result))
                self.assertNotIn("PRIVATE_SCOPE_SECRET", render_html(result))


class CliTests(unittest.TestCase):
    script = str(Path(__file__).with_name("crm_snapshot.py"))

    def call(self, args=(), raw=None):
        return subprocess.run([sys.executable, self.script] + list(args),
                              input=json.dumps(payload()) if raw is None else raw,
                              text=True, capture_output=True, check=False)

    def test_stdin_and_file_outputs_no_overwrite_and_path_conflict(self):
        result = self.call()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["customerStats"]["totalCount"], 87)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            out = Path(directory) / "summary.json"
            page = Path(directory) / "summary.html"
            source.write_text(json.dumps(payload()), encoding="utf-8")
            args = ["--input", str(source), "--json-out", str(out), "--html-out", str(page)]
            self.assertEqual(self.call(args).returncode, 0)
            self.assertTrue(page.read_text(encoding="utf-8").startswith("<!doctype html>"))
            result = self.call(args)
            self.assertEqual(result.returncode, 2)
            self.assertIn("OUTPUT_EXISTS", warning_codes(json.loads(result.stdout)))
            self.assertEqual(self.call(args + ["--overwrite"]).returncode, 0)
            result = self.call(["--input", str(source), "--json-out", str(source), "--overwrite"])
            self.assertEqual(result.returncode, 2)
            self.assertIn("PATH_CONFLICT", warning_codes(json.loads(result.stdout)))
            self.assertEqual(json.loads(source.read_text(encoding="utf-8")), payload())

    def test_invalid_and_oversized_input_fail_without_echoing_input(self):
        for raw, expected in (("SECRET not json", "INVALID_INPUT"), ("x" * (MAX_INPUT_BYTES + 1), "INPUT_TOO_LARGE")):
            with self.subTest(expected=expected):
                result = self.call(raw=raw)
                self.assertEqual(result.returncode, 2)
                self.assertIn(expected, warning_codes(json.loads(result.stdout)))
                self.assertNotIn("SECRET", result.stdout)


if __name__ == "__main__":
    unittest.main()
