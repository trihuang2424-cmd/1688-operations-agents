#!/usr/bin/env python3
"""Offline behavior regressions for complete metadata and task tool selection."""
import copy
import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tool_catalog import (ASSIGNMENTS, DEFINITIONS, ROOT, CatalogError,
                          build_tool_context, catalog_diff, import_snapshot,
                          load_current_catalog, normalize_snapshot,
                          validate_current_catalog)


class ToolCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        baseline = json.loads((ROOT / "catalog/live-tool-schemas.json").read_text())
        names = {"inquiry_data_load", "get_search_channel_detail", "customer_stats"}
        cls.original = [copy.deepcopy(row) for row in baseline["tools"] if row["name"] in names]
        if len(cls.original) != 3:
            raise AssertionError("Required real metadata fixture is missing")
        cls.registry = json.loads((ROOT / "catalog/agent-registry.json").read_text())

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="1688-tool-catalog-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.snapshot = {"schema_version": 1, "captured_at": "2026-11-10T08:00:00Z",
                         "source": {"kind": "live_accio_metadata", "server": "accio",
                                    "toolkit": "ali1688", "catalog_complete": True},
                         "tool_count": 3, "tools": copy.deepcopy(self.original)}
        self.write("catalog/agent-registry.json", self.registry)
        import_snapshot(self.root, self.snapshot)
        self.review_all()

    def write(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def review_all(self):
        assignments = load_current_catalog(self.root)["assignments"]
        for row in assignments["tools"]:
            traffic = row["name"] == "get_search_channel_detail"
            row.update(capabilities=["traffic_analysis" if traffic else "customer_conversion"],
                       owner="traffic_operations" if traffic else "operations_director",
                       review_status="reviewed", basis="Reviewed original metadata in this local test fixture.")
        self.write(ASSIGNMENTS, assignments)

    def new_tool(self):
        return {"name": "new_query", "description": "查询含日期与分页约束的新资料；保留原始说明。",
                "inputSchema": {"type": "object", "required": ["ds"],
                                "properties": {"ds": {"type": "string", "pattern": "^[0-9]{8}$"},
                                               "range": {"enum": ["recent7", "recent30"]},
                                               "filters": {"type": "object", "properties": {
                                                   "tags": {"type": "array", "items": {"type": "string"}}}}},
                                "additionalProperties": False},
                "server": "accio", "effects": "unclassified/potential_changes",
                "annotations": {"readOnlyHint": False}}

    def append_new_tool(self):
        updated = copy.deepcopy(self.snapshot)
        updated["tools"].append(self.new_tool())
        updated["tool_count"] += 1
        return updated

    def test_actual_metadata_descriptions_and_nested_schemas_survive_import(self):
        bundle = load_current_catalog(self.root)
        self.assertEqual(validate_current_catalog(self.root), [])
        by_name = {row["name"]: row for row in bundle["definitions"]["tools"]}
        for original in self.original:
            self.assertEqual(by_name[original["name"]]["description"], original["description"])
            self.assertEqual(by_name[original["name"]]["inputSchema"], original["inputSchema"])
        new = self.append_new_tool()
        import_snapshot(self.root, new)
        imported = next(row for row in load_current_catalog(self.root)["definitions"]["tools"]
                        if row["name"] == "new_query")
        self.assertEqual(imported["inputSchema"], self.new_tool()["inputSchema"])

    def test_missing_assignment_is_an_error_not_implicit_permission(self):
        assignments = load_current_catalog(self.root)["assignments"]
        removed = assignments["tools"].pop()["name"]
        self.write(ASSIGNMENTS, assignments)
        self.assertIn("Missing assignment (use explicit unassigned): " + removed,
                      validate_current_catalog(self.root))
        with self.assertRaises(CatalogError):
            build_tool_context(self.root, ["customer_conversion"])

    def test_added_tools_are_explicitly_unassigned_and_existing_reviews_survive(self):
        result = import_snapshot(self.root, self.append_new_tool())
        self.assertEqual(result["diff"]["added"], ["new_query"])
        self.assertEqual(result["diff"]["removed"], [])
        assignments = {row["name"]: row for row in load_current_catalog(self.root)["assignments"]["tools"]}
        self.assertEqual(assignments["new_query"]["review_status"], "unassigned")
        self.assertEqual(assignments["new_query"]["capabilities"], [])
        self.assertIsNone(assignments["new_query"]["owner"])
        self.assertEqual(assignments["inquiry_data_load"]["review_status"], "reviewed")
        context = build_tool_context(self.root, ["customer_conversion"])
        self.assertEqual(context["unassigned"], {"count": 1, "names": ["new_query"]})
        self.assertNotIn("new_query", [row["name"] for row in context["candidates"]])

    def test_complete_snapshot_removal_reconciles_assignments(self):
        updated = copy.deepcopy(self.snapshot)
        updated["tools"] = [r for r in updated["tools"] if r["name"] != "customer_stats"]
        updated["tool_count"] = len(updated["tools"])
        result = import_snapshot(self.root, updated)
        self.assertEqual(result["diff"]["removed"], ["customer_stats"])
        self.assertEqual(validate_current_catalog(self.root), [])
        self.assertNotIn("customer_stats", [r["name"] for r in load_current_catalog(self.root)["assignments"]["tools"]])

    def test_partial_page_cannot_be_imported_or_used_to_infer_removal(self):
        page = copy.deepcopy(self.snapshot)
        page["source"].pop("catalog_complete")
        page["tools"] = page["tools"][:1]
        page["tool_count"] = 1
        before = (self.root / DEFINITIONS).read_bytes()
        for operation in (lambda: import_snapshot(self.root, page),
                          lambda: catalog_diff(self.snapshot, page)):
            with self.assertRaisesRegex(CatalogError, "completeness"):
                operation()
        self.assertEqual((self.root / DEFINITIONS).read_bytes(), before)

    def test_claimed_complete_page_with_total_count_mismatch_is_rejected(self):
        page = copy.deepcopy(self.snapshot)
        page["tools"] = page["tools"][:1]
        with self.assertRaisesRegex(CatalogError, "tool_count"):
            import_snapshot(self.root, page)

    def test_definition_change_reports_fields_and_requires_planning_review(self):
        updated = copy.deepcopy(self.snapshot)
        tool = next(row for row in updated["tools"] if row["name"] == "inquiry_data_load")
        tool["description"] += " 新的接口前置条件。"
        tool["inputSchema"]["properties"]["new_required_field"] = {"type": "string"}
        tool["inputSchema"].setdefault("required", []).append("new_required_field")
        result = import_snapshot(self.root, updated)
        self.assertEqual(result["diff"]["changed"],
                         [{"name": "inquiry_data_load", "fields": ["description", "inputSchema"]}])
        current = load_current_catalog(self.root)
        assignment = next(row for row in current["assignments"]["tools"] if row["name"] == "inquiry_data_load")
        self.assertEqual(assignment["review_status"], "unassigned")

    def test_metadata_timestamp_change_alone_does_not_reset_reviews(self):
        updated = copy.deepcopy(self.snapshot)
        updated["captured_at"] = "2026-11-12T08:00:00+00:00"
        result = import_snapshot(self.root, updated)
        self.assertEqual(result["diff"]["changed"], [])
        self.assertTrue(all(r["review_status"] == "reviewed"
                            for r in load_current_catalog(self.root)["assignments"]["tools"]))

    def test_capability_selection_does_not_dump_other_domain_tools(self):
        customer = build_tool_context(self.root, ["customer_conversion"])
        self.assertEqual({row["name"] for row in customer["candidates"]},
                         {"customer_stats", "inquiry_data_load"})
        traffic = build_tool_context(self.root, ["traffic_analysis"])
        self.assertEqual([row["name"] for row in traffic["candidates"]], ["get_search_channel_detail"])
        empty = build_tool_context(self.root, [])
        self.assertEqual(empty["candidates"], [])
        self.assertEqual(len(empty["capability_map"]), len(self.registry["skills"]))
        self.assertTrue(all("description" not in row for row in empty["capability_map"]))
        actual = {row["capability"]: row for row in empty["capability_map"]}
        for registered in self.registry["skills"]:
            self.assertEqual(actual[registered["id"]]["display_name"], registered["display_name"])
            self.assertEqual(actual[registered["id"]]["skill"], registered["skill"])
        self.assertEqual(customer["additional_capability_tools"]["count"], 0)

    def test_profile_narrows_candidate_cards_and_exposes_missing_tools(self):
        profile = {"groups": [{"id": "conversation", "purpose": "Original conversation evidence",
                                "tools": ["inquiry_data_load", "missing_query"],
                                "selection_note": "Verify scope and live definition before a call."}]}
        context = build_tool_context(self.root, ["customer_conversion"], profile)
        self.assertEqual([row["name"] for row in context["candidates"]], ["inquiry_data_load"])
        self.assertEqual(context["missing_profile_tools"], ["missing_query"])
        self.assertEqual(context["groups"], profile["groups"])
        self.assertFalse(context["automatic_fallback"])
        self.assertTrue(context["live_describe_required"])
        self.assertEqual(context["permission_status"], "not_inferred_from_catalog")
        self.assertEqual(context["additional_capability_tools"]["names"], ["customer_stats"])

    def test_profile_does_not_hide_new_reviewed_same_capability_tools(self):
        import_snapshot(self.root, self.append_new_tool())
        assignments = load_current_catalog(self.root)["assignments"]
        added = next(row for row in assignments["tools"] if row["name"] == "new_query")
        added.update(capabilities=["customer_conversion"], owner="operations_director",
                     review_status="reviewed", basis="New definition reviewed for customer evidence.")
        self.write(ASSIGNMENTS, assignments)
        context = build_tool_context(self.root, ["customer_conversion"],
                                     {"groups": [{"id": "conversation", "tools": ["inquiry_data_load"]}]})
        self.assertEqual([row["name"] for row in context["candidates"]], ["inquiry_data_load"])
        additional = context["additional_capability_tools"]
        self.assertEqual(additional["count"], 2)
        self.assertEqual(additional["names"], ["customer_stats", "new_query"])
        self.assertNotIn("get_search_channel_detail", additional["names"])
        command = shlex.split(additional["discovery_command"])
        command[0] = sys.executable
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        discovered = json.loads(result.stdout)
        self.assertEqual({row["name"] for row in discovered["candidates"]},
                         {"inquiry_data_load", "customer_stats", "new_query"})
        self.assertEqual(discovered["additional_capability_tools"]["count"], 0)

    def test_card_schema_pointer_resolves_without_copying_full_schema(self):
        context = build_tool_context(self.root, ["customer_conversion"])
        definitions = load_current_catalog(self.root)["definitions"]
        for card in context["candidates"]:
            filename, pointer = card["schema_ref"].split("#")
            self.assertEqual(filename, DEFINITIONS)
            parts = pointer.strip("/").split("/")
            schema = definitions[parts[0]][int(parts[1])][parts[2]]
            self.assertEqual(card["required"], schema.get("required", []))
            self.assertNotIn("inputSchema", card)

    def test_unassigned_profile_tool_is_visible_with_its_unreviewed_status(self):
        import_snapshot(self.root, self.append_new_tool())
        result = build_tool_context(self.root, ["customer_conversion"],
                                    {"groups": [{"id": "new", "tools": ["new_query"]}]})
        self.assertEqual(result["candidates"][0]["planning"]["review_status"], "unassigned")
        self.assertFalse(result["automatic_fallback"])

    def test_duplicate_and_unknown_assignments_fail_coverage_validation(self):
        assignments = load_current_catalog(self.root)["assignments"]
        assignments["tools"].append(copy.deepcopy(assignments["tools"][0]))
        assignments["tools"][1]["capabilities"] = ["unknown_capability"]
        self.write(ASSIGNMENTS, assignments)
        errors = validate_current_catalog(self.root)
        self.assertTrue(any(x.startswith("Duplicate tool assignment:") for x in errors))
        self.assertTrue(any("unknown IDs" in x for x in errors))

    def test_stale_assignment_for_removed_definition_is_an_error(self):
        assignments = load_current_catalog(self.root)["assignments"]
        extra = copy.deepcopy(assignments["tools"][0])
        extra["name"] = "removed_query"
        assignments["tools"].append(extra)
        self.write(ASSIGNMENTS, assignments)
        self.assertIn("Assignment has no current tool definition: removed_query",
                      validate_current_catalog(self.root))

    def test_duplicate_definition_and_invalid_provenance_rejected_before_write(self):
        duplicate = copy.deepcopy(self.snapshot)
        duplicate["tools"][1] = copy.deepcopy(duplicate["tools"][0])
        with self.assertRaisesRegex(CatalogError, "Duplicate tool definition"):
            normalize_snapshot(duplicate)
        invalid = copy.deepcopy(self.snapshot)
        invalid["source"]["server"] = "other"
        with self.assertRaisesRegex(CatalogError, "provenance"):
            normalize_snapshot(invalid)

    def test_malformed_file_returns_validation_errors_not_traceback(self):
        broken = copy.deepcopy(self.snapshot)
        broken["tools"] = None
        self.write(DEFINITIONS, broken)
        self.assertIn("Current definitions.tools must be a list", validate_current_catalog(self.root))
        (self.root / DEFINITIONS).write_text("not json")
        self.assertTrue(validate_current_catalog(self.root)[0].startswith("Cannot read"))

    def test_invalid_schema_shapes_are_reported_without_crashing_or_writing(self):
        original = (self.root / DEFINITIONS).read_bytes()
        for bad_schema in (None, [], {"required": [{}]}, {"required": "ds"},
                           {"properties": []}, {"properties": {"ds": None}},
                           {"type": None}, {"type": {}}, {"type": ["object", {}]}, {"type": []}):
            with self.subTest(schema=bad_schema):
                snapshot = copy.deepcopy(self.snapshot)
                snapshot["tools"][0]["inputSchema"] = bad_schema
                with self.assertRaisesRegex(CatalogError, "inputSchema"):
                    import_snapshot(self.root, snapshot)
                self.assertEqual((self.root / DEFINITIONS).read_bytes(), original)
        with self.assertRaisesRegex(CatalogError, "Capabilities"):
            build_tool_context(self.root, [{}])

    def test_import_custom_output_does_not_replace_current_or_assignments(self):
        previous = {p: (self.root / p).read_bytes() for p in (DEFINITIONS, ASSIGNMENTS)}
        result = import_snapshot(self.root, self.append_new_tool(), "review/metadata.json")
        self.assertFalse(result["assignments_updated"])
        self.assertEqual(json.loads((self.root / "review/metadata.json").read_text())["tool_count"], 4)
        self.assertTrue(all((self.root / p).read_bytes() == value for p, value in previous.items()))

    def test_historical_snapshots_cannot_be_overwritten(self):
        for protected in ("catalog/tool-routing.json", "catalog/live-tool-schemas.json"):
            self.write(protected, {"historical": True})
            before = (self.root / protected).read_bytes()
            with self.assertRaisesRegex(CatalogError, "Historical"):
                import_snapshot(self.root, self.snapshot, protected)
            self.assertEqual((self.root / protected).read_bytes(), before)

    def test_cli_validates_and_rejects_partial_diff(self):
        script = Path(__file__).with_name("tool_catalog.py")
        result = subprocess.run([sys.executable, str(script), "--root", str(self.root), "validate"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(json.loads(result.stdout)["passed"])
        page = copy.deepcopy(self.snapshot)
        page["source"].pop("catalog_complete")
        self.write("page.json", page)
        result = subprocess.run([sys.executable, str(script), "--root", str(self.root), "diff",
                                 "--input", str(self.root / "page.json")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("completeness", json.loads(result.stdout)["error"])


if __name__ == "__main__":
    unittest.main()
