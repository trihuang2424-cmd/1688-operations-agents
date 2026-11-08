#!/usr/bin/env python3
"""Offline regression checks for real routing-stage differences and fail-closed reads."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from task_context import (ROOT, ContextError, build_context, load_catalog,
                          markdown_section, read_reference, validate_loading_contract)


def rule(name):
    return f"references/business-rules/1688-{name}/RULES.md"


class TaskContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(ROOT)

    def context(self, route, phase, role="executor", *conditions, deliverable=None):
        return build_context(ROOT, route, phase, role, conditions, self.catalog, deliverable)

    def test_entire_catalog_and_all_stage_roles_resolve(self):
        self.assertEqual(validate_loading_contract(ROOT, self.catalog), [])
        self.assertEqual(self.catalog["version"], "2.4.0")
        self.assertEqual(len(self.catalog["routes"]), 24)
        for route in self.catalog["routes"]:
            for phase, stage in route["phase_loading"].items():
                conditions = [group[0] for group in stage["required_any_conditions"]]
                for role in ("director", "executor"):
                    with self.subTest(route=route["id"], phase=phase, role=role):
                        result = self.context(route["id"], phase, role, *conditions)
                        self.assertTrue(result["read"])
                        self.assertEqual(len(result["read"]), len(set(result["read"])))

    def test_director_routes_without_preloading_domain_rules(self):
        for route in ("title_optimization", "product_change", "product_images", "traffic_and_ads", "conversion_analysis"):
            with self.subTest(route=route):
                result = self.context(route, "plan", "director")
                self.assertEqual(result["rules"], [])
                self.assertFalse(any("/business-rules/" in ref or ref.startswith("source/") for ref in result["read"]))
                self.assertFalse(any(ref.endswith("SKILL.md") for ref in result["read"]))

    def test_acquisition_policy_is_loaded_for_analysis_but_not_local_recovery(self):
        shared = "references/acquisition-analysis.md"
        for route, phase in (("daily_metrics", "execute"), ("period_analysis", "evaluate"),
                             ("weekly_review", "plan"), ("monthly_review", "evaluate"),
                             ("traffic_and_ads", "monitor")):
            with self.subTest(route=route, phase=phase):
                result = self.context(route, phase)
                self.assertIn(shared, result["read"])
                self.assertIn("acquisition_analysis", result["active_conditions"])
                self.assertTrue(result["completion_contract"]["declared"])
                self.assertTrue(result["completion_contract"]["requirements"])
        for route, phase in (("daily_operations", "monitor"),
                             ("conversion_monitoring", "monitor"), ("product_change", "receipt")):
            with self.subTest(local_route=route, phase=phase):
                local = self.context(route, phase)
                self.assertFalse(any(ref.startswith(shared) for ref in local["read"]))
                self.assertEqual(local["rules"], [])
        for selected in ("inquiry", "crm"):
            queried = self.context("conversion_monitoring", "monitor", "executor", selected)
            self.assertIn(shared + "#客户身份与成交来源", queried["read"])
            self.assertIn(shared + "#指标与队列", queried["read"])

    def test_free_query_ads_loads_acquisition_without_starting_content_work(self):
        result = self.context("product_diagnosis", "execute", "executor", "free_query", "ads",
                              deliverable="evidence")
        self.assertIn("references/acquisition-analysis.md", result["read"])
        self.assertIn("source/plugins/1688-seller-assistant/skills/1688-shop-freedom-query-data/SKILL.md",
                      result["read"])
        self.assertNotIn("images", result["active_conditions"])
        self.assertNotIn("apply_images", result["active_conditions"])
        self.assertTrue(all(h["activation_status"] == "candidate_only" and not h["automatic_execution"]
                            for h in result["conditional_handoffs"]))

    def test_monitor_and_evaluation_have_decisions_without_granting_execution(self):
        for phase in ("monitor", "evaluate"):
            with self.subTest(phase=phase):
                evidence = self.context("traffic_and_ads", phase, deliverable="evidence")
                plan = self.context("traffic_and_ads", phase, deliverable="plan")
                self.assertTrue(evidence["completion_contract"]["declared"])
                self.assertTrue(plan["completion_contract"]["declared"])
                self.assertTrue(all(h["activation_status"] == "candidate_only"
                                    for h in evidence["conditional_handoffs"]))
                self.assertTrue(all(h["authorization"] == "inherit_only" and not h["automatic_execution"]
                                    for h in plan["conditional_handoffs"]))
                self.assertNotIn("apply_images", plan["active_conditions"])
                with self.assertRaisesRegex(ContextError, "not declared"):
                    self.context("traffic_and_ads", phase, deliverable="execution")

    def test_title_and_detail_handoffs_resolve_to_real_assets_then_application(self):
        plan = self.context("traffic_and_ads", "monitor", deliverable="plan")
        handoffs = {h["id"]: h for h in plan["conditional_handoffs"]}
        for name in ("prepare_title_asset", "prepare_detail_asset"):
            with self.subTest(handoff=name):
                h = handoffs[name]
                self.assertEqual(h["target_deliverable"], "asset")
                self.assertEqual(h["required_scope"], ["asset_preparation"])
                asset = self.context(h["target_route"], h["target_phase"], deliverable="asset")
                self.assertTrue(asset["completion_contract"]["declared"])
                application = next(item for item in asset["conditional_handoffs"]
                                   if item["id"] == "apply_approved_copy")
                self.assertEqual(application["target_route"], "product_change")
                self.assertEqual(application["target_phase"], "execute")
                self.assertEqual(application["target_deliverable"], "execution")
                self.assertIn("approved_version", application["required_scope"])
                self.assertIn("product_write", application["required_scope"])
                self.assertEqual(application["activation_status"], "pending_scope_check")
                self.assertFalse(application["automatic_execution"])
        applied = self.context("product_change", "execute", deliverable="execution")
        self.assertIn("references/execution-protocol.md", applied["read"])
        self.assertIn("references/sales-growth-workflow.md#成品审核与应用", applied["read"])
        self.assertNotIn("apply_images", applied["active_conditions"])

    def test_title_plan_and_execution_are_different_full_rule_sets(self):
        plan = self.context("title_optimization", "plan")
        execution = self.context("title_optimization", "execute")
        self.assertEqual(plan["rules"], [rule("title-optimizer")])
        self.assertNotIn(rule("product-editor"), plan["read"])
        self.assertNotIn("references/execution-protocol.md", plan["read"])
        self.assertIn(rule("product-editor"), execution["read"])
        self.assertIn("references/execution-protocol.md", execution["read"])
        self.assertIn("references/runtime.md#商品编辑字段边界", execution["read"])
        for name in ("optimize_title", "optimize_title_llm"):
            self.assertIn("source/plugins/1688-seller-assistant/skills/1688-item-title-optimizer/capabilities/" + name + ".md", plan["read"])

    def test_local_daily_monitor_does_not_load_old_director_or_customer_write_rules(self):
        result = self.context("daily_operations", "monitor")
        self.assertEqual(result["rules"], [])
        self.assertNotIn(rule("operations-director"), result["read"])
        self.assertFalse(any("/business-rules/" in ref for ref in result["read"]))
        self.assertIn("references/sales-growth-workflow.md#两类观察", result["read"])

    def test_conversion_monitor_loads_only_actual_data_scope(self):
        local = self.context("conversion_monitoring", "monitor")
        self.assertEqual(local["rules"], [])
        for chosen, absent, source in (("inquiry", "crm-manager", "1688-inquiry-evaluate"),
                                       ("crm", "inquiry-analyst", "1688-shop-crm-customer-filter")):
            with self.subTest(chosen=chosen):
                result = self.context("conversion_monitoring", "monitor", "executor", "data_query", chosen)
                self.assertNotIn(rule(absent), result["read"])
                self.assertIn(f"source/plugins/1688-seller-assistant/skills/{source}/SKILL.md", result["read"])
                self.assertNotIn(rule("outreach-operator"), result["read"])
        with self.assertRaisesRegex(ContextError, "scope must be explicit"):
            self.context("conversion_monitoring", "monitor", "executor", "data_query")

    def test_deep_conversion_requires_scope_without_forcing_dual_rules(self):
        with self.assertRaisesRegex(ContextError, "scope must be explicit"):
            self.context("conversion_analysis", "plan")
        result = self.context("conversion_analysis", "evaluate", "executor", "crm")
        self.assertEqual(result["rules"], [rule("crm-manager")])
        result = self.context("conversion_analysis", "plan", "executor", "inquiry", "crm")
        self.assertEqual(set(result["rules"]), {rule("crm-manager"), rule("inquiry-analyst")})

    def test_plan_status_query_is_explicit_and_keeps_full_outreach_rule(self):
        result = self.context("conversion_monitoring", "monitor", "executor", "crm", "crm_plan_query")
        self.assertIn(rule("outreach-operator"), result["read"])
        self.assertNotIn(".agents/skills/1688-customer-conversion/references/crm-outreach.md", result["read"])
        with self.assertRaisesRegex(ContextError, "scope must be explicit"):
            self.context("conversion_monitoring", "monitor", "executor", "crm_plan_query")

    def test_manual_receipt_is_local_until_business_verification_selected(self):
        local = self.context("new_listing", "receipt")
        queried = self.context("new_listing", "receipt", "executor", "data_query")
        self.assertEqual(local["rules"], [])
        self.assertIn(rule("listing-publisher"), queried["read"])
        self.assertIn("source/plugins/1688-seller-assistant/skills/1688-product-manage/SKILL.md", queried["read"])
        self.assertIn("references/sales-growth-workflow.md#逐链接执行与人工交接", local["read"])
        self.assertIn("references/sales-growth-workflow.md#两类观察", local["read"])
        self.assertNotIn("references/account-strategies/songtai-sales-growth.md", local["read"])

    def test_due_evaluation_keeps_original_workflow_sections(self):
        result = self.context("daily_operations", "evaluate")
        self.assertIn("references/sales-growth-workflow.md#两类观察", result["read"])
        self.assertIn("references/sales-growth-workflow.md#完整周期与比较基线", result["read"])
        self.assertEqual(self.catalog["context_loading"]["entrypoints"]["manual_receipt"]["phase"], "receipt")

    def test_ads_data_images_and_sales_boundaries_cannot_disappear_by_default(self):
        self.assertIn("references/ad-decision-policy.md", self.context("traffic_and_ads", "plan")["read"])
        self.assertIn("references/ad-decision-policy.md", self.context("period_analysis", "plan", "executor", "ads")["read"])
        data = self.context("period_analysis", "execute")
        self.assertIn("references/runtime.md#连接和工具", data["read"])
        self.assertIn("references/runtime.md#数据和交接", data["read"])
        images = self.context("product_images", "execute")
        self.assertIn("references/runtime.md#默认图片方案", images["read"])
        self.assertNotIn("references/runtime.md#连接和工具", images["read"])
        self.assertIn(rule("creative-studio"), images["read"])
        self.assertIn("references/runtime.md#商品编辑字段边界", self.context("product_change", "plan")["read"])

    def test_multimodule_routes_require_explicit_module(self):
        with self.assertRaisesRegex(ContextError, "scope must be explicit"):
            self.context("erp_inventory", "execute")
        erp = self.context("erp_inventory", "execute", "executor", "jushuitan")
        self.assertIn(rule("erp-jushuitan-analyst"), erp["read"])
        self.assertNotIn(rule("erp-jackyun-analyst"), erp["read"])

    def test_evidence_deliverable_keeps_handoffs_inactive_without_loading_assets(self):
        evidence = self.context("traffic_and_ads", "plan", deliverable="evidence")
        plan = self.context("traffic_and_ads", "plan", deliverable="plan")
        self.assertEqual(evidence["deliverable_type"], "evidence")
        self.assertEqual(evidence["scope_origin"], "explicit")
        self.assertEqual(evidence["read"], plan["read"])
        self.assertNotIn("agents/image-agent/AGENTS.md", evidence["read"])
        self.assertNotIn("apply_images", evidence["active_conditions"])
        self.assertTrue(evidence["conditional_handoffs"])
        self.assertTrue(all(row["activation_status"] == "candidate_only"
                            for row in evidence["conditional_handoffs"]))
        image_handoff = next(row for row in plan["conditional_handoffs"]
                             if row["target_deliverable"] == "asset")
        self.assertEqual(image_handoff["target_route"], "product_images")
        self.assertEqual(image_handoff["target_owner"], "product_operations")
        self.assertEqual(image_handoff["activation_status"], "pending_scope_check")
        self.assertEqual(image_handoff["required_scope"], ["asset_preparation"])
        self.assertFalse(image_handoff["automatic_execution"])

    def test_defaults_describe_output_without_inventing_authorization(self):
        result = self.context("traffic_and_ads", "execute")
        self.assertEqual(result["deliverable_type"], "evidence")
        self.assertEqual(result["scope_origin"], "default")
        self.assertIn("不证明用户授权", result["scope_note"])
        legacy = self.context("daily_operations", "monitor")
        self.assertFalse(legacy["completion_contract"]["declared"])
        self.assertEqual(legacy["deliverable_type"], "evidence")
        self.assertEqual(legacy["conditional_handoffs"], [])

    def test_pure_design_plan_keeps_business_experiment_requirements_conditional(self):
        result = self.context("product_images", "plan", deliverable="plan")
        requirements = " ".join(result["completion_contract"]["requirements"])
        self.assertIn("涉及经营措施或试验时", requirements)
        self.assertIn("不强制设计试验", requirements)
        self.assertNotIn("apply_images", result["active_conditions"])

    def test_image_asset_is_distinct_from_application_and_checks_apply_boundary(self):
        asset = self.context("product_images", "execute", deliverable="asset")
        self.assertIn("真实可访问的成稿", " ".join(asset["completion_contract"]["requirements"]))
        self.assertNotIn("apply_images", asset["active_conditions"])
        application_handoff = asset["conditional_handoffs"][0]
        self.assertIn("product_write", application_handoff["required_scope"])
        self.assertFalse(application_handoff["automatic_execution"])
        with self.assertRaisesRegex(ContextError, "requires explicit --condition: apply_images"):
            self.context("product_images", "execute", deliverable="execution")
        application = self.context("product_images", "execute", "executor", "apply_images", deliverable="execution")
        self.assertIn("references/runtime.md#商品编辑字段边界", application["read"])
        self.assertIn(rule("product-editor"), application["rules"])
        self.assertEqual(application["completion_contract"]["required_conditions"], ["apply_images"])

    def test_deliverables_do_not_expand_unsupported_route_or_phase(self):
        for route, phase, deliverable in (("traffic_and_ads", "plan", "asset"),
                                         ("product_diagnosis", "execute", "execution"),
                                         ("daily_operations", "monitor", "asset")):
            with self.subTest(route=route, phase=phase, deliverable=deliverable):
                with self.assertRaisesRegex(ContextError, "not declared"):
                    self.context(route, phase, deliverable=deliverable)
        with self.assertRaisesRegex(ContextError, "Unknown deliverable"):
            self.context("traffic_and_ads", "plan", deliverable="publish")

    def test_completion_and_handoff_contracts_reject_scope_or_target_drift(self):
        def image_stage(data):
            return next(row for row in data["routes"] if row["id"] == "product_images")["phase_loading"]["execute"]
        def traffic_stage(data):
            return next(row for row in data["routes"] if row["id"] == "traffic_and_ads")["phase_loading"]["plan"]
        mutations = [
            lambda d: traffic_stage(d).pop("completion_contract"),
            lambda d: traffic_stage(d).update(conditional_handoffs=[]),
            lambda d: traffic_stage(d)["completion_contract"].update(default_deliverable="asset"),
            lambda d: traffic_stage(d)["completion_contract"].update(default_deliverable=[]),
            lambda d: traffic_stage(d)["completion_contract"]["deliverables"]["plan"].update(requirements=[]),
            lambda d: traffic_stage(d)["conditional_handoffs"][0].update(target_route="missing"),
            lambda d: traffic_stage(d)["conditional_handoffs"][0].update(target_route=[]),
            lambda d: traffic_stage(d)["conditional_handoffs"][0].update(target_phase="receipt"),
            lambda d: traffic_stage(d)["conditional_handoffs"][0].update(target_owner="operations_director"),
            lambda d: traffic_stage(d)["conditional_handoffs"][0].update(target_deliverable="asset"),
            lambda d: traffic_stage(d)["conditional_handoffs"][0].update(automatic_execution=True),
            lambda d: traffic_stage(d)["conditional_handoffs"][0].update(authorization="granted"),
            lambda d: traffic_stage(d)["conditional_handoffs"][1].update(required_scope=["read"]),
            lambda d: image_stage(d)["completion_contract"]["deliverables"]["execution"].update(required_conditions=[]),
            lambda d: image_stage(d)["conditional_handoffs"][0].update(required_scope=["asset_preparation"]),
        ]
        for mutate in mutations:
            altered = copy.deepcopy(self.catalog)
            mutate(altered)
            with self.subTest(mutation=mutate):
                self.assertTrue(validate_loading_contract(ROOT, altered))
    def test_unknown_and_unsupported_scope_is_an_error(self):
        for route, phase, role, conditions in [
            ("missing", "plan", "executor", ()),
            ("title_optimization", "guess", "executor", ()),
            ("title_optimization", "plan", "unknown", ()),
            ("platform_rules", "receipt", "executor", ()),
            ("title_optimization", "plan", "executor", ("jackyun",)),
        ]:
            with self.subTest(route=route, phase=phase, role=role, conditions=conditions):
                with self.assertRaises(ContextError):
                    self.context(route, phase, role, *conditions)

    def test_validator_rejects_missing_boundaries_sources_and_stage_contracts(self):
        mutations = [
            lambda d: d["context_loading"]["conditions"]["ads"].update(read=[]),
            lambda d: d["context_loading"]["conditions"]["data_query"].update(read=[]),
            lambda d: d["context_loading"]["rule_sources"][rule("daily-report")].update(read=[]),
            lambda d: next(r for r in d["routes"] if r["id"] == "title_optimization")["phase_loading"]["execute"].update(executor_read=[]),
            lambda d: next(r for r in d["routes"] if r["id"] == "product_change")["phase_loading"]["plan"].update(director_read=[rule("product-editor")]),
            lambda d: next(r for r in d["routes"] if r["id"] == "daily_operations")["phase_loading"].update(unknown={}),
        ]
        for mutate in mutations:
            altered = copy.deepcopy(self.catalog)
            mutate(altered)
            with self.subTest(mutation=mutate):
                self.assertTrue(validate_loading_contract(ROOT, altered))


class OriginalTextReadTests(unittest.TestCase):
    def test_section_is_verbatim_and_includes_subsections_but_not_next_section(self):
        content = "# File\r\n\r\n## Section\r\nbody\r\n### Child\r\nchild\r\n```md\r\n## Fake\r\n```\r\n\r\n## Next\r\nnext\r\n"
        expected = content[content.index("## Section"):content.index("## Next")]
        self.assertEqual(markdown_section(content, "Section"), expected)
        self.assertEqual(markdown_section(content, "section"), expected)
        with self.assertRaisesRegex(ContextError, "Missing section"):
            markdown_section(content, "Fake")

    def test_ambiguous_or_missing_anchor_is_rejected(self):
        with self.assertRaisesRegex(ContextError, "Ambiguous section"):
            markdown_section("## Same\na\n## Same\nb\n", "Same")
        with self.assertRaisesRegex(ContextError, "Missing section"):
            read_reference(ROOT, "references/runtime.md#不存在的标题")

    def test_full_rules_and_sources_cannot_be_excerpted(self):
        for path in (rule("title-optimizer") + "#任务流程",
                     "source/plugins/1688-seller-assistant/skills/1688-item-title-optimizer/SKILL.md#使用原则"):
            with self.assertRaisesRegex(ContextError, "require full reads"):
                read_reference(ROOT, path)

    def test_traversal_absolute_paths_directories_and_external_symlinks_fail(self):
        for ref in ("../AGENTS.md", "%2e%2e/AGENTS.md", str(ROOT / "AGENTS.md"), "references", "references/runtime.md#"):
            with self.subTest(ref=ref), self.assertRaises(ContextError):
                read_reference(ROOT, ref)
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "file.md"
            external.write_text("outside")
            (Path(folder) / "escape.md").symlink_to(external)
            with self.assertRaises(ContextError):
                read_reference(folder, "escape.md")

    def test_cli_list_is_lightweight_and_read_returns_exact_section(self):
        cli = [sys.executable, str(ROOT / "scripts/task_context.py")]
        listing = subprocess.run(cli + ["list"], capture_output=True, text=True, check=True)
        rows = json.loads(listing.stdout)
        self.assertEqual(len(rows), 24)
        self.assertEqual(set(rows[0]), {"id", "owner", "intent", "phases"})
        ref = "references/runtime.md#连接和工具"
        read = subprocess.run(cli + ["read", ref], capture_output=True, text=True, check=True)
        self.assertEqual(read.stdout, read_reference(ROOT, ref))
        failed = subprocess.run(cli + ["--route", "title_optimization", "--role", "executor"], capture_output=True, text=True)
        self.assertEqual(failed.returncode, 2)
        self.assertIn("--phase", failed.stderr)

    def test_cli_deliverable_is_explicit_and_does_not_dispatch(self):
        cli = [sys.executable, str(ROOT / "scripts/task_context.py")]
        selected = ["--route", "traffic_and_ads", "--phase", "plan", "--role", "executor", "--deliverable", "evidence"]
        result = subprocess.run(cli + selected, capture_output=True, text=True, check=True)
        context = json.loads(result.stdout)
        self.assertEqual(context["scope_origin"], "explicit")
        self.assertTrue(all(row["activation_status"] == "candidate_only" for row in context["conditional_handoffs"]))
        text_result = subprocess.run(cli + selected + ["--read"], capture_output=True, text=True, check=True)
        self.assertIn("# Deliverable: evidence / explicit", text_result.stdout)
        self.assertIn("Candidate handoffs (not dispatched)", text_result.stdout)
        invalid = subprocess.run(cli + ["list", "--deliverable", "asset"], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
