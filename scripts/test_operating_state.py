"""Offline fixtures only; all fabricated records live in TemporaryDirectory."""
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import operating_state as state


TEMPLATE = json.loads((state.ROOT / "references/templates/sales-growth-records.json").read_text())
AT = state.instant("2026-10-30T09:00:00+08:00")


class OperatingStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.path = self.root / "state.json"
        strategy_path = self.root / state.DEFAULT_STRATEGY
        strategy_path.parent.mkdir(parents=True)
        strategy_path.write_text("策略ID：test-only；版本：2；生效日期：2026-10-30\n")
        (self.root / "evidence.md").write_text("Offline fixture, not business evidence.\n")
        (self.root / "conversion.json").write_text('{"do_not_read_or_migrate": true}')
        self.payload = {
            "store_ref": "offline-fixture-store",
            "strategy": {"strategy_id": "test-only", "version": 2, "reference": state.DEFAULT_STRATEGY,
                         "sha256": hashlib.sha256(strategy_path.read_bytes()).hexdigest()},
            "conversion_state_ref": "conversion.json",
        }
        self.data = state.empty_ledger(self.payload, AT)
        self.data.update(
            history_reconciliation={"status": "reconciled", "reviewed_at": AT.isoformat(),
                                    "evidence_refs": ["evidence.md"], "outcome": "no_relevant_records", "unresolved": []},
            data_cutoff="2026-10-29T23:59:59+08:00",
            last_conclusion={"recorded_at": AT.isoformat(), "summary": "离线测试结论",
                             "evidence_refs": ["evidence.md"]})

    def action(self, aid="a1", status="awaiting_manual_execution", due="2026-10-30"):
        record = copy.deepcopy(TEMPLATE["action_template"])
        record.pop("workflow", None)  # Preserve explicit coverage of pre-workflow records.
        record.update(action_id=aid, store_ref=self.payload["store_ref"], strategy_version=2,
                      issue_ref="fixture-issue", product_id_or_draft_ref="fixture-product",
                      owner="product_operations", executor="fixture-executor",
                      objective_and_hypothesis="fixture objective", status=status,
                      next_step="fixture next step", next_review_at=due)
        record["manual_handoff"].update(required=True, reason="fixture", assignee="fixture",
                                        due_at=due, acceptance_and_required_receipt="fixture receipt")
        record["plan"].update(changes=[{"field": "fixture", "before": "a", "after": "b"}],
                              steps=["fixture step"], authorization_ref="evidence.md")
        record["execution"]["display_verification_status"] = "pending"
        if status == "completed":
            record["execution"].update(effective_at="2026-10-20T12:00:00+08:00",
                                       receipt_refs=["evidence.md"], readback_refs=["evidence.md"])
            record["evaluation_history"] = [{"evaluated_at": AT.isoformat(), "conclusion": "fixture correctness accepted",
                                              "decision": "completed", "evidence_refs": ["evidence.md"]}]
        if status in {"observing", "evaluating"}:
            record["execution"].update(effective_at="2026-10-20T12:00:00+08:00",
                                       receipt_refs=["evidence.md"], readback_refs=["evidence.md"])
            record["fixed_baseline"].update(
                period={"start": "2026-10-12", "end": "2026-10-18"},
                metrics=[{"metric": "fixture", "value": 1}], evidence_refs=["evidence.md"])
            record["observation"].update(
                start="2026-10-21T00:00:00+08:00", end="2026-10-30T00:00:00+08:00", evaluate_at=due,
                latest_reconsider_at="2026-11-02", primary_metrics=["fixture"],
                sample_and_maturity_basis="fixture")
        return record

    def workflow_action(self, deliverable_type="plan", status="plan_ready"):
        record = self.action(status=status)
        record["manual_handoff"].update(required=False, reason=None, assignee=None, due_at=None,
                                        acceptance_and_required_receipt=None)
        workflow = copy.deepcopy(TEMPLATE["action_template"]["workflow"])
        workflow["deliverable_type"] = deliverable_type
        if deliverable_type != "execution" and status == "plan_ready":
            workflow.update(delivered_at=AT.isoformat(), delivery_receipt_refs=["evidence.md"])
        workflow["decision"].update(choice="fixture choice", basis="fixture decision basis", evidence_refs=["evidence.md"])
        artifact_type = "image" if deliverable_type == "asset" else "plan" if deliverable_type == "execution" else deliverable_type
        artifact_ref = "asset.png" if artifact_type == "image" else "deliverable.md"
        if artifact_type == "image":
            # A minimal real PNG fixture; basic signature checking is not a visual quality review.
            import base64
            (self.root / artifact_ref).write_bytes(base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="))
        else:
            (self.root / artifact_ref).write_text("Offline deliverable fixture.\n")
        workflow["preparation"].update(required=True, required_types=[artifact_type], deliverables=[{
            "type": artifact_type, "artifact_refs": [artifact_ref], "check_status": "passed", "check_evidence_refs": ["evidence.md"]}])
        record["workflow"] = workflow
        return record

    def request_review(self, record, approval_type="plan_review"):
        item = record["workflow"]["preparation"]["deliverables"][0]
        record["status"] = "awaiting_approval"
        record["workflow"].update(delivered_at=None, delivery_receipt_refs=[])
        record["workflow"]["approval"].update(type=approval_type, necessary_basis="fixture explicit review requirement",
            basis_refs=["evidence.md"], review_objects=[{"type": item["type"], "artifact_refs": list(item["artifact_refs"])}], status="pending")

    def focus(self, action_ids=None):
        record = copy.deepcopy(TEMPLATE["focus_product_template"])
        record.update(focus_id="f1", store_ref=self.payload["store_ref"], company_instruction_ref="evidence.md",
                      product_ids_or_draft_refs=["fixture-product"], objective="fixture long-term",
                      started_at="2026-10-20T10:00:00+08:00", owner="product_operations", status="active",
                      next_weekly_review_at="2026-10-30", next_monthly_review_at="2026-11-01",
                      action_ids=action_ids or [])
        return record

    def review(self, action_ids=None):
        record = copy.deepcopy(TEMPLATE["review_template"])
        record.update(review_id="r1", store_ref=self.payload["store_ref"], strategy_version=2,
                      review_type="weekly", period={"start": "2026-10-19", "end": "2026-10-25"},
                      baseline={"start": "2026-09-21", "end": "2026-09-27", "basis": "fixture", "evidence_refs": ["evidence.md"]},
                      data_cutoff="2026-10-29T00:00:00+08:00", retrieved_at=AT.isoformat(),
                      coverage_and_comparability="fixture complete", bottleneck_conclusions=["fixture"],
                      action_ids=action_ids or [], evidence_refs=["evidence.md"])
        return record

    def ad(self, status="active", due="2026-10-30"):
        record = copy.deepcopy(TEMPLATE["ad_plan_template"])
        record.update(plan_ref="plan1", version=1, status=status, next_daily_check_at=due,
                      product_ids=["fixture-product"], objective="fixture", channel_and_targeting="fixture",
                      creative_and_landing_refs=["evidence.md"], starts_at="2026-10-20T12:00:00+08:00",
                      ends_at="2026-11-20T12:00:00+08:00", daily_budget=0, total_budget_cap=0, currency="CNY",
                      authorization_ref="evidence.md", metric_and_attribution_basis="fixture",
                      fixed_baseline_ref="a1.fixed_baseline", maturity_and_evaluation_conditions="fixture",
                      budget_pacing_and_intervention_conditions="fixture", execution_mode="manual",
                      executor="fixture", review_owner="traffic_operations", actual_plan_id="fixture-plan-id",
                      activation_evidence_refs=["evidence.md"])
        return record

    def query(self, command="summary", **kwargs):
        return state.query(self.data, self.root, self.path, state.digest(self.data), command, AT, **kwargs)

    def write(self, data=None):
        self.path.write_text(json.dumps(self.data if data is None else data, ensure_ascii=False))

    def cli(self, *args):
        return subprocess.run([sys.executable, str(state.ROOT / "scripts/operating_state.py"),
                               "--root", str(self.root), "--state", str(self.path),
                               "--at", AT.isoformat(), *args], capture_output=True, text=True)

    def test_missing_state_is_not_no_tasks_and_includes_strategy(self):
        result = self.cli("summary")
        self.assertEqual(result.returncode, 3)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "uninitialized")
        self.assertIsNone(output["counts"])
        self.assertTrue(output["history_reconciliation_required"])
        self.assertEqual(output["strategy"]["source"]["version"], "2")
        self.assertFalse(self.path.exists())

    def test_init_is_explicit_empty_history_required_and_never_overwrites(self):
        state.initialize(self.path, self.payload, self.root, AT)
        before = self.path.read_bytes()
        self.data = json.loads(before)
        result = self.query()
        self.assertEqual(result["status"], "history_reconciliation_required")
        self.assertEqual(result["total"], 0)
        self.assertFalse(result["dispatch_permitted_by_this_tool"])
        with self.assertRaises(state.StateError):
            state.initialize(self.path, self.payload, self.root, AT)
        self.assertEqual(before, self.path.read_bytes())

    def test_init_invalid_strategy_does_not_publish(self):
        self.payload["strategy"]["version"] = 99
        with self.assertRaises(state.StateError):
            state.initialize(self.path, self.payload, self.root, AT)
        self.assertFalse(self.path.exists())

    def test_atomic_init_failure_leaves_no_partial_ledger(self):
        with patch.object(state.os, "link", side_effect=OSError("fixture publish failure")):
            with self.assertRaises(state.StateError):
                state.initialize(self.path, self.payload, self.root, AT)
        self.assertFalse(self.path.exists())
        self.assertEqual(list(self.root.glob(".state.json.*.tmp")), [])

    def test_concurrent_initializers_publish_exactly_once(self):
        def initialize():
            try:
                state.initialize(self.path, self.payload, self.root, AT)
                return "created"
            except state.StateError:
                return "rejected"
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: initialize(), range(2)))
        self.assertCountEqual(results, ["created", "rejected"])
        state.read_json(self.path)

    def test_reconciled_empty_history_requires_evidence(self):
        result = self.query()
        self.assertEqual(result["status"], "ready")
        self.data["history_reconciliation"]["evidence_refs"] = []
        with self.assertRaises(state.StateError):
            self.query()

    def test_imported_history_cannot_have_no_records(self):
        self.data["history_reconciliation"]["outcome"] = "imported"
        with self.assertRaises(state.StateError):
            self.query()

    def test_unknown_first_even_when_scheduled_in_future(self):
        self.data["actions"] = [self.action("due"), self.action("unknown", "unknown", "2026-11-20")]
        result = self.query("due")
        self.assertEqual(result["items"][0]["id"], "unknown")
        self.assertTrue(result["items"][0]["requires_reconciliation"])
        self.assertEqual(result["counts"]["unknown_results"], 1)

    def test_all_records_scanned_before_pagination(self):
        self.data["actions"] = [self.action(f"a{n:03}", due="2026-11-20") for n in range(150)]
        self.data["actions"] += [self.action("z-due")]
        first = self.query("summary", limit=1)
        self.assertEqual(first["total"], 151)
        self.assertEqual(first["due"]["total"], 1)
        self.assertEqual(first["due"]["items"][0]["id"], "z-due")
        self.assertEqual(first["counts"]["actions"], 151)
        self.assertEqual(first["next_offset"], 1)

    def test_due_pages_cover_all_without_duplicates(self):
        self.data["actions"] = [self.action(f"a{n:03}") for n in range(27)]
        ids, offset = [], 0
        while offset is not None:
            result = self.query("due", offset=offset, limit=4)
            self.assertEqual(result["total"], 27)
            ids.extend(item["id"] for item in result["items"])
            offset = result["next_offset"]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 27)
        self.assertEqual(self.query("due", offset=100)["items"], [])

    def test_manual_pending_does_not_start_observation(self):
        action = self.action()
        self.data["actions"] = [action]
        self.assertEqual(self.query()["counts"]["manual_execution"], 1)
        action["observation"]["start"] = "2026-10-21T00:00:00+08:00"
        with self.assertRaises(state.StateError):
            self.query()

    def test_generic_manual_verification_status_also_cannot_observe(self):
        action = self.action(status="observing")
        action["status"] = "awaiting_verification"
        self.data["actions"] = [action]
        with self.assertRaises(state.StateError):
            self.query()
        action["observation"]["start"] = None
        self.assertEqual(self.query()["counts"]["manual_verification"], 1)

    def test_manual_observation_requires_actual_receipt_and_confirmation(self):
        action = self.action(status="observing")
        self.data["actions"] = [action]
        self.query()
        action["execution"]["receipt_refs"] = []
        with self.assertRaises(state.StateError):
            self.query()
        action["execution"]["receipt_refs"] = ["evidence.md"]
        action["execution"]["readback_refs"] = []
        with self.assertRaises(state.StateError):
            self.query()
        action["execution"]["effect_verification"] = {"status": "confirmed", "evidence_refs": ["evidence.md"]}
        self.assertEqual(self.query()["items"][0]["status"], "observing")
        self.assertEqual(action["execution"]["display_verification_status"], "pending")

    def test_all_manual_categories_visible_separately(self):
        self.data["actions"] = [self.action("review", "awaiting_manual_review"),
                                self.action("execute"), self.action("verify", "awaiting_manual_verification")]
        counts = self.query()["counts"]
        self.assertEqual([counts[k] for k in ("manual_review", "manual_execution", "manual_verification")], [1, 1, 1])

    def test_multiple_actions_and_focus_survive_one_completed(self):
        first, second = self.action("done", "completed"), self.action("pending")
        first["focus_id"] = second["focus_id"] = "f1"
        self.data["actions"] = [first, second]
        self.data["focus_products"] = [self.focus(["done", "pending"])]
        result = self.query("due")
        self.assertEqual({item["id"] for item in result["items"]}, {"f1", "pending"})
        obj = self.query("object", object_id="fixture-product")
        self.assertEqual({item["id"] for item in obj["items"]}, {"done", "pending", "f1"})
        self.assertEqual(self.data["focus_products"][0]["status"], "active")

    def test_relationships_preserved_and_dangling_ids_rejected(self):
        action = self.action()
        action["review_id"] = "r1"
        self.data["actions"], self.data["reviews"] = [action], [self.review(["a1"])]
        self.assertEqual({i["id"] for i in self.query("object", object_id="a1")["items"]}, {"a1", "r1"})
        self.data["reviews"][0]["action_ids"] = []
        with self.assertRaises(state.StateError):
            self.query()

    def test_focus_exit_requires_company_decision(self):
        focus = self.focus()
        focus["status"] = "exited"
        self.data["focus_products"] = [focus]
        with self.assertRaises(state.StateError):
            self.query()
        focus["company_exit_decision_ref"] = "evidence.md"
        self.assertEqual(self.query("due")["total"], 0)

    def test_ad_checks_scan_even_if_parent_action_is_completed(self):
        action = self.action(status="completed")
        action["ad_plan"] = self.ad()
        self.data["actions"] = [action]
        result = self.query("due")
        self.assertEqual([item["kind"] for item in result["items"]], ["ad_plan"])
        self.assertEqual(result["items"][0]["id"], "plan1")

    def test_active_ad_requires_real_activation_evidence(self):
        action = self.action()
        action["ad_plan"] = self.ad()
        action["ad_plan"]["activation_evidence_refs"] = []
        self.data["actions"] = [action]
        with self.assertRaises(state.StateError):
            self.query()

    def test_unknown_ad_and_missing_schedule_are_not_hidden(self):
        action = self.action(status="completed")
        action["ad_plan"] = self.ad("unknown", None)
        self.data["actions"] = [action]
        result = self.query("due")
        self.assertTrue(result["items"][0]["requires_reconciliation"])
        self.assertEqual(len(result["items"][0]["reasons"]), 2)

    def test_focus_weekly_monthly_and_daily_conditions_all_retained(self):
        focus = self.focus()
        focus.update(next_monthly_review_at="2026-10-30", next_ad_daily_check_at="2026-10-29")
        self.data["focus_products"] = [focus]
        self.assertEqual(len(self.query("due")["items"][0]["reasons"]), 3)

    def test_date_due_is_shanghai_midnight_and_z_offsets_compare_instants(self):
        self.data["actions"] = [self.action(due="2026-10-30")]
        before = state.instant("2026-10-29T15:59:59Z")
        exact = state.instant("2026-10-29T16:00:00Z")
        self.assertEqual(state.scan_due(self.data, before, []), [])
        self.assertEqual(len(state.scan_due(self.data, exact, [])), 1)
        self.data["actions"][0]["next_review_at"] = "2026-10-30T01:00:00Z"
        self.data["actions"][0]["manual_handoff"]["due_at"] = None
        self.assertEqual(self.query("due")["total"], 1)

    def test_no_implicit_timezone_and_invalid_dates_rejected(self):
        for timestamp in ("2026-10-30T09:00:00", "2026-02-30", "bad"):
            with self.subTest(timestamp=timestamp), self.assertRaises(state.StateError):
                state.instant(timestamp)

    def test_stale_future_and_missing_cutoffs_explicit(self):
        for cutoff, expected in (("2026-10-01T00:00:00+08:00", "stale"),
                                 ("2026-11-01T00:00:00+08:00", "future_relative_to_query"), (None, "missing")):
            self.data["data_cutoff"] = cutoff
            self.assertEqual(self.query()["data_freshness"]["status"], expected)

    def test_strategy_changed_or_missing_is_gap_but_due_still_scans(self):
        self.data["actions"] = [self.action()]
        path = self.root / state.DEFAULT_STRATEGY
        path.write_text("策略ID：test-only；版本：3；\n")
        result = self.query("due")
        self.assertEqual(result["strategy"]["status"], "mismatch")
        self.assertEqual(result["total"], 1)
        path.unlink()
        self.assertEqual(self.query()["strategy"]["status"], "missing")

    def test_queries_never_modify_ledger_baseline_or_conversion(self):
        self.data["actions"] = [self.action(status="observing")]
        self.write()
        original, conversion = self.path.read_bytes(), (self.root / "conversion.json").read_bytes()
        baseline = copy.deepcopy(self.data["actions"][0]["fixed_baseline"])
        for command in ("summary", "due", "validate"):
            result = self.cli(command)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual((self.root / "conversion.json").read_bytes(), conversion)
        self.assertEqual(self.data["actions"][0]["fixed_baseline"], baseline)

    def test_fixed_baseline_snapshot_hash_detects_change(self):
        action = self.action(status="observing")
        baseline = action["fixed_baseline"]
        baseline["snapshot_sha256"] = state.digest(baseline)
        self.data["actions"] = [action]
        self.query()
        baseline["metrics"][0]["value"] = 2
        with self.assertRaises(state.StateError):
            self.query()

    def test_evaluation_extension_preserves_original_due_and_reason(self):
        action = self.action(status="observing", due="2026-11-03")
        action["evaluation_history"] = [{"evaluated_at": AT.isoformat(), "scheduled_evaluate_at": "2026-10-30",
                                          "conclusion": "证据不足", "decision": "补证",
                                          "next_evaluate_at": "2026-11-03", "extension_reason": "fixture data delay",
                                          "evidence_refs": ["evidence.md"]}]
        self.data["actions"] = [action]
        result = self.query()
        self.assertEqual(result["items"][0]["last_evaluation"]["scheduled_evaluate_at"], "2026-10-30")
        del action["evaluation_history"][0]["extension_reason"]
        with self.assertRaises(state.StateError):
            self.query()

    def test_bad_record_beyond_page_fails_instead_of_silently_skipping(self):
        self.data["actions"] = [self.action(f"a{n}") for n in range(100)]
        del self.data["actions"][-1]["status"]
        with self.assertRaises(state.StateError):
            self.query(limit=1)

    def test_wrong_store_duplicate_ids_and_second_conversion_state_rejected(self):
        for mutation in ("store", "duplicate", "conversion"):
            with self.subTest(mutation=mutation):
                self.data["actions"] = [self.action()]
                if mutation == "store":
                    self.data["actions"][0]["store_ref"] = "another-fixture"
                elif mutation == "duplicate":
                    self.data["actions"].append(self.action())
                else:
                    self.data["conversion_issues"] = []
                with self.assertRaises(state.StateError):
                    self.query()

    def test_missing_evidence_and_conversion_ref_are_explicit_gaps(self):
        (self.root / "evidence.md").unlink()
        (self.root / "conversion.json").unlink()
        result = self.query()
        codes = set(result["gap_counts"])
        self.assertIn("evidence_file_missing", codes)
        self.assertIn("conversion_state_missing", codes)
        self.assertEqual(result["conversion_state"]["status"], "missing")

    def test_cli_invalid_pagination_and_malformed_json(self):
        self.write()
        for args in (("summary", "--limit", "0"), ("due", "--offset", "-1"), ("object", "--id", "missing")):
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stderr)["status"], "error")
        for content in ('{"duplicate": 1, "duplicate": 2}', '{"bad": NaN}', '{"broken":'):
            self.path.write_text(content)
            self.assertEqual(self.cli("summary").returncode, 2)

    def test_summary_short_cards_and_gap_pagination(self):
        self.data["actions"] = [self.action(f"a{n}", "unknown", None) for n in range(20)]
        result = self.query(gap_limit=3)
        self.assertEqual(len(result["items"]), 10)
        self.assertNotIn("manual_handoff", result["items"][0])
        self.assertNotIn("execution", result["items"][0])
        self.assertNotIn("observation", result["items"][0])
        self.assertEqual(len(result["gaps"]["items"]), 3)
        self.assertEqual(result["gaps"]["next_offset"], 3)
        self.assertEqual(result["gap_counts"]["action_schedule_missing"], 20)
        detail = self.query("object", object_id="a0", limit=100)
        self.assertIn("manual_handoff", detail["items"][0]["record"])

    def test_object_expands_same_issue_and_bidirectional_related_actions(self):
        one, two, three = self.action("one"), self.action("two"), self.action("three")
        one["issue_ref"], two["issue_ref"], three["issue_ref"] = "same", "same", "different"
        three["related_action_ids"] = ["two"]
        self.data["actions"] = [one, two, three]
        result = self.query("object", object_id="one")
        self.assertEqual({item["id"] for item in result["items"]}, {"one", "two", "three"})

    def test_observation_end_exclusive_boundary_and_midnight_effect(self):
        action = self.action(status="observing")
        action["execution"]["effective_at"] = "2026-10-21T00:00:00+08:00"
        self.data["actions"] = [action]
        self.query()  # Equal midnight start/effective is valid.
        action["observation"]["evaluate_at"] = "2026-10-29T23:59:59+08:00"
        with self.assertRaises(state.StateError):
            self.query()
        action["observation"]["evaluate_at"] = "2026-10-30"
        action["observation"]["end"] = "2026-10-29"
        with self.assertRaises(state.StateError):
            self.query()  # Date-only windows cannot lose the last complete day.

    def test_evaluation_cannot_precede_complete_observation_end(self):
        action = self.action(status="observing")
        action["evaluation_history"] = [{"evaluated_at": "2026-10-29T23:00:00+08:00",
                                          "scheduled_evaluate_at": "2026-10-30",
                                          "conclusion": "fixture", "decision": "fixture",
                                          "evidence_refs": ["evidence.md"]}]
        self.data["actions"] = [action]
        with self.assertRaises(state.StateError):
            self.query()

    def test_baseline_must_precede_effective_date(self):
        action = self.action(status="observing")
        action["fixed_baseline"]["period"]["end"] = "2026-10-21"
        self.data["actions"] = [action]
        with self.assertRaises(state.StateError):
            self.query()

    def test_completed_correctness_fix_needs_no_business_observation(self):
        action = self.action(status="completed")
        action["evaluation_history"] = [{"evaluated_at": AT.isoformat(), "conclusion": "后台字段正确性验收",
                                          "decision": "完成", "evidence_refs": ["evidence.md"]}]
        self.data["actions"] = [action]
        self.assertEqual(self.query("due")["total"], 0)

    def test_completed_without_execution_or_conclusion_cannot_hide(self):
        for missing in ("effective_at", "receipt_refs", "evaluation_history"):
            action = self.action(status="completed")
            if missing == "evaluation_history":
                action[missing] = []
            else:
                action["execution"][missing] = [] if missing == "receipt_refs" else None
            self.data["actions"] = [action]
            with self.subTest(missing=missing), self.assertRaises(state.StateError):
                self.query("due")

    def test_cancelled_requires_reason_and_evidence_but_not_execution(self):
        action = self.action(status="cancelled")
        self.data["actions"] = [action]
        with self.assertRaises(state.StateError):
            self.query()
        action["cancellation"] = {"recorded_at": AT.isoformat(), "reason": "fixture decision not to execute",
                                  "evidence_refs": ["evidence.md"]}
        self.assertEqual(self.query("due")["total"], 0)

    def test_legacy_workflow_is_readable_but_not_assumed_ready(self):
        self.data["actions"] = [self.action()]
        result = self.query("check", object_id="a1")
        self.assertTrue(result["structurally_valid"])
        self.assertFalse(result["check_passed"])
        self.assertEqual(result["readiness"]["contract"], "legacy_unknown")

    def test_evidence_plan_and_asset_delivery_do_not_require_remote_execution(self):
        for deliverable_type in ("evidence", "plan", "asset"):
            with self.subTest(deliverable_type=deliverable_type):
                action = self.workflow_action(deliverable_type)
                self.data["actions"] = [action]
                result = self.query("check", object_id="a1")
                self.assertTrue(result["check_passed"])
                self.assertIsNone(action["execution"]["effective_at"])
                self.assertFalse(result["readiness"]["execution_ready"])
                self.assertFalse(result["readiness"]["user_action_required"])

    def test_plan_review_requires_checked_plan_but_does_not_require_image(self):
        action = self.workflow_action()
        self.request_review(action)
        action["workflow"]["preparation"]["deliverables"].append({
            "type": "image", "artifact_refs": [], "check_status": "pending", "check_evidence_refs": []})
        self.data["actions"] = [action]
        result = self.query("check", object_id="a1", requirement="handoff")
        self.assertTrue(result["check_passed"])
        self.assertTrue(result["readiness"]["user_action_required"])
        self.assertFalse(result["readiness"]["preparation_ready"])
        self.assertFalse(self.query("check", object_id="a1")["check_passed"])

    def test_asset_review_cannot_use_only_plan_or_pdf_as_image(self):
        action = self.workflow_action()
        self.request_review(action, "asset_review")
        self.data["actions"] = [action]
        self.assertFalse(self.query("check", object_id="a1", requirement="handoff")["check_passed"])
        (self.root / "brief.pdf").write_bytes(b"%PDF-1.7\nOffline brief")
        item = action["workflow"]["preparation"]["deliverables"][0]
        action["workflow"]["preparation"]["required_types"] = ["image"]
        item.update(type="image", artifact_refs=["brief.pdf"])
        action["workflow"]["approval"]["review_objects"] = [{"type": "image", "artifact_refs": ["brief.pdf"]}]
        result = self.query("check", object_id="a1", requirement="handoff")
        self.assertFalse(result["check_passed"])
        self.assertIn("artifact_type_mismatch", {item["status"] for item in result["readiness"]["reference_checks"]})

    def test_image_extension_does_not_make_text_into_image(self):
        action = self.workflow_action("asset")
        (self.root / "asset.png").write_text("This is a design brief, not an image.")
        self.data["actions"] = [action]
        self.assertFalse(self.query("check", object_id="a1")["check_passed"])

    def test_image_requirement_cannot_be_satisfied_by_copy_or_other(self):
        for artifact_type in ("copy", "other"):
            with self.subTest(artifact_type=artifact_type):
                action = self.workflow_action("asset")
                action["workflow"]["preparation"]["deliverables"][0].update(type=artifact_type, artifact_refs=["evidence.md"])
                self.data["actions"] = [action]
                self.assertFalse(self.query("check", object_id="a1")["check_passed"])
                self.request_review(action, "asset_review")
                self.assertFalse(self.query("check", object_id="a1", requirement="handoff")["check_passed"])

    def test_asset_and_execution_authorization_review_require_all_required_materials(self):
        for approval_type in ("asset_review", "execution_authorization"):
            with self.subTest(approval_type=approval_type):
                action = self.workflow_action("asset" if approval_type == "asset_review" else "execution")
                self.request_review(action, approval_type)
                action["workflow"]["preparation"]["required_types"].append("copy")
                self.data["actions"] = [action]
                self.assertFalse(self.query("check", object_id="a1", requirement="handoff")["check_passed"])

    def test_file_presence_alone_and_unchecked_remote_refs_are_not_ready(self):
        action = self.workflow_action()
        self.data["actions"] = [action]
        item = action["workflow"]["preparation"]["deliverables"][0]
        item["check_evidence_refs"] = []
        result = self.query("check", object_id="a1")
        self.assertTrue(result["structurally_valid"])
        self.assertFalse(result["check_passed"])
        item["check_evidence_refs"] = ["evidence.md"]
        item["artifact_refs"] = ["https://example.com/plan.pdf"]
        result = self.query("check", object_id="a1")
        self.assertFalse(result["check_passed"])
        self.assertIn("external_pending_verification", {item["status"] for item in result["readiness"]["reference_checks"]})

    def test_review_without_necessary_basis_does_not_create_user_task(self):
        action = self.workflow_action()
        self.request_review(action)
        action["workflow"]["approval"]["necessary_basis"] = None
        self.data["actions"] = [action]
        result = self.query()
        self.assertEqual(result["counts"]["manual_review"], 0)
        self.assertEqual(result["counts"]["unready_review_handoffs"], 1)
        self.assertFalse(result["items"][0]["readiness"]["user_action_required"])

    def test_existing_authorization_is_not_requested_again(self):
        action = self.workflow_action()
        self.request_review(action)
        action["workflow"]["approval"].update(status="covered", authorization_ref="evidence.md")
        self.data["actions"] = [action]
        with self.assertRaises(state.StateError):
            self.query()
        action["status"] = "plan_ready"
        action["workflow"].update(delivered_at=AT.isoformat(), delivery_receipt_refs=["evidence.md"])
        result = self.query("check", object_id="a1")
        self.assertTrue(result["check_passed"])
        self.assertFalse(result["readiness"]["user_action_required"])

    def test_nonexecution_scope_cannot_acquire_publication_authorization_or_effect(self):
        for mutation in ("status", "approval", "effect"):
            with self.subTest(mutation=mutation):
                action = self.workflow_action("evidence")
                if mutation == "status":
                    action["status"] = "executing"
                elif mutation == "approval":
                    self.request_review(action, "execution_authorization")
                else:
                    action["execution"].update(effective_at=AT.isoformat(), receipt_refs=["evidence.md"])
                self.data["actions"] = [action]
                with self.assertRaises(state.StateError):
                    self.query()

    def test_execution_ready_does_not_mean_execution_delivered(self):
        action = self.workflow_action("execution", "awaiting_execution")
        self.data["actions"] = [action]
        result = self.query("check", object_id="a1", requirement="execution")
        self.assertTrue(result["check_passed"])
        self.assertFalse(result["readiness"]["closure_ready"])
        action["plan"]["authorization_ref"] = None
        self.assertFalse(self.query("check", object_id="a1", requirement="execution")["check_passed"])

    def test_execution_readiness_requires_executor_and_next_step(self):
        for missing in ("executor", "next_step", "owner"):
            with self.subTest(missing=missing):
                action = self.workflow_action("execution", "awaiting_execution")
                action[missing] = None
                self.data["actions"] = [action]
                self.assertFalse(self.query("check", object_id="a1", requirement="execution")["check_passed"])

    def test_execution_check_preserves_strategy_and_history_preconditions(self):
        for problem in ("strategy_source", "action_version", "history"):
            with self.subTest(problem=problem):
                action = self.workflow_action("execution", "awaiting_execution")
                self.data["actions"] = [action]
                original_history = copy.deepcopy(self.data["history_reconciliation"])
                if problem == "strategy_source":
                    self.data["strategy"]["sha256"] = "0" * 64
                elif problem == "action_version":
                    action["strategy_version"] = 1
                else:
                    self.data["history_reconciliation"]["status"] = "required"
                result = self.query("check", object_id="a1", requirement="execution")
                self.assertFalse(result["check_passed"])
                self.assertTrue(result["blocking_gaps"])
                self.assertNotEqual(result["ledger_status"], "ready")
                self.assertNotEqual(result["status"], "ready")
                self.data["strategy"]["sha256"] = self.payload["strategy"]["sha256"]
                self.data["history_reconciliation"] = original_history

    def test_global_strategy_warning_does_not_block_evidence_delivery(self):
        self.data["actions"] = [self.workflow_action("evidence")]
        self.data["strategy"]["sha256"] = "0" * 64
        result = self.query("check", object_id="a1")
        self.assertTrue(result["check_passed"])
        self.assertEqual(result["status"], "needs_attention")
        self.assertEqual(result["check_status"], "ready")
        self.assertEqual(result["blocking_gaps"], [])

    def test_observation_check_does_not_hide_missing_fixed_baseline(self):
        action = self.workflow_action("execution", "observing")
        action["fixed_baseline"].update(period=None, metrics=[], evidence_refs=[])
        self.data["actions"] = [action]
        result = self.query("check", object_id="a1")
        self.assertFalse(result["check_passed"])
        self.assertIn("fixed_baseline_missing", {item["code"] for item in result["blocking_gaps"]})

    def test_execution_delivery_still_requires_readback_and_observation_conditions(self):
        action = self.workflow_action("execution", "observing")
        self.data["actions"] = [action]
        self.assertTrue(self.query("check", object_id="a1")["check_passed"])
        action["execution"]["readback_refs"] = []
        self.assertFalse(self.query("check", object_id="a1")["check_passed"])
        action["execution"]["readback_refs"] = ["evidence.md"]
        action["observation"]["latest_reconsider_at"] = None
        self.assertFalse(self.query("check", object_id="a1")["check_passed"])

    def test_investigation_and_preparation_deadlines_are_scanned(self):
        action = self.workflow_action(status="preparing_assets")
        action["next_review_at"] = "2026-11-20"
        action["workflow"]["decision"]["investigation"].update(status="in_progress", blocking=False,
            stop_conditions=["fixture decision can be made"], stop_at="2026-10-30")
        action["workflow"]["preparation"].update(due_at="2026-10-29")
        action["workflow"]["preparation"]["deliverables"][0]["check_status"] = "pending"
        self.data["actions"] = [action]
        result = self.query("due")
        self.assertEqual({item["condition"] for item in result["items"][0]["reasons"]}, {"investigation_stop_at", "preparation_due_at"})

    def test_delivered_nonexecution_stage_does_not_repeat_due_or_missing_schedule(self):
        action = self.workflow_action("evidence")
        action["next_review_at"] = None
        self.data["actions"] = [action]
        result = self.query("due")
        self.assertEqual(result["items"], [])
        self.assertNotIn("action_schedule_missing", result["gap_counts"])
        self.assertEqual(result["counts"]["delivered_stages"], 1)
        self.assertTrue(self.query()["items"][0]["readiness"]["delivery_closed"])
        action["workflow"]["delivered_at"] = None
        action["workflow"]["delivery_receipt_refs"] = []
        self.assertTrue(self.query("check", object_id="a1")["check_passed"])
        self.assertTrue(self.query("check", object_id="a1", requirement="delivery")["check_passed"])
        self.assertEqual(self.query("due")["total"], 1)

    def test_delivery_receipt_cannot_hide_unready_artifact_or_business_execution(self):
        action = self.workflow_action("asset")
        action["workflow"]["preparation"]["deliverables"][0]["check_status"] = "pending"
        self.data["actions"] = [action]
        self.assertFalse(self.query("check", object_id="a1")["check_passed"])
        self.assertEqual(self.query("due")["total"], 1)
        action = self.workflow_action("execution", "awaiting_execution")
        action["workflow"].update(delivered_at=AT.isoformat(), delivery_receipt_refs=["evidence.md"])
        self.data["actions"] = [action]
        with self.assertRaises(state.StateError):
            self.query()

    def test_delivered_stage_does_not_hide_ad_focus_or_unknown_reconciliation(self):
        action = self.workflow_action("evidence")
        action["ad_plan"] = self.ad()
        self.data["actions"] = [action]
        self.data["focus_products"] = [self.focus()]
        result = self.query("due")
        self.assertEqual({item["id"] for item in result["items"]}, {"plan1", "f1"})
        action["status"] = "unknown"
        result = self.query("due")
        self.assertEqual({item["id"] for item in result["items"]}, {"a1", "plan1", "f1"})
        self.assertTrue(next(item for item in result["items"] if item["id"] == "a1")["requires_reconciliation"])

    def test_investigation_needs_a_stop_and_only_blocking_unknowns_prevent_decision(self):
        action = self.workflow_action()
        investigation = action["workflow"]["decision"]["investigation"]
        action["workflow"]["decision"]["key_unknowns"] = ["fixture cause is unproven"]
        self.data["actions"] = [action]
        self.assertTrue(self.query("check", object_id="a1")["check_passed"])
        investigation.update(status="in_progress", blocking=True)
        self.assertFalse(self.query("check", object_id="a1")["check_passed"])
        investigation.update(blocking=False, stop_conditions=["fixture stop"], stop_at="2026-11-01")
        self.assertTrue(self.query("check", object_id="a1")["check_passed"])

    def test_workflow_check_cli_exit_and_queries_are_read_only(self):
        action = self.workflow_action()
        self.data["actions"] = [action]
        self.write()
        originals = {path: path.read_bytes() for path in (self.path, self.root / "conversion.json", self.root / "deliverable.md", self.root / "evidence.md")}
        self.assertEqual(self.cli("check", "--id", "a1").returncode, 0)
        action["workflow"]["preparation"]["deliverables"][0]["check_status"] = "pending"
        self.write()
        originals[self.path] = self.path.read_bytes()
        result = self.cli("check", "--id", "a1")
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertFalse(json.loads(result.stdout)["check_passed"])
        for command in ("summary", "due", "validate"):
            self.assertEqual(self.cli(command).returncode, 0)
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
