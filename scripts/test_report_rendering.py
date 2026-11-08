"""Offline report contract tests. All example metrics are explicitly simulated."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from render_operating_report import ASSETS, ReportError, main, render_report


def simulated_report():
    return {
        "schema_version": 1, "data_mode": "simulation", "report_type": "daily",
        "period_basis": "single_day_t_plus_1", "title": "模拟日报",
        "period": {"start": "2026-10-27", "end": "2026-10-27", "timezone": "Asia/Shanghai"},
        "data_cutoff": "2026-10-27T23:59:00+08:00",
        "retrieved_at": "2026-10-28T09:00:00+08:00",
        "storeAttribution": {"store_ref": "simulation-store", "display_name": "模拟店铺"},
        "strategy_version": None, "coverage": {"status": "partial", "notes": ["仅测试缺失值与零值"]},
        "metrics": [{"name": "模拟订单", "value": 0, "unit": "笔", "source": "模拟输入", "evidence": "simulation.json", "basis": "模拟单日", "denominator": "不适用", "missing_reason": None}],
        "findings": [], "actions": [], "unfinished": [],
    }


class RenderingTests(unittest.TestCase):
    def test_templates_and_remaining_placeholders_cannot_render(self):
        for filename in ("daily-input.json", "weekly-input.json", "monthly-input.json"):
            with self.subTest(filename=filename):
                data = json.loads((ASSETS / filename).read_text(encoding="utf-8"))
                with self.assertRaises(ReportError):
                    render_report(data, allow_simulation=True)
                data["data_mode"] = "actual"
                with self.assertRaises(ReportError):
                    render_report(data)

    def test_simulation_requires_flag_and_is_visible(self):
        with self.assertRaises(ReportError):
            render_report(simulated_report())
        result = render_report(simulated_report(), True)
        self.assertIn("模拟数据，不代表店铺实绩", result)

    def test_zero_and_missing_are_distinct(self):
        data = simulated_report()
        missing = deepcopy(data["metrics"][0])
        missing.update(name="模拟访客", value=None, missing_reason="模拟查询未返回")
        data["metrics"].append(missing)
        result = render_report(data, True)
        self.assertIn('<span class="value">0</span>', result)
        self.assertIn('<span class="missing">缺失</span>', result)
        self.assertIn("模拟查询未返回", result)

    def test_stale_data_requires_explicit_incomplete_coverage(self):
        data = simulated_report()
        data["data_cutoff"] = "2026-10-25T23:59:00+08:00"
        data["coverage"] = {"status": "partial", "notes": ["数据延迟，仅更新到10月25日；所选区间尚不完整"]}
        result = render_report(data, True)
        self.assertIn("2026-10-25T23:59:00+08:00", result)
        self.assertIn("数据延迟", result)
        data["coverage"]["status"] = "complete"
        with self.assertRaises(ReportError):
            render_report(data, True)

    def test_day_and_week_periods_cannot_be_mixed(self):
        data = simulated_report()
        data["period"]["start"] = "2026-10-21"
        with self.assertRaises(ReportError):
            render_report(data, True)
        data.update(report_type="weekly", period_basis="independent_period")
        self.assertIn("2026-10-21 至 2026-10-27", render_report(data, True))
        data["period_basis"] = "single_day_t_plus_1"
        with self.assertRaises(ReportError):
            render_report(data, True)

    def test_daily_t_plus_one_uses_declared_timezone(self):
        data = simulated_report()
        data["retrieved_at"] = "2026-10-27T15:59:00Z"
        with self.assertRaises(ReportError):
            render_report(data, True)
        data["retrieved_at"] = "2026-10-27T16:00:00Z"
        self.assertIn("单日 T+1 日报", render_report(data, True))

    def test_monthly_accepts_real_calendar_month_lengths(self):
        for start, end, retrieved in (
            ("2024-02-01", "2024-02-29", "2024-03-01T09:00:00+08:00"),
            ("2025-02-01", "2025-02-28", "2025-03-01T09:00:00+08:00"),
            ("2026-04-01", "2026-04-30", "2026-05-01T09:00:00+08:00"),
            ("2025-12-01", "2025-12-31", "2026-01-01T09:00:00+08:00"),
        ):
            with self.subTest(start=start):
                data = simulated_report()
                data.update(report_type="monthly", period_basis="complete_calendar_month",
                            data_cutoff=end + "T23:59:00+08:00", retrieved_at=retrieved)
                data["period"].update(start=start, end=end)
                data["coverage"] = {"status": "complete", "notes": []}
                result = render_report(data, True)
                self.assertIn(f"{start} 至 {end}", result)
                self.assertIn("完整自然月月报", result)

    def test_monthly_rejects_partial_rolling_and_cross_month_periods(self):
        for start, end in (
            ("2024-02-01", "2024-02-28"),
            ("2025-02-02", "2025-02-28"),
            ("2026-04-01", "2026-04-29"),
            ("2026-03-15", "2026-04-13"),
            ("2025-12-01", "2026-01-31"),
        ):
            with self.subTest(start=start, end=end):
                data = simulated_report()
                data.update(report_type="monthly", period_basis="complete_calendar_month")
                data["period"].update(start=start, end=end)
                with self.assertRaises(ReportError):
                    render_report(data, True)

    def test_monthly_requires_completed_month_in_shanghai_even_with_missing_data(self):
        data = simulated_report()
        data.update(report_type="monthly", period_basis="complete_calendar_month",
                    data_cutoff="2024-02-28T23:59:00+08:00",
                    retrieved_at="2024-02-29T15:59:59Z")
        data["period"].update(start="2024-02-01", end="2024-02-29")
        with self.assertRaises(ReportError):
            render_report(data, True)
        data["retrieved_at"] = "2024-02-29T16:00:00Z"
        self.assertIn("2024-02-01 至 2024-02-29", render_report(data, True))
        data["period"]["timezone"] = "UTC"
        with self.assertRaises(ReportError):
            render_report(data, True)

    def test_monthly_retains_unknown_metrics_and_requires_honest_coverage(self):
        data = simulated_report()
        data.update(report_type="monthly", period_basis="complete_calendar_month",
                    data_cutoff="2026-09-29T23:59:00+08:00",
                    retrieved_at="2026-10-01T09:00:00+08:00")
        data["period"].update(start="2026-09-01", end="2026-09-30")
        data["coverage"] = {"status": "partial", "notes": ["月末数据尚未回补"]}
        data["metrics"][0].update(name="月销售额变化幅度", value=None,
                                   missing_reason="对比期销售额未知，无法计算变化幅度")
        result = render_report(data, True)
        self.assertIn('<span class="missing">缺失</span>', result)
        self.assertIn("对比期销售额未知，无法计算变化幅度", result)
        self.assertIn("2026-09-29T23:59:00+08:00", result)
        data["coverage"]["status"] = "complete"
        with self.assertRaises(ReportError):
            render_report(data, True)

    def test_monthly_basis_cannot_be_presented_as_daily_or_weekly(self):
        data = simulated_report()
        data.update(period_basis="complete_calendar_month")
        with self.assertRaises(ReportError):
            render_report(data, True)
        data["report_type"] = "weekly"
        data["period"]["start"] = "2026-10-21"
        with self.assertRaises(ReportError):
            render_report(data, True)
        data["report_type"] = "monthly"
        data["period_basis"] = "independent_period"
        with self.assertRaises(ReportError):
            render_report(data, True)

    def test_data_cutoff_and_retrieval_are_distinct(self):
        data = simulated_report()
        result = render_report(data, True)
        self.assertIn("数据实际截止：2026-10-27T23:59:00+08:00", result)
        self.assertIn("取数时间：2026-10-28T09:00:00+08:00", result)
        data["data_cutoff"] = "2026-10-28T10:00:00+08:00"
        with self.assertRaises(ReportError):
            render_report(data, True)

    def test_markup_and_unsafe_links_cannot_execute(self):
        data = simulated_report()
        data["title"] = '<script>alert("source")</script>'
        data["findings"] = [{"kind": "fact", "text": '<img src=x onerror="alert(1)">', "evidence": "javascript:alert(1)"}]
        data["metrics"][0]["evidence"] = "https://example.invalid/evidence?a=1&b=2"
        result = render_report(data, True)
        self.assertNotIn("<script>", result)
        self.assertNotIn("<img ", result)
        self.assertNotIn('href="javascript:', result)
        self.assertIn("&lt;script&gt;", result)
        self.assertIn('href="https://example.invalid/evidence?a=1&amp;b=2"', result)

    def test_invalid_numbers_and_missing_reasons_fail(self):
        for value in (float("nan"), float("inf"), True, {"value": 3}, "42", None):
            with self.subTest(value=value):
                data = simulated_report()
                data["metrics"][0]["value"] = value
                with self.assertRaises(ReportError):
                    render_report(data, True)

    def test_cli_preserves_input_and_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "simulation.json"
            output = Path(directory) / "simulation.html"
            original = json.dumps(simulated_report(), ensure_ascii=False)
            source.write_text(original, encoding="utf-8")
            arguments = ["--input", str(source), "--output", str(output), "--allow-simulation"]
            main(arguments)
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            output.write_text("existing", encoding="utf-8")
            with self.assertRaises(SystemExit):
                main(arguments)
            self.assertEqual(output.read_text(encoding="utf-8"), "existing")


if __name__ == "__main__":
    unittest.main()
