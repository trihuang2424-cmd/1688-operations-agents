#!/usr/bin/env python3
"""Resolve task-stage reads from the routing catalog; never call business tools.

The catalog is the dependency authority. This module returns original document
text, not model summaries, and treats unknown phases/conditions as errors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
PHASES = {"plan", "execute", "monitor", "evaluate", "receipt"}
DELIVERABLES = {"evidence", "plan", "asset", "execution"}
DEFAULT_DELIVERABLES = {"plan": "plan", "execute": "execution", "monitor": "evidence",
                        "evaluate": "plan", "receipt": "evidence"}
ACQUISITION_SECTION = "references/acquisition-analysis.md"
ACQUISITION_AUTOMATIC_STAGES = {
    (route, phase) for route in ("daily_metrics", "period_analysis")
    for phase in ("plan", "execute", "evaluate")
} | {
    ("traffic_and_ads", phase) for phase in ("plan", "execute", "monitor", "evaluate")
} | {
    (route, phase) for route in ("weekly_review", "monthly_review")
    for phase in ("plan", "evaluate")
}
REQUIRED_COMPLETION_CONTRACTS = ACQUISITION_AUTOMATIC_STAGES | {
    (route, phase) for route in ("product_diagnosis", "product_images",
                                "title_optimization", "product_change")
    for phase in ("plan", "execute")
}
REQUIRED_HANDOFFS = {
    ("traffic_and_ads", phase): {"inspect_product_expression", "prepare_image_trial_asset",
                                "prepare_title_asset", "prepare_detail_asset"}
    for phase in ("plan", "execute", "monitor", "evaluate")
}
REQUIRED_HANDOFFS.update({
    ("product_diagnosis", phase): {"prepare_selected_image_asset", "prepare_title_asset",
                                  "prepare_detail_asset"} for phase in ("plan", "execute")
})
REQUIRED_HANDOFFS.update({
    ("product_images", "plan"): {"produce_reviewable_image"},
    ("product_images", "execute"): {"apply_approved_image"},
    ("title_optimization", "plan"): {"apply_approved_copy"},
    ("title_optimization", "execute"): {"apply_approved_copy"},
    ("product_change", "plan"): {"apply_approved_copy"},
})
DECISION_SECTION = "references/sales-growth-workflow.md#决策与阶段交付"
CONTENT_APPLICATION_SECTION = "references/sales-growth-workflow.md#成品审核与应用"
ROLES = {"director", "executor"}
CATALOG = "catalog/task-routing.json"


class ContextError(ValueError):
    """A missing or ambiguous dependency must be resolved before proceeding."""


def unique(values):
    return list(dict.fromkeys(values))


def load_catalog(root=ROOT):
    try:
        return json.loads((Path(root) / CATALOG).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ContextError(f"Cannot read routing catalog: {exc}") from exc


def resolve_reference(root, reference):
    """Accept only existing relative files inside the actual project root."""
    if not isinstance(reference, str) or not reference.strip():
        raise ContextError("Document reference must be a nonempty string")
    raw_path, separator, anchor = reference.partition("#")
    raw_path, anchor = unquote(raw_path), unquote(anchor)
    if separator and not anchor:
        raise ContextError(f"Empty section anchor: {reference}")
    if "\x00" in raw_path or "\\" in raw_path or "://" in raw_path:
        raise ContextError(f"Invalid document path: {reference}")
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ContextError(f"Path must stay inside the project: {reference}")
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ContextError(f"Missing file or path outside the project: {reference}")
    # Full business rules cannot accidentally become a convenient excerpt.
    if anchor and (relative.name == "RULES.md" or relative.parts[0] == "source"):
        raise ContextError(f"Business rules and source documents require full reads: {reference}")
    return path, anchor


def heading_slug(title):
    title = re.sub(r"[`*_~]", "", title).lower()
    title = re.sub(r"[^\w\s\-\u4e00-\u9fff]", "", title)
    return re.sub(r"\s+", "-", title.strip())


def markdown_section(content, anchor, reference="document"):
    """Return the original complete ATX section, including its subsections.

    Fenced examples do not create headings. Exact titles and ordinary markdown
    slugs are accepted; ambiguous headings deliberately fail instead of guessing.
    """
    lines = content.splitlines(keepends=True)
    headings = []
    fence = None
    for index, line in enumerate(lines):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1]:
                if not line[marker.end():].strip():
                    fence = None
            continue
        if fence:
            continue
        found = re.match(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*\r?\n?$", line)
        if found:
            title = re.sub(r"[ \t]+#+[ \t]*$", "", found.group(2)).strip()
            headings.append((index, len(found.group(1)), title))
    matches = [(i, row) for i, row in enumerate(headings)
               if anchor == row[2] or anchor == heading_slug(row[2])]
    if not matches:
        raise ContextError(f"Missing section anchor: {reference}#{anchor}")
    if len(matches) != 1:
        raise ContextError(f"Ambiguous section anchor: {reference}#{anchor}")
    position, (start, level, _) = matches[0]
    end = next((row[0] for row in headings[position + 1:] if row[1] <= level), len(lines))
    return "".join(lines[start:end])


def read_reference(root, reference):
    path, anchor = resolve_reference(root, reference)
    try:
        # read_bytes().decode preserves the original line endings.
        content = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ContextError(f"Cannot read UTF-8 document {reference}: {exc}") from exc
    return markdown_section(content, anchor, reference.split("#")[0]) if anchor else content


def _descriptor(root, reference):
    path, _ = resolve_reference(root, reference)
    text = read_reference(root, reference)
    return {"reference": reference, "bytes": len(text.encode("utf-8")),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _expand_rules(loading, rules):
    sources, condition_names, followups = [], [], []
    for rule in unique(rules):
        if rule not in loading["rule_sources"]:
            raise ContextError(f"Missing source-loading entry for full rule: {rule}")
        item = loading["rule_sources"][rule]
        sources += item.get("read", [])
        condition_names += item.get("conditional", [])
        followups += [{"rule": rule, **row} for row in item.get("on_demand", [])]
    return unique(sources), unique(condition_names), followups


def _condition_additions(loading, names):
    reads, rules, sources = [], [], []
    for name in names:
        condition = loading["conditions"][name]
        reads += condition.get("read", [])
        rules += condition.get("rules", [])
        sources += condition.get("source_read", [])
    expanded, _, _ = _expand_rules(loading, rules)
    return unique(reads + rules + sources + expanded), unique(rules)


def _completion_context(stage, phase, deliverable, active, role):
    """Describe requested output and candidate handoffs, never grant scope or dispatch."""
    contract = stage.get("completion_contract")
    default = contract["default_deliverable"] if contract else DEFAULT_DELIVERABLES[phase]
    selected = default if deliverable is None else deliverable
    if selected not in DELIVERABLES:
        raise ContextError(f"Unknown deliverable {selected!r}")
    supported = contract["deliverables"] if contract else {default: {"requirements": []}}
    if selected not in supported:
        raise ContextError(f"Deliverable {selected!r} is not declared for this route/phase; "
                           + "supported: " + ", ".join(supported))
    definition = supported[selected]
    required = definition.get("required_conditions", [])
    missing = [name for name in required if name not in active]
    if role == "executor" and missing:
        raise ContextError("Deliverable requires explicit --condition: " + ", ".join(missing))
    handoffs = []
    for handoff in stage.get("conditional_handoffs", []):
        status = "candidate_only" if selected == "evidence" or selected not in handoff["from_deliverables"] else "pending_scope_check"
        handoffs.append({**handoff, "activation_status": status})
    return {
        "deliverable_type": selected,
        "scope_origin": "default" if deliverable is None else "explicit",
        "scope_note": "交付类型只声明本轮输出；默认值、显式选择和候选交接均不证明用户授权，也不启动任务。",
        "completion_contract": {"declared": contract is not None,
                                "requirements": definition["requirements"],
                                "required_conditions": required},
        "unresolved_deliverable_conditions": missing,
        "conditional_handoffs": handoffs,
    }


def build_context(root, route_id, phase, role, conditions=(), catalog=None, deliverable=None):
    catalog = catalog if catalog is not None else load_catalog(root)
    loading = catalog.get("context_loading", {})
    if phase not in PHASES:
        raise ContextError(f"Unknown phase {phase!r}; choose one of {', '.join(sorted(PHASES))}")
    if role not in ROLES:
        raise ContextError(f"Unknown role {role!r}; choose director or executor")
    matches = [row for row in catalog.get("routes", []) if row.get("id") == route_id]
    if len(matches) != 1:
        raise ContextError(f"Unknown or duplicate route: {route_id}")
    route = matches[0]
    if phase not in route.get("phase_loading", {}):
        raise ContextError(f"Route {route_id} does not support phase {phase}; supported: "
                           + ", ".join(route.get("phase_loading", {})))
    stage = route["phase_loading"][phase]
    requested = unique(conditions)
    allowed = unique(stage.get("conditions", []) + stage.get("automatic_conditions", []))
    # Source-specific conditions are made available only for this route's
    # possible full rules, never by searching/loading all business documents.
    possible_rules = list(stage["rules"])
    for extra_rules in stage.get("condition_rules", {}).values():
        possible_rules += extra_rules
    for name in allowed:
        possible_rules += loading["conditions"][name].get("rules", [])
    _, source_conditions, _ = _expand_rules(loading, possible_rules)
    allowed = unique(allowed + source_conditions)
    for name in requested:
        if name not in allowed:
            raise ContextError(f"Condition {name!r} is not supported by {route_id}/{phase}; "
                               + "allowed: " + ", ".join(allowed))
    active = unique(stage.get("automatic_conditions", []) + requested)
    completion = _completion_context(stage, phase, deliverable, active, role)
    missing = [group for group in stage.get("required_any_conditions", [])
               if not set(group).intersection(active)]
    for requirement in stage.get("condition_requirements", []):
        if set(requirement["when_any"]).intersection(active):
            if not set(requirement["require_any"]).intersection(active):
                missing.append(requirement["require_any"])
    for name in active:
        group = loading["conditions"][name].get("requires_any_conditions", [])
        if group and not set(group).intersection(active):
            missing.append(group)
    if role == "executor" and missing:
        raise ContextError("Task scope must be explicit before loading/executing; add --condition: "
                           + "; ".join(" or ".join(group) for group in missing))
    reads = list(loading[f"{role}_read"]) + list(stage[f"{role}_read"])
    selected_rules, followups = [], []
    if role == "executor":
        selected_rules = list(stage["rules"])
        for name in active:
            selected_rules += stage.get("condition_rules", {}).get(name, [])
        additions, condition_rules = _condition_additions(loading, active)
        selected_rules = unique(selected_rules + condition_rules)
        sources, extra_conditions, followups = _expand_rules(loading, selected_rules)
        reads += selected_rules + list(stage.get("source_read", [])) + sources + additions
        allowed = unique(allowed + extra_conditions)
    else:
        # Coordination carries applicable safety/authorization boundaries but
        # never makes the director preload domain skills or business rules.
        for name in active:
            reads += [ref for ref in loading["conditions"][name].get("read", [])
                      if ref.startswith("references/") and "/business-rules/" not in ref]
    reads = unique(reads)
    # If the whole document is needed, do not also return a duplicate excerpt.
    full_files = {ref for ref in reads if "#" not in ref}
    reads = [ref for ref in reads if "#" not in ref or ref.split("#")[0] not in full_files]
    documents = [_descriptor(root, ref) for ref in reads]
    conditional = []
    for name in allowed:
        if name in active:
            continue
        definition = loading["conditions"][name]
        item = {"condition": name, "when": definition["when"]}
        if role == "executor":
            more, _ = _condition_additions(loading, [name])
            extra_rules = stage.get("condition_rules", {}).get(name, [])
            extra_sources, _, _ = _expand_rules(loading, extra_rules)
            more = unique(more + extra_rules + extra_sources)
            item["read"] = [ref for ref in more if ref not in reads]
            for ref in item["read"]:
                read_reference(root, ref)
        else:
            item["executor_condition"] = name
        if definition.get("requires_any_conditions"):
            item["requires_any_conditions"] = definition["requires_any_conditions"]
        conditional.append(item)
    return {
        "version": catalog["version"], "route": {key: route[key] for key in
            ("id", "intent", "owner", "capability", "delegation_policy", "executor") if key in route},
        "phase": phase, "phase_meaning": loading["phases"][phase], "role": role,
        "active_conditions": active, "read": reads, "documents": documents,
        "rules": selected_rules, "conditional_read": conditional,
        "required_any_conditions": stage.get("required_any_conditions", []),
        "unresolved_conditions": missing, "source_followups": followups,
        "condition_policy": loading["condition_policy"], "source_policy": loading["source_policy"],
        "task_packet": "另附目标、店铺/对象、实际周期/截止、证据路径、现行策略、已有行动及授权；清单不证明已读、已委派或已执行业务。",
        **completion,
    }


def validate_loading_contract(root, catalog=None):
    """Validate all stages/conditions and original-reference paths offline.

    This supplements, and does not replace, validate_package's existing source,
    archived-entry and preserved-rule SHA checks.
    """
    errors = []
    catalog = catalog if catalog is not None else load_catalog(root)
    loading = catalog.get("context_loading")
    if not isinstance(loading, dict):
        return ["Missing context_loading contract"]
    def fail(message):
        errors.append(message)
    def references(values, label, full_rules=False):
        if not isinstance(values, list) or any(not isinstance(ref, str) for ref in values):
            fail(f"Invalid reference list: {label}")
            return
        for ref in values:
            if full_rules and (not ref.startswith("references/business-rules/") or not ref.endswith("/RULES.md")):
                fail(f"Full business-rule path required: {label}: {ref}")
            try:
                read_reference(root, ref)
            except ContextError as exc:
                fail(f"{label}: {exc}")
    if loading.get("schema_version") != 1:
        fail("Unsupported context-loading schema version")
    if set(loading.get("phases", {})) != PHASES:
        fail("Context-loading phases must define plan/execute/monitor/evaluate/receipt")
    if set(loading.get("roles", {})) != ROLES:
        fail("Context-loading roles must define director/executor")
    references(loading.get("director_read"), "director_read")
    references(loading.get("executor_read"), "executor_read")
    definitions = loading.get("conditions", {})
    source_index = loading.get("rule_sources", {})
    registered_rules = {rule for route in catalog.get("routes", []) for rule in route.get("rules", [])}
    if set(source_index) != registered_rules:
        fail("Full source-loading index must cover exactly the registered preserved business rules")
    for name, definition in definitions.items():
        if not definition.get("when"):
            fail(f"Missing condition trigger: {name}")
        for key in ("read", "rules", "source_read"):
            references(definition.get(key), f"condition {name}.{key}", key == "rules")
        for rule in definition.get("rules", []):
            if rule not in source_index:
                fail(f"Condition {name} has unindexed full rule: {rule}")
        if any(item not in definitions for item in definition.get("requires_any_conditions", [])):
            fail(f"Unknown prerequisite condition: {name}")
    for rule, entry in source_index.items():
        references([rule], "source index rule", True)
        references(entry.get("read"), f"sources of {rule}")
        if any(name not in definitions for name in entry.get("conditional", [])):
            fail(f"Unknown source condition: {rule}")
        for row in entry.get("on_demand", []):
            if not row.get("when"):
                fail(f"Missing source-specific trigger: {rule}")
            references(row.get("read"), f"source followup of {rule}")
        # Retain discoverability of every source referenced by the preserved
        # rule, even when a fine-grained source is conditional rather than eager.
        accounted = set(entry.get("read", []))
        for name in entry.get("conditional", []):
            definition = definitions.get(name, {})
            accounted.update(definition.get("source_read", []))
            for selected in definition.get("rules", []):
                accounted.update(source_index.get(selected, {}).get("read", []))
        for row in entry.get("on_demand", []):
            accounted.update(row.get("read", []))
        try:
            original = read_reference(root, rule)
            project = Path(root).resolve()
            for target in re.findall(r"\]\(([^)]+)\)", original):
                path = (project / Path(rule).parent / target.split("#")[0]).resolve()
                if path.is_relative_to(project / "source") and path.is_file():
                    source = str(path.relative_to(project))
                    if source not in accounted:
                        fail(f"Referenced source missing from loading index: {rule}: {source}")
        except ContextError:
            pass  # Already reported by references([rule], ...).
    route_map = {route["id"]: route for route in catalog.get("routes", [])}
    for route in route_map.values():
        stages = route.get("phase_loading", {})
        if not stages or set(stages) - PHASES:
            fail(f"Missing or unsupported phase loading: {route['id']}")
        for phase, stage in stages.items():
            label = route["id"] + "/" + phase
            contract = stage.get("completion_contract")
            if (route["id"], phase) in REQUIRED_COMPLETION_CONTRACTS:
                if contract is None:
                    fail(f"Missing mandatory completion contract: {label}")
                if DECISION_SECTION not in stage.get("executor_read", []):
                    fail(f"Missing decision and deliverable workflow: {label}")
                if CONTENT_APPLICATION_SECTION not in stage.get("executor_read", []):
                    fail(f"Missing reviewable content and application workflow: {label}")
            if (route["id"], phase) in ACQUISITION_AUTOMATIC_STAGES:
                if "acquisition_analysis" not in stage.get("automatic_conditions", []):
                    fail(f"Acquisition analysis policy must be automatic: {label}")
            if contract is not None:
                if not isinstance(contract, dict):
                    fail(f"Invalid completion contract: {label}")
                else:
                    deliveries = contract.get("deliverables", {})
                    if not isinstance(deliveries, dict) or not deliveries or set(deliveries) - DELIVERABLES:
                        fail(f"Invalid deliverable types: {label}")
                        deliveries = {}
                    default_delivery = contract.get("default_deliverable")
                    if not isinstance(default_delivery, str) or default_delivery not in deliveries:
                        fail(f"Invalid default deliverable: {label}")
                    for delivery, definition in deliveries.items():
                        if not isinstance(definition, dict):
                            fail(f"Invalid deliverable definition: {label}/{delivery}")
                            continue
                        requirements = definition.get("requirements")
                        if not isinstance(requirements, list) or not requirements or any(not isinstance(x, str) or not x.strip() for x in requirements):
                            fail(f"Missing deliverable completion requirements: {label}/{delivery}")
                        required = definition.get("required_conditions", [])
                        available_conditions = stage.get("conditions", []) + stage.get("automatic_conditions", [])
                        if not isinstance(required, list) or any(not isinstance(x, str) or x not in available_conditions for x in required):
                            fail(f"Invalid deliverable conditions: {label}/{delivery}")
                    if route["id"] == "product_images" and phase == "execute":
                        if not {"asset", "execution"}.issubset(deliveries):
                            fail(f"Images must separate asset and execution deliverables: {label}")
                        application = deliveries.get("execution", {})
                        application_conditions = application.get("required_conditions", []) if isinstance(application, dict) else []
                        if not isinstance(application_conditions, list) or "apply_images" not in application_conditions:
                            fail(f"Image execution deliverable must require apply_images: {label}")
            handoffs = stage.get("conditional_handoffs", [])
            if not isinstance(handoffs, list):
                fail(f"Invalid conditional handoff list: {label}")
                handoffs = []
            handoff_ids = set()
            for handoff in handoffs:
                if not isinstance(handoff, dict):
                    fail(f"Invalid conditional handoff: {label}")
                    continue
                handoff_id = handoff.get("id")
                if not isinstance(handoff_id, str) or not handoff_id.strip() or handoff_id in handoff_ids:
                    fail(f"Invalid or duplicate conditional handoff id: {label}")
                elif handoff_id:
                    handoff_ids.add(handoff_id)
                if not isinstance(handoff.get("when"), str) or not handoff["when"].strip():
                    fail(f"Missing conditional handoff trigger: {label}")
                deliveries = contract.get("deliverables", {}) if isinstance(contract, dict) else {}
                deliveries = deliveries if isinstance(deliveries, dict) else {}
                origins = handoff.get("from_deliverables")
                if not isinstance(origins, list) or not origins or any(not isinstance(x, str) or x not in deliveries for x in origins):
                    fail(f"Invalid handoff source deliverable: {label}")
                target_route = handoff.get("target_route")
                target = route_map.get(target_route, {}) if isinstance(target_route, str) else {}
                target_phase = handoff.get("target_phase")
                target_stage = target.get("phase_loading", {}).get(target_phase) if isinstance(target_phase, str) else None
                if not target or target_stage is None:
                    fail(f"Unknown conditional handoff target: {label}")
                else:
                    if handoff.get("target_owner") != target.get("owner"):
                        fail(f"Conditional handoff owner mismatch: {label}")
                    target_contract = target_stage.get("completion_contract")
                    allowed_deliverables = target_contract.get("deliverables", {}) if isinstance(target_contract, dict) else {DEFAULT_DELIVERABLES[target_phase]: {}}
                    target_delivery = handoff.get("target_deliverable")
                    if not isinstance(target_delivery, str) or target_delivery not in allowed_deliverables:
                        fail(f"Unsupported conditional handoff deliverable: {label}")
                scope = handoff.get("required_scope")
                if not isinstance(scope, list) or not scope or any(not isinstance(x, str) or not x.strip() for x in scope):
                    fail(f"Missing conditional handoff scope: {label}")
                elif handoff.get("target_deliverable") == "asset" and "asset_preparation" not in scope:
                    fail(f"Asset handoff must require asset preparation scope: {label}")
                elif handoff.get("target_route") == "product_change" and handoff.get("target_deliverable") == "execution" and "product_write" not in scope:
                    fail(f"Product execution handoff must require product write scope: {label}")
                if handoff.get("authorization") != "inherit_only" or handoff.get("automatic_execution") is not False:
                    fail(f"Conditional handoff must not grant authorization or execute automatically: {label}")
                if isinstance(handoff_id, str) and handoff_id in {"apply_approved_copy", "apply_approved_image"}:
                    if not isinstance(scope, list) or "approved_version" not in scope:
                        fail(f"Approved content handoff must retain version scope: {label}")
                    if (target_route != "product_change" or target_phase != "execute"
                            or handoff.get("target_deliverable") != "execution"):
                        fail(f"Approved content must hand off to product application: {label}")
            if not REQUIRED_HANDOFFS.get((route["id"], phase), set()).issubset(handoff_ids):
                fail(f"Missing mandatory conditional handoff: {label}")
            for key in ("director_read", "executor_read", "rules", "source_read"):
                references(stage.get(key), label + "." + key, key == "rules")
            if any("/business-rules/" in ref or ref.startswith("source/") for ref in stage.get("director_read", [])):
                fail(f"Director routing view must not load business rules or sources: {label}")
            if any(rule not in route.get("rules", []) for rule in stage.get("rules", [])):
                fail(f"Stage rule is outside its route's preserved rules: {label}")
            available = set(stage.get("conditions", [])) | set(stage.get("automatic_conditions", []))
            if available - definitions.keys():
                fail(f"Unknown condition in stage: {label}")
            for name, rules in stage.get("condition_rules", {}).items():
                if name not in available:
                    fail(f"Unknown stage-specific rule condition: {label}: {name}")
                references(rules, f"{label}.condition_rules.{name}", True)
                if any(rule not in route.get("rules", []) for rule in rules):
                    fail(f"Conditional stage rule is outside its route: {label}: {name}")
            for group in stage.get("required_any_conditions", []):
                if not group or set(group) - available:
                    fail(f"Invalid required condition group: {label}")
            for requirement in stage.get("condition_requirements", []):
                if not requirement.get("when_any") or not requirement.get("require_any"):
                    fail(f"Invalid conditional scope requirement: {label}")
                elif (set(requirement["when_any"]) | set(requirement["require_any"])) - available:
                    fail(f"Unknown conditional scope requirement: {label}")
            if phase == "execute" and route["id"] in {
                    "daily_operations", "title_optimization", "product_change", "product_images",
                    "new_listing", "traffic_and_ads", "customer_conversion", "buyer_transactions",
                    "distribution", "connections_and_components", "procurement_research"}:
                if "references/execution-protocol.md" not in stage.get("executor_read", []):
                    fail(f"Missing mandatory execution protocol: {label}")
            if route["id"] == "traffic_and_ads" and "ads" not in stage.get("automatic_conditions", []):
                fail(f"Advertising policy must be automatic: {label}")
            if route["id"] == "product_images":
                if "images" not in stage.get("automatic_conditions", []) and "references/runtime.md#默认图片方案" not in stage.get("executor_read", []):
                    fail(f"Default image boundaries must be automatic: {label}")
            if route["id"] in {"product_change", "new_listing"} or (route["id"] == "title_optimization" and phase in {"execute", "receipt"}):
                if "references/runtime.md#商品编辑字段边界" not in stage.get("executor_read", []):
                    fail(f"Missing mandatory product-field boundary: {label}")
    for name, required in {
        "ads": {"references/ad-decision-policy.md", ACQUISITION_SECTION},
        "acquisition_analysis": {ACQUISITION_SECTION},
        "inquiry": {ACQUISITION_SECTION + "#客户身份与成交来源", ACQUISITION_SECTION + "#指标与队列"},
        "crm": {ACQUISITION_SECTION + "#客户身份与成交来源", ACQUISITION_SECTION + "#指标与队列"},
        "data_query": {"references/runtime.md#连接和工具", "references/runtime.md#数据和交接"},
        "images": {"references/runtime.md#默认图片方案", "agents/image-agent/AGENTS.md"},
        "sales_fields": {"references/runtime.md#商品编辑字段边界"},
    }.items():
        if not required.issubset(definitions.get(name, {}).get("read", [])):
            fail(f"Missing mandatory conditional boundary: {name}")
    for name, phase in (("manual_receipt", "receipt"), ("due_evaluation", "evaluate")):
        entry = loading.get("entrypoints", {}).get(name, {})
        route = route_map.get(entry.get("route"), {})
        if entry.get("phase") != phase or phase not in route.get("phase_loading", {}):
            fail(f"Missing explicit operating entrypoint: {name}")
    title = route_map.get("title_optimization", {}).get("phase_loading", {})
    title_rule = "references/business-rules/1688-title-optimizer/RULES.md"
    editor_rule = "references/business-rules/1688-product-editor/RULES.md"
    if title.get("plan", {}).get("rules") != [title_rule]:
        fail("Title planning must load the full title rule without the editor rule")
    if not {title_rule, editor_rule}.issubset(title.get("execute", {}).get("rules", [])):
        fail("Title execution must load both full title and editor rules")
    for route_id in ("daily_operations", "conversion_monitoring"):
        stage = route_map.get(route_id, {}).get("phase_loading", {}).get("monitor", {})
        if stage.get("rules"):
            fail(f"Local monitoring must not preload full business rules: {route_id}")
    return unique(errors)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=["list", "read", "validate"])
    parser.add_argument("reference", nargs="?")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--route")
    parser.add_argument("--phase", choices=sorted(PHASES))
    parser.add_argument("--role", choices=sorted(ROLES))
    parser.add_argument("--condition", action="append", default=[])
    parser.add_argument("--deliverable", choices=sorted(DELIVERABLES),
                        help="Requested output type, not authorization to generate, apply or publish")
    parser.add_argument("--details", action="store_true", help="Include hashes and expanded conditional read lists")
    parser.add_argument("--read", action="store_true", help="Print a short task header and exact selected document text")
    args = parser.parse_args(argv)
    try:
        if args.command and (args.route or args.phase or args.role or args.condition or args.deliverable or args.read or args.details):
            raise ContextError("Do not combine list/read/validate with task-selection options")
        if args.command == "read":
            if not args.reference:
                raise ContextError("read requires a relative file path, optionally #section")
            sys.stdout.write(read_reference(args.root, args.reference))
            return 0
        if args.reference:
            raise ContextError("A document reference is accepted only with the read command")
        catalog = load_catalog(args.root)
        if args.command == "list":
            result = [{"id": row["id"], "owner": row["owner"], "intent": row["intent"],
                       "phases": list(row["phase_loading"])} for row in catalog["routes"]]
        elif args.command == "validate":
            errors = validate_loading_contract(args.root, catalog)
            result = {"valid": not errors, "errors": errors}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if errors else 0
        else:
            if not all((args.route, args.phase, args.role)):
                raise ContextError("Specify --route, --phase and --role explicitly; use list to discover routes")
            result = build_context(args.root, args.route, args.phase, args.role, args.condition, catalog, args.deliverable)
        if args.read:
            print(f"# Context: {args.route} / {args.phase} / {args.role} / version {result['version']}")
            print("# Conditions: " + (", ".join(result["active_conditions"]) or "none"))
            print("# Deliverable: " + result["deliverable_type"] + " / " + result["scope_origin"])
            print("# Completion: " + json.dumps(result["completion_contract"], ensure_ascii=False))
            print("# Scope: " + result["scope_note"])
            if result["conditional_handoffs"]:
                print("# Candidate handoffs (not dispatched): " + json.dumps(result["conditional_handoffs"], ensure_ascii=False))
            if result["unresolved_conditions"]:
                print("# Scope still required: " + json.dumps(result["unresolved_conditions"], ensure_ascii=False))
            for ref in result["read"]:
                print(f"\n===== {ref} =====")
                sys.stdout.write(read_reference(args.root, ref))
                print()
            if result["source_followups"]:
                print("# Source-specific followups (read before the applicable subflow):")
                print(json.dumps(result["source_followups"], ensure_ascii=False, indent=2))
        else:
            if args.command != "list" and not args.details:
                result = {key: value for key, value in result.items()
                          if key not in {"documents", "condition_policy", "source_policy", "task_packet"}}
                result["conditional_read"] = [{key: value for key, value in item.items() if key != "read"}
                                               for item in result["conditional_read"]]
                result["details_hint"] = "Use --details for exact conditional additions and file hashes; use --read for selected original text."
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ContextError, KeyError, TypeError) as exc:
        print(f"task_context: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
