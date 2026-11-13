#!/usr/bin/env python3
"""Offline current-tool metadata, coverage and task candidates.

This module never connects to a gateway, invokes tools, checks shop entitlements,
or switches to an alternative endpoint. The original 205-tool snapshot is input
provenance and is never rewritten here.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shlex
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = "catalog/current-tool-definitions.json"
ASSIGNMENTS = "catalog/tool-assignments.json"
REGISTRY = "catalog/agent-registry.json"
PROTECTED = ("catalog/tool-routing.json", "catalog/live-tool-schemas.json",
             "catalog/2026-10-25-tool-catalog.md")
METADATA_FIELDS = ("name", "description", "inputSchema", "server", "effects", "annotations")


class CatalogError(ValueError):
    """Metadata is missing, incomplete, or inconsistent; no business inference."""


def _read(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CatalogError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CatalogError(f"Expected an object: {path}")
    return data


def load_current_catalog(root=ROOT):
    root = Path(root)
    return {"definitions": _read(root / DEFINITIONS),
            "assignments": _read(root / ASSIGNMENTS),
            "registry": _read(root / REGISTRY)}


def _complete(data):
    source = data.get("source", {})
    return data.get("complete") is True or (
        isinstance(source, dict) and source.get("catalog_complete") is True)


def _definition_errors(data):
    errors = []
    if data.get("schema_version") != 1:
        errors.append("Current tool definitions require schema_version=1")
    try:
        captured = datetime.fromisoformat(str(data.get("captured_at", "")).replace("Z", "+00:00"))
        if captured.tzinfo is None:
            raise ValueError("timezone missing")
    except (ValueError, TypeError):
        errors.append("captured_at must be an ISO8601 timestamp with timezone")
    source = data.get("source")
    if not isinstance(source, dict) or any(source.get(k) != v for k, v in
            (("kind", "live_accio_metadata"), ("server", "accio"), ("toolkit", "ali1688"))):
        errors.append("Current metadata requires live_accio_metadata/accio/ali1688 provenance")
    if not _complete(data):
        errors.append("Catalog completeness must be explicitly declared; a page is not a full catalog")
    rows = data.get("tools")
    if not isinstance(rows, list):
        return errors + ["Current definitions.tools must be a list"]
    if type(data.get("tool_count")) is not int or data["tool_count"] != len(rows):
        errors.append("Current tool_count does not match the number of tool definitions")
    names = []
    for index, row in enumerate(rows):
        label = f"tool[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{label} has no name")
        else:
            names.append(name)
            label = name
        if not isinstance(row.get("description"), str) or not row["description"].strip():
            errors.append(f"{label}: description must be nonempty original metadata")
        schema = row.get("inputSchema")
        if not isinstance(schema, dict):
            errors.append(f"{label}: inputSchema must be an object")
        else:
            schema_types = schema.get("type")
            allowed_types = {"null", "boolean", "object", "array", "number", "integer", "string"}
            if "type" in schema:
                type_list = schema_types if isinstance(schema_types, list) else [schema_types]
                if (not type_list or any(not isinstance(value, str) or value not in allowed_types
                                         for value in type_list)
                        or len(type_list) != len(set(value for value in type_list if isinstance(value, str)))):
                    errors.append(f"{label}: inputSchema.type is not a valid JSON Schema type")
            required = schema.get("required", [])
            if (not isinstance(required, list) or any(not isinstance(x, str) for x in required)
                    or len(required) != len(set(x for x in required if isinstance(x, str)))):
                errors.append(f"{label}: inputSchema.required must contain unique field names")
            if "properties" in schema and not isinstance(schema["properties"], dict):
                errors.append(f"{label}: inputSchema.properties must be an object")
            elif isinstance(schema.get("properties"), dict):
                for field, field_schema in schema["properties"].items():
                    if not isinstance(field_schema, (dict, bool)):
                        errors.append(f"{label}: inputSchema.properties.{field} must be a schema object or boolean")
        if row.get("server") != "accio":
            errors.append(f"{label}: server must be accio")
        if "effects" in row and not isinstance(row["effects"], str):
            errors.append(f"{label}: effects must be text")
        if "annotations" in row and not isinstance(row["annotations"], dict):
            errors.append(f"{label}: annotations must be an object")
    for name, count in Counter(names).items():
        if count > 1:
            errors.append(f"Duplicate tool definition: {name}")
    return errors


def _catalog_errors(bundle):
    definitions, assignments, registry = (bundle[k] for k in ("definitions", "assignments", "registry"))
    errors = _definition_errors(definitions)
    skills = registry.get("skills", [])
    roles = registry.get("agents", [])
    skills = skills if isinstance(skills, list) else []
    roles = roles if isinstance(roles, list) else []
    capability_owners = {r["id"]: r.get("owner") for r in skills
                         if isinstance(r, dict) and isinstance(r.get("id"), str)}
    owners = {r["id"] for r in roles if isinstance(r, dict) and isinstance(r.get("id"), str)}
    if not capability_owners or not owners:
        errors.append("Registry must declare capabilities and core agents")
    rows = assignments.get("tools")
    if assignments.get("schema_version") != 1 or not isinstance(rows, list):
        return errors + ["Tool assignments require schema_version=1 and tools list"]
    assigned_names = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not row["name"].strip():
            errors.append("Every assignment must name one tool")
            continue
        name = row["name"]
        assigned_names.append(name)
        status, caps, owner = row.get("review_status"), row.get("capabilities"), row.get("owner")
        if status not in ("reviewed", "unassigned"):
            errors.append(f"{name}: review_status must be reviewed or unassigned")
        if not isinstance(row.get("basis"), str) or not row["basis"].strip():
            errors.append(f"{name}: assignment basis is missing")
        if not isinstance(caps, list) or any(not isinstance(x, str) for x in caps):
            errors.append(f"{name}: capabilities must be a list of registered capability IDs")
            continue
        if len(caps) != len(set(caps)) or set(caps) - set(capability_owners):
            errors.append(f"{name}: capabilities contain duplicate or unknown IDs")
        if status == "reviewed":
            if (not caps or not isinstance(owner, str) or owner not in owners
                    or owner not in {capability_owners.get(x) for x in caps}):
                errors.append(f"{name}: reviewed assignment needs registered capabilities and a matching owner")
        elif owner is not None and (not isinstance(owner, str) or owner not in owners):
            errors.append(f"{name}: unassigned owner must be null or a registered core agent")
    for name, count in Counter(assigned_names).items():
        if count > 1:
            errors.append(f"Duplicate tool assignment: {name}")
    definition_rows = definitions.get("tools", [])
    definition_rows = definition_rows if isinstance(definition_rows, list) else []
    names = {r["name"] for r in definition_rows
             if isinstance(r, dict) and isinstance(r.get("name"), str)}
    for name in sorted(names - set(assigned_names)):
        errors.append(f"Missing assignment (use explicit unassigned): {name}")
    for name in sorted(set(assigned_names) - names):
        errors.append(f"Assignment has no current tool definition: {name}")
    return errors


def validate_current_catalog(root=ROOT):
    try:
        return _catalog_errors(load_current_catalog(root))
    except CatalogError as exc:
        return [str(exc)]


def build_tool_context(root, capabilities, profile=None):
    """Return relevant definitions, never availability or an executable fallback.

    An explicit profile narrows candidates to its groups. Without a profile,
    reviewed capability assignments select candidates. Unassigned tools remain
    visible as a separate gap, never silently promoted to reviewed candidates.
    """
    bundle = load_current_catalog(root)
    errors = _catalog_errors(bundle)
    if errors:
        raise CatalogError("; ".join(errors))
    if isinstance(capabilities, str):
        capabilities = [capabilities]
    if capabilities is not None and (not isinstance(capabilities, (list, tuple, set))
                                    or any(not isinstance(cap, str) for cap in capabilities)):
        raise CatalogError("Capabilities must contain registered capability IDs")
    caps = set(capabilities or [])
    registry = {r["id"]: r for r in bundle["registry"]["skills"]}
    if caps - set(registry):
        raise CatalogError("Unknown capabilities: " + ", ".join(sorted(caps - set(registry))))
    definitions = bundle["definitions"]
    tools = {r["name"]: r for r in definitions["tools"]}
    assignment = {r["name"]: r for r in bundle["assignments"]["tools"]}
    groups = []
    if profile is not None:
        if not isinstance(profile, dict) or not isinstance(profile.get("groups"), list):
            raise CatalogError("Tool profile must contain groups")
        for group in profile["groups"]:
            if (not isinstance(group, dict) or not isinstance(group.get("id"), str)
                    or not isinstance(group.get("tools"), list)
                    or any(not isinstance(n, str) for n in group["tools"])):
                raise CatalogError("Each tool group requires an id and tool names")
            groups.append({k: copy.deepcopy(group[k]) for k in
                           ("id", "purpose", "tools", "selection_note") if k in group})
        names = list(dict.fromkeys(n for g in groups for n in g["tools"]))
    else:
        names = sorted(n for n, a in assignment.items()
                       if a["review_status"] == "reviewed" and caps.intersection(a["capabilities"]))
    indexes = {r["name"]: i for i, r in enumerate(definitions["tools"])}
    candidates = []
    for name in names:
        if name not in tools:
            continue
        tool, planned = tools[name], assignment[name]
        candidates.append({"name": name, "description": tool["description"],
                           "effects": tool.get("effects", "unclassified/potential_changes"),
                           "annotations": copy.deepcopy(tool.get("annotations", {})),
                           "required": copy.deepcopy(tool["inputSchema"].get("required", [])),
                           "schema_ref": f"{DEFINITIONS}#/tools/{indexes[name]}/inputSchema",
                           "planning": {k: copy.deepcopy(planned.get(k)) for k in
                                        ("owner", "capabilities", "review_status", "basis")}})
    unassigned = sorted(n for n, a in assignment.items() if a["review_status"] == "unassigned")
    additional = sorted(n for n, a in assignment.items() if n not in names
                        and a["review_status"] == "reviewed" and caps.intersection(a["capabilities"]))
    discovery = ("python3 scripts/tool_catalog.py --root " + shlex.quote(str(Path(root).resolve()))
                 + " list" + "".join(" --capability " + shlex.quote(cap) for cap in sorted(caps)))
    return {"catalog": {"path": DEFINITIONS, "captured_at": definitions["captured_at"],
                        "source": copy.deepcopy(definitions["source"]), "tool_count": definitions["tool_count"],
                        "freshness": "metadata_snapshot_requires_live_describe"},
            "capability_map": [{"capability": cap, "owner": registry[cap]["owner"],
                                "display_name": registry[cap].get("display_name", cap),
                                "skill": registry[cap].get("skill"),
                                "tool_count": sum(a["review_status"] == "reviewed" and
                                                  cap in a["capabilities"] for a in assignment.values())}
                               for cap in sorted(registry)],
            "candidates": candidates, "groups": groups,
            "additional_capability_tools": {"count": len(additional), "names": additional,
                                            "discovery_command": discovery},
            "unassigned": {"count": len(unassigned), "names": unassigned},
            "missing_profile_tools": [n for n in names if n not in tools],
            "live_describe_required": True, "automatic_fallback": False,
            "permission_status": "not_inferred_from_catalog"}


def normalize_snapshot(snapshot):
    """Import only complete metadata, retaining original descriptions and schemas."""
    if not isinstance(snapshot, dict):
        raise CatalogError("Input metadata must be an object")
    result = {"schema_version": snapshot.get("schema_version", 1),
              "captured_at": snapshot.get("captured_at"),
              "source": copy.deepcopy(snapshot.get("source", {})),
              "tool_count": snapshot.get("tool_count"), "tools": []}
    if _complete(snapshot) and isinstance(result["source"], dict):
        result["source"]["catalog_complete"] = True
    if not isinstance(snapshot.get("tools"), list):
        raise CatalogError("Input tools must be a complete metadata list")
    for row in snapshot["tools"]:
        result["tools"].append({k: copy.deepcopy(row[k]) for k in METADATA_FIELDS if k in row}
                               if isinstance(row, dict) else row)
    errors = _definition_errors(result)
    if errors:
        raise CatalogError("; ".join(errors))
    result["tools"].sort(key=lambda row: row["name"])
    return result


def catalog_diff(before, after):
    """A missing name is a removal only in an explicitly complete new snapshot."""
    after = normalize_snapshot(after)
    previous = {r["name"]: r for r in before.get("tools", [])} if before else {}
    current = {r["name"]: r for r in after["tools"]}
    changed = []
    for name in sorted(set(previous) & set(current)):
        fields = [k for k in METADATA_FIELDS if previous[name].get(k) != current[name].get(k)]
        if fields:
            changed.append({"name": name, "fields": fields})
    return {"added": sorted(set(current) - set(previous)),
            "removed": sorted(set(previous) - set(current)), "changed": changed,
            "unchanged_count": len(set(previous) & set(current)) - len(changed),
            "before_count": len(previous), "after_count": len(current),
            "complete_snapshot": True}


def _write_json_files(updates):
    """Stage local files first; restore prior bytes if replacing a pair fails."""
    staged, originals, replaced = [], {}, []
    try:
        for path, data in updates:
            path.parent.mkdir(parents=True, exist_ok=True)
            originals[path] = path.read_bytes() if path.exists() else None
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                             prefix=".tool-catalog-", delete=False) as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                staged.append((Path(handle.name), path))
        for temporary, path in staged:
            os.replace(temporary, path)
            replaced.append(path)
    except Exception:
        for path in replaced:
            if originals[path] is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(originals[path])
        raise
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def import_snapshot(root, snapshot, output=None):
    """Persist metadata; new/changed definitions require planning review.

    A custom output produces a reviewable metadata file only. Importing to the
    canonical path also reconciles assignments, explicitly marking new or
    changed tools unassigned instead of assuming permissions or responsibilities.
    """
    root = Path(root).resolve()
    target = Path(output) if output is not None else root / DEFINITIONS
    if not target.is_absolute():
        target = root / target
    if target.resolve() in {(root / p).resolve() for p in PROTECTED}:
        raise CatalogError("Historical source snapshots cannot be overwritten")
    current = normalize_snapshot(snapshot)
    before = _read(root / DEFINITIONS) if (root / DEFINITIONS).exists() else None
    diff = catalog_diff(before, current)
    updates = [(target, current)]
    if target.resolve() == (root / DEFINITIONS).resolve():
        previous = _read(root / ASSIGNMENTS) if (root / ASSIGNMENTS).exists() else {"tools": []}
        prior = {r["name"]: r for r in previous.get("tools", []) if isinstance(r, dict) and "name" in r}
        changed = {row["name"] for row in diff["changed"]}
        assignments = []
        for tool in current["tools"]:
            name = tool["name"]
            if name in prior and name not in changed:
                assignments.append(copy.deepcopy(prior[name]))
            else:
                assignments.append({"name": name, "capabilities": [], "owner": None,
                                    "review_status": "unassigned",
                                    "basis": "Current definition changed; planning review required."
                                    if name in changed else "New current metadata; planning review required."})
        assignment_data = {"schema_version": 1, "tools": assignments}
        errors = _catalog_errors({"definitions": current, "assignments": assignment_data,
                                  "registry": _read(root / REGISTRY)})
        if errors:
            raise CatalogError("; ".join(errors))
        updates.append((root / ASSIGNMENTS, assignment_data))
    _write_json_files(updates)
    return {"output": str(target), "diff": diff,
            "assignments_updated": len(updates) == 2, "business_calls": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import", help="Import an explicitly complete local metadata snapshot")
    imp.add_argument("--input", required=True, type=Path)
    imp.add_argument("--output", type=Path)
    diff = sub.add_parser("diff", help="Compare a complete local snapshot with the current catalog")
    diff.add_argument("--input", required=True, type=Path)
    sub.add_parser("validate", help="Check definitions, assignments and registry coverage offline")
    listing = sub.add_parser("list", help="List task candidates without accessing business tools")
    listing.add_argument("--capability", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == "import":
            result = import_snapshot(args.root, _read(args.input), args.output)
        elif args.command == "diff":
            existing = _read(args.root / DEFINITIONS) if (args.root / DEFINITIONS).exists() else None
            result = catalog_diff(existing, _read(args.input))
        elif args.command == "validate":
            errors = validate_current_catalog(args.root)
            result = {"passed": not errors, "errors": errors, "offline_only": True}
        else:
            result = build_tool_context(args.root, args.capability)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if args.command == "validate" and result["errors"] else 0
    except (CatalogError, OSError) as exc:
        print(json.dumps({"error": str(exc), "offline_only": True}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
