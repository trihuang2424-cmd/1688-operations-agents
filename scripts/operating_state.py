#!/usr/bin/env python3
"""Local operating ledger: derived queries and explicit empty initialization only."""
import argparse
from collections import Counter
from datetime import date, datetime, time
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
ZONE = ZoneInfo("Asia/Shanghai")
DEFAULT_STATE = "reports/operating-state/current.json"
DEFAULT_STRATEGY = "references/account-strategies/songtai-sales-growth.md"
TERMINAL = {"completed", "cancelled"}
MANUAL_REVIEW = {"awaiting_approval", "awaiting_manual_review"}
MANUAL_EXECUTION = {"awaiting_manual_execution"}
MANUAL_VERIFICATION = {"awaiting_manual_verification"}
ACTION_STATUSES = TERMINAL | MANUAL_REVIEW | MANUAL_EXECUTION | MANUAL_VERIFICATION | {
    "analysis_pending", "preparing_assets", "plan_ready", "awaiting_execution", "executing",
    "awaiting_verification", "observing", "evaluating", "blocked", "failed",
    "unknown", "insufficient_evidence"}
AD_STATUSES = {"draft", "awaiting_approval", "awaiting_execution", "awaiting_verification",
               "active", "paused", "ended", "unknown", "cancelled"}
REF_KEYS = {"evidence_refs", "receipt_refs", "readback_refs", "activation_evidence_refs",
            "creative_and_landing_refs", "authorization_ref", "company_instruction_ref",
            "company_exit_decision_ref", "artifact_refs", "check_evidence_refs", "basis_refs", "delivery_receipt_refs"}
DELIVERABLE_TYPES = {"evidence", "plan", "asset", "execution"}
PREPARATION_TYPES = {"evidence", "plan", "image", "video", "audio", "copy", "other"}
ASSET_TYPES = PREPARATION_TYPES - {"evidence", "plan"}
EXECUTION_STATES = {"awaiting_execution", "awaiting_manual_execution", "executing",
                    "awaiting_verification", "awaiting_manual_verification", "observing", "evaluating", "completed"}
REVIEW_FIELDS = "review_id store_ref strategy_version review_type period baseline trend_period data_cutoff retrieved_at coverage_and_comparability metric_comparisons sales_contributions bottleneck_conclusions confounders_and_unknowns prioritized_links action_ids evidence_refs"
ACTION_FIELDS = "action_id store_ref strategy_version review_id issue_ref focus_id product_id_or_draft_ref owner executor objective_and_hypothesis status plan manual_handoff execution fixed_baseline observation evaluation_history next_step related_action_ids ad_plan"
FOCUS_FIELDS = "focus_id store_ref company_instruction_ref product_ids_or_draft_refs objective started_at owner status next_weekly_review_at next_monthly_review_at next_ad_daily_check_at action_ids ad_plan_refs company_exit_decision_ref"
AD_FIELDS = "plan_ref version product_ids objective channel_and_targeting creative_and_landing_refs starts_at ends_at daily_budget total_budget_cap currency authorization_ref metric_and_attribution_basis fixed_baseline_ref maturity_and_evaluation_conditions budget_pacing_and_intervention_conditions execution_mode executor review_owner actual_plan_id activation_evidence_refs daily_checks status next_daily_check_at"


class StateError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise StateError("JSON 重复字段: " + key)
        result[key] = value
    return result


def read_json(path):
    def reject_constant(value):
        raise StateError("非有限 JSON: " + value)
    try:
        raw = path.read_bytes()
        data = json.loads(raw, object_pairs_hook=reject_duplicates, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateError(str(path) + ": " + str(exc)) from exc
    return data, hashlib.sha256(raw).hexdigest()


def require(obj, keys, path):
    if not isinstance(obj, dict):
        raise StateError(path + " 必须是对象")
    keys = keys.split() if isinstance(keys, str) else keys
    missing = sorted(set(keys) - set(obj))
    if missing:
        raise StateError(path + " 缺字段: " + ", ".join(missing))


def string(value, path, nullable=False):
    if value is None and nullable:
        return
    if not isinstance(value, str) or not value.strip():
        raise StateError(path + " 必须是非空字符串" + ("或 null" if nullable else ""))


def version(value, path):
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value).strip():
        raise StateError(path + " 必须是版本字符串或整数")


def array(value, path, strings=False, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise StateError(path + " 必须是" + ("非空" if nonempty else "") + "数组")
    if strings:
        for index, item in enumerate(value):
            string(item, f"{path}[{index}]")
        if len(value) != len(set(value)):
            raise StateError(path + " 不得含重复引用")


def instant(value, path="时间", allow_date=False):
    string(value, path)
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            if not allow_date:
                raise ValueError("须带时间和时区")
            return datetime.combine(date.fromisoformat(value), time.min, ZONE)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or "T" not in value:
            raise ValueError("须带时区和 T 分隔符")
        return parsed.astimezone(ZONE)
    except ValueError as exc:
        raise StateError(path + " 不是有效时间: " + value) from exc


def maybe_time(value, path, allow_date=False):
    return instant(value, path, allow_date) if value is not None else None


def period(value, path, nullable=False):
    if value is None and nullable:
        return
    require(value, "start end", path)
    try:
        start, end = date.fromisoformat(value["start"]), date.fromisoformat(value["end"])
    except (ValueError, TypeError) as exc:
        raise StateError(path + " 的 start/end 必须是 YYYY-MM-DD") from exc
    if start > end or value.get("timezone", "Asia/Shanghai") != "Asia/Shanghai":
        raise StateError(path + " 起止顺序或时区错误")


def gap(gaps, code, path, message):
    gaps.append({"code": code, "path": path, "message": message})


def local_path(reference, root):
    path = Path(reference).expanduser()
    return path if path.is_absolute() else root / path


def source_metadata(reference, root):
    result = {"reference": reference, "path": str(local_path(reference, root)),
              "exists": False, "strategy_id": None, "version": None, "sha256": None,
              "verification_scope": "仅本地文件来源核对，不证明业务授权或实际执行"}
    try:
        content = local_path(reference, root).read_bytes()
        text = content.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        result["error"] = str(exc)
        return result
    result.update(exists=True, sha256=hashlib.sha256(content).hexdigest())
    for key, pattern in (("strategy_id", r"策略ID[：:]\s*([^；;\s]+)"),
                         ("version", r"版本[：:]\s*([^；;\s]+)")):
        match = re.search(pattern, text)
        if match:
            result[key] = match.group(1)
    return result


def strategy_check(strategy, root, gaps):
    require(strategy, "strategy_id version reference sha256", "strategy")
    for key in ("strategy_id", "reference", "sha256"):
        string(strategy[key], "strategy." + key)
    version(strategy["version"], "strategy.version")
    if not re.fullmatch(r"[0-9a-f]{64}", strategy["sha256"]):
        raise StateError("strategy.sha256 必须是文件字节 SHA256 的64位小写十六进制")
    source = source_metadata(strategy["reference"], root)
    status = "verified"
    if not source["exists"]:
        status = "missing"
        gap(gaps, "strategy_source_missing", "strategy.reference", "策略来源无法读取，须核对原文")
    elif source["sha256"] != strategy["sha256"]:
        status = "mismatch"
        gap(gaps, "strategy_digest_mismatch", "strategy.sha256", "策略文件已变化或摘要不符，先读原文并核对版本")
    for key in ("strategy_id", "version"):
        if source[key] is None:
            gap(gaps, "strategy_metadata_unparsed", "strategy." + key, "来源未解析出" + key + "，需人工核对")
            if status == "verified":
                status = "needs_manual_verification"
        elif str(strategy[key]) != source[key]:
            status = "mismatch"
            gap(gaps, "strategy_" + key + "_mismatch", "strategy." + key, "账本与来源的" + key + "不符")
    return {"registered": strategy, "source": source, "status": status}


def collect_refs(value):
    refs = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in REF_KEYS:
                candidates = item if isinstance(item, list) else [item]
                refs.update(v for v in candidates if isinstance(v, str) and v.strip())
            refs.update(collect_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.update(collect_refs(item))
    return refs


def evidence_paths(refs, root, gaps):
    result = []
    for ref in sorted(refs):
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", ref):
            result.append({"reference": ref, "status": "external_not_checked"})
            gap(gaps, "external_evidence_not_checked", ref, "外部证据仅保留引用，本地未验证内容")
            continue
        path = local_path(ref.split("#", 1)[0], root)
        present = path.is_file()
        result.append({"reference": ref, "path": str(path), "status": "present" if present else "missing"})
        if not present:
            gap(gaps, "evidence_file_missing", ref, "证据路径不存在或不是文件，不能据引用声称已核验")
    return result


def validate_workflow(record, path):
    """Optional contract: legacy actions keep their original meaning and validation."""
    if "workflow" not in record:
        return
    workflow = record["workflow"]
    wp = path + ".workflow"
    require(workflow, "version deliverable_type decision preparation approval delivered_at delivery_receipt_refs", wp)
    if type(workflow["version"]) is not int or workflow["version"] != 1:
        raise StateError(wp + ".version 不支持；不自动迁移")
    if workflow["deliverable_type"] not in DELIVERABLE_TYPES:
        raise StateError(wp + ".deliverable_type 无效")
    maybe_time(workflow["delivered_at"], wp + ".delivered_at")
    array(workflow["delivery_receipt_refs"], wp + ".delivery_receipt_refs", strings=True)
    if workflow["delivered_at"] and not workflow["delivery_receipt_refs"]:
        raise StateError(wp + " 已交付时间须有真实交付回执引用")
    if workflow["deliverable_type"] == "execution" and (workflow["delivered_at"] or workflow["delivery_receipt_refs"]):
        raise StateError(wp + " 执行交付继续使用既有生效/回执/核验，不用本轮资料交付字段绕过")
    decision = workflow["decision"]
    require(decision, "choice basis evidence_refs key_unknowns investigation", wp + ".decision")
    for key in ("choice", "basis"):
        string(decision[key], wp + ".decision." + key, nullable=True)
    for key in ("evidence_refs", "key_unknowns"):
        array(decision[key], wp + ".decision." + key, strings=True)
    investigation = decision["investigation"]
    require(investigation, "status blocking stop_conditions stop_at", wp + ".decision.investigation")
    if investigation["status"] not in {"not_required", "in_progress", "stopped", "exhausted"}:
        raise StateError(wp + ".decision.investigation.status 无效")
    if not isinstance(investigation["blocking"], bool):
        raise StateError(wp + ".decision.investigation.blocking 必须是布尔值")
    array(investigation["stop_conditions"], wp + ".decision.investigation.stop_conditions", strings=True)
    maybe_time(investigation["stop_at"], wp + ".decision.investigation.stop_at", allow_date=True)
    preparation = workflow["preparation"]
    require(preparation, "required required_types due_at deliverables", wp + ".preparation")
    if not isinstance(preparation["required"], bool):
        raise StateError(wp + ".preparation.required 必须是布尔值")
    maybe_time(preparation["due_at"], wp + ".preparation.due_at", allow_date=True)
    array(preparation["required_types"], wp + ".preparation.required_types", strings=True)
    if any(item not in PREPARATION_TYPES for item in preparation["required_types"]):
        raise StateError(wp + ".preparation.required_types 含无效产物类型")
    array(preparation["deliverables"], wp + ".preparation.deliverables")
    for index, item in enumerate(preparation["deliverables"]):
        ip = f"{wp}.preparation.deliverables[{index}]"
        require(item, "type artifact_refs check_status check_evidence_refs", ip)
        if item["type"] not in PREPARATION_TYPES or item["check_status"] not in {"pending", "passed", "failed"}:
            raise StateError(ip + " 产物类型或检查状态无效")
        for key in ("artifact_refs", "check_evidence_refs"):
            array(item[key], ip + "." + key, strings=True)
    approval = workflow["approval"]
    require(approval, "type necessary_basis basis_refs review_objects status authorization_ref", wp + ".approval")
    if approval["type"] not in {"none", "plan_review", "asset_review", "execution_authorization"}:
        raise StateError(wp + ".approval.type 无效")
    if approval["status"] not in {"not_required", "pending", "approved", "rejected", "covered"}:
        raise StateError(wp + ".approval.status 无效")
    for key in ("necessary_basis", "authorization_ref"):
        string(approval[key], wp + ".approval." + key, nullable=True)
    array(approval["basis_refs"], wp + ".approval.basis_refs", strings=True)
    array(approval["review_objects"], wp + ".approval.review_objects")
    for index, item in enumerate(approval["review_objects"]):
        ip = f"{wp}.approval.review_objects[{index}]"
        require(item, "type artifact_refs", ip)
        if item["type"] not in PREPARATION_TYPES:
            raise StateError(ip + ".type 无效")
        array(item["artifact_refs"], ip + ".artifact_refs", strings=True)
    if approval["type"] == "none" and approval["status"] != "not_required":
        raise StateError(wp + " 无需审核时不能制造待审核状态")
    if approval["type"] != "none" and approval["status"] == "not_required":
        raise StateError(wp + " 审核类型与无需审核状态矛盾")
    if record["status"] in MANUAL_REVIEW and (approval["type"] == "none" or approval["status"] != "pending"):
        raise StateError(wp + " 待审核行动必须有实际待审核事项，既有授权不再次请求")
    if approval["type"] == "execution_authorization" and workflow["deliverable_type"] != "execution":
        raise StateError(wp + " 非执行交付不能扩展为发布或业务执行授权")
    if workflow["deliverable_type"] != "execution" and (record["status"] in EXECUTION_STATES or record["execution"]["effective_at"] is not None):
        raise StateError(wp + " 非执行交付用 plan_ready 和 check 表达交付就绪，不登记远端执行或生效")


def reference_check(reference, root, artifact_type=None):
    """Basic local presence/type checks, never a content-quality or authority verdict."""
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", reference):
        return {"reference": reference, "status": "external_pending_verification"}
    path = local_path(reference.split("#", 1)[0], root)
    if not path.is_file():
        return {"reference": reference, "status": "missing"}
    if artifact_type == "image":
        suffix = path.suffix.lower()
        try:
            with path.open("rb") as handle:
                header = handle.read(512)
        except OSError:
            return {"reference": reference, "status": "unreadable"}
        signatures = {
            ".png": header.startswith(b"\x89PNG\r\n\x1a\n"),
            ".jpg": header.startswith(b"\xff\xd8\xff"), ".jpeg": header.startswith(b"\xff\xd8\xff"),
            ".gif": header.startswith((b"GIF87a", b"GIF89a")),
            ".webp": header.startswith(b"RIFF") and header[8:12] == b"WEBP",
            ".bmp": header.startswith(b"BM"),
            ".tif": header.startswith((b"II*\x00", b"MM\x00*")),
            ".tiff": header.startswith((b"II*\x00", b"MM\x00*")),
            ".avif": header[4:8] == b"ftyp" and b"avif" in header[8:32],
            ".svg": b"<svg" in header.lower(),
        }
        if not signatures.get(suffix, False):
            return {"reference": reference, "status": "artifact_type_mismatch"}
    return {"reference": reference, "status": "present"}


def workflow_readiness(record, root):
    scope = "仅核对本地字段、文件存在/基础类型和已登记检查证据；不证明内容质量、授权有效性或远端实际状态，不授予业务权限"
    if "workflow" not in record:
        return {"contract": "legacy_unknown", "stage_ready": False, "delivery_ready": False,
                "handoff_ready": False, "execution_ready": False, "closure_ready": False,
                "delivery_closed": False,
                "user_action_required": False, "blockers": ["legacy_workflow_not_recorded"], "verification_scope": scope}
    workflow = record["workflow"]
    decision, preparation, approval = (workflow[key] for key in ("decision", "preparation", "approval"))
    blockers, checks, checked_objects = [], [], set()
    def refs_ready(refs, artifact_type=None):
        results = [reference_check(ref, root, artifact_type) for ref in refs]
        checks.extend(results)
        return bool(refs) and all(item["status"] == "present" for item in results)
    investigation = decision["investigation"]
    decision_ready = bool(decision["choice"] and decision["basis"]) and refs_ready(decision["evidence_refs"])
    if not decision_ready:
        blockers.append("decision_basis_not_ready")
    if investigation["status"] == "in_progress" and (not investigation["stop_conditions"] or not investigation["stop_at"]):
        blockers.append("investigation_stop_condition_missing")
        decision_ready = False
    if investigation["blocking"]:
        blockers.append("blocking_unknowns_unresolved")
        decision_ready = False
    item_readiness = []
    for index, item in enumerate(preparation["deliverables"]):
        artifacts_ready = refs_ready(item["artifact_refs"], item["type"])
        evidence_ready = refs_ready(item["check_evidence_refs"])
        ready = item["check_status"] == "passed" and artifacts_ready and evidence_ready
        item_readiness.append({"index": index, "type": item["type"], "ready": ready})
        if ready:
            checked_objects.update((item["type"], ref) for ref in item["artifact_refs"])
        else:
            blockers.append("deliverable_not_checked:" + str(index))
    ready_types = {item["type"] for item in item_readiness if item["ready"]}
    required_types = set(preparation["required_types"])
    expected_types_ready = required_types <= ready_types
    if workflow["deliverable_type"] == "asset" and not required_types:
        expected_types_ready = False
        blockers.append("required_asset_types_not_recorded")
    if not expected_types_ready:
        blockers.append("required_deliverable_types_not_ready")
    preparation_ready = (not preparation["required"] or bool(item_readiness)) and all(item["ready"] for item in item_readiness) and expected_types_ready
    if not preparation_ready:
        blockers.append("preparation_not_ready")
    objects = approval["review_objects"]
    object_types = {item["type"] for item in objects}
    objects_ready = bool(objects) and all(item["artifact_refs"] and all((item["type"], ref) in checked_objects for ref in item["artifact_refs"]) for item in objects)
    if approval["type"] == "plan_review":
        objects_ready = objects_ready and "plan" in object_types
    elif approval["type"] == "asset_review":
        objects_ready = objects_ready and bool(object_types & ASSET_TYPES)
    elif approval["type"] == "execution_authorization":
        objects_ready = objects_ready and "plan" in object_types
    approval_basis_ready = bool(approval["necessary_basis"]) and refs_ready(approval["basis_refs"]) if approval["type"] != "none" else True
    review_preparation_ready = approval["type"] == "plan_review" or preparation_ready
    if approval["type"] == "asset_review":
        objects_ready = objects_ready and bool(required_types & ASSET_TYPES) and (required_types & ASSET_TYPES) <= object_types
    can_request_review = decision_ready and approval_basis_ready and objects_ready and review_preparation_ready and approval["status"] == "pending"
    if approval["type"] != "none" and not approval_basis_ready:
        blockers.append("approval_necessity_not_evidenced")
    if approval["type"] != "none" and not objects_ready:
        blockers.append("review_objects_not_ready")
    authorization_ready = refs_ready([approval["authorization_ref"]]) if approval["authorization_ref"] else False
    approval_clear = approval["type"] == "none" or (approval["status"] in {"approved", "covered"} and authorization_ready and approval_basis_ready and objects_ready)
    if not approval_clear:
        blockers.append("approval_not_cleared")
    business_authorization = refs_ready([record["plan"]["authorization_ref"]]) if record["plan"]["authorization_ref"] else False
    responsibility_ready = all(record[key] for key in ("owner", "executor", "objective_and_hypothesis", "next_step"))
    execution_ready = (workflow["deliverable_type"] == "execution" and decision_ready and preparation_ready and approval_clear
                       and business_authorization and responsibility_ready and bool(record["plan"]["changes"] and record["plan"]["steps"]))
    if workflow["deliverable_type"] == "execution":
        if not business_authorization:
            blockers.append("business_authorization_not_recorded_or_verified")
        if not responsibility_ready:
            blockers.append("execution_responsibility_or_next_step_missing")
        if not record["plan"]["changes"] or not record["plan"]["steps"]:
            blockers.append("execution_plan_incomplete")
    target_types = {"evidence": {"evidence"}, "plan": {"plan"}, "asset": ASSET_TYPES}.get(workflow["deliverable_type"], set())
    output_ready = any(item["ready"] and item["type"] in target_types for item in item_readiness)
    if workflow["deliverable_type"] != "execution" and not output_ready:
        blockers.append("requested_delivery_not_ready")
    executed = bool(record["execution"]["effective_at"] and record["execution"]["receipt_refs"])
    execution_evidence_ready = executed and refs_ready(record["execution"]["receipt_refs"])
    verification_refs = record["execution"]["readback_refs"]
    if not verification_refs:
        confirmation = record["execution"].get("effect_verification") or {}
        verification_refs = confirmation.get("evidence_refs", []) if confirmation.get("status") == "confirmed" else []
    verified_execution = execution_evidence_ready and refs_ready(verification_refs)
    if workflow["deliverable_type"] == "execution" and not verified_execution:
        blockers.append("execution_or_readback_not_confirmed")
    delivery_ready = (execution_ready and verified_execution if workflow["deliverable_type"] == "execution"
                      else decision_ready and preparation_ready and output_ready and approval_clear)
    handoff_ready = can_request_review if approval["status"] == "pending" else delivery_ready
    closure_ready = delivery_ready
    if workflow["deliverable_type"] == "execution":
        closure_ready = delivery_ready and record["status"] in {"observing", "evaluating", "completed"}
    if workflow["deliverable_type"] == "execution" and record["status"] in {"observing", "evaluating"}:
        observation = record["observation"]
        closure_ready = delivery_ready and all(observation[key] for key in ("start", "end", "evaluate_at", "latest_reconsider_at", "primary_metrics", "sample_and_maturity_basis"))
        if not closure_ready:
            blockers.append("observation_handoff_not_ready")
    status = record["status"]
    if status in {"unknown", "blocked", "failed"}:
        delivery_ready = handoff_ready = closure_ready = execution_ready = can_request_review = False
        blockers.append("result_or_blocker_requires_reconciliation")
    if status == "cancelled":
        closure_ready = decision_ready and refs_ready(record.get("cancellation", {}).get("evidence_refs", []))
    delivery_closed = bool(workflow["deliverable_type"] != "execution" and delivery_ready and workflow["delivered_at"]
                           and refs_ready(workflow["delivery_receipt_refs"]))
    if status in MANUAL_REVIEW:
        stage_ready = can_request_review
    elif status in {"awaiting_execution", "awaiting_manual_execution", "executing"}:
        stage_ready = execution_ready
    elif status in {"observing", "evaluating", "completed", "cancelled"}:
        stage_ready = closure_ready
    elif status == "plan_ready":
        stage_ready = can_request_review or (decision_ready and preparation_ready and (execution_ready or delivery_ready))
    else:
        stage_ready = False
    return {"contract": "workflow_v1", "deliverable_type": workflow["deliverable_type"],
            "decision_ready": decision_ready, "preparation_ready": preparation_ready,
            "required_types": sorted(required_types), "required_types_ready": expected_types_ready,
            "delivery_ready": delivery_ready, "handoff_ready": handoff_ready,
            "can_request_review": can_request_review, "execution_ready": execution_ready,
            "closure_ready": closure_ready, "stage_ready": stage_ready,
            "delivery_closed": delivery_closed,
            "user_action_required": bool(status in MANUAL_REVIEW and can_request_review),
            "blockers": list(dict.fromkeys(blockers)), "deliverables": item_readiness,
            "reference_checks": checks, "verification_scope": scope}


def contextual_readiness(action, index, data, strategy, gaps, root):
    """Use the same action checks in cards and check; unrelated gaps stay warnings."""
    readiness = workflow_readiness(action, root)
    blocking_gaps = []
    if action.get("workflow", {}).get("deliverable_type") == "execution":
        if strategy["status"] != "verified":
            blocking_gaps.append({"code": "execution_strategy_not_verified", "path": "strategy", "message": "现行策略来源核对未通过，不能认定新措施可执行"})
        if str(action["strategy_version"]) != str(data["strategy"]["version"]):
            blocking_gaps.append({"code": "execution_action_strategy_differs", "path": action["action_id"], "message": "行动依据与现行策略版本不同，先核对方案"})
        if data["history_reconciliation"]["status"] != "reconciled":
            blocking_gaps.append({"code": "execution_history_not_reconciled", "path": "history_reconciliation", "message": "历史尚未核对，不能据空状态认定新措施可执行"})
        prefix = f"actions[{index}]"
        execution_gap_codes = {"executor_missing", "action_context_missing", "execution_authorization_missing",
                               "manual_handoff_gap", "manual_plan_incomplete", "observation_conditions_missing",
                               "fixed_baseline_missing", "fixed_baseline_metrics_missing", "active_ad_plan_gap"}
        blocking_gaps.extend(item for item in gaps if item["path"].startswith(prefix + ".") and item["code"] in execution_gap_codes)
        if blocking_gaps:
            for flag in ("execution_ready", "delivery_ready", "closure_ready"):
                readiness[flag] = False
            if action["status"] in EXECUTION_STATES:
                readiness["stage_ready"] = False
            if action["workflow"]["approval"]["type"] == "execution_authorization":
                for flag in ("handoff_ready", "can_request_review", "user_action_required"):
                    readiness[flag] = False
            readiness["blockers"].extend(item["code"] for item in blocking_gaps)
    readiness["blocking_gaps"] = blocking_gaps
    return readiness


def validate_review(record, path, gaps):
    require(record, REVIEW_FIELDS, path)
    version(record["strategy_version"], path + ".strategy_version")
    if record["review_type"] not in {"weekly", "monthly", "special"}:
        raise StateError(path + ".review_type 无效")
    period(record["period"], path + ".period")
    period(record["baseline"], path + ".baseline")
    require(record["baseline"], "basis evidence_refs", path + ".baseline")
    string(record["baseline"]["basis"], path + ".baseline.basis", nullable=True)
    array(record["baseline"]["evidence_refs"], path + ".baseline.evidence_refs", strings=True)
    period(record["trend_period"], path + ".trend_period", nullable=True)
    for key in ("data_cutoff", "retrieved_at"):
        maybe_time(record[key], path + "." + key)
        if record[key] is None:
            gap(gaps, "review_time_missing", path + "." + key, "诊断时间/数据截止待核实")
    for key in ("metric_comparisons", "sales_contributions", "bottleneck_conclusions",
                "confounders_and_unknowns", "prioritized_links", "action_ids", "evidence_refs"):
        array(record[key], path + "." + key, strings=key in {"action_ids", "evidence_refs"})
    if not record["evidence_refs"] or not record["bottleneck_conclusions"] or record["coverage_and_comparability"] is None:
        gap(gaps, "review_evidence_gap", path, "经营结论、可比性或证据不完整；不推定正常")


def validate_ad(plan, path, gaps):
    require(plan, AD_FIELDS, path)
    string(plan["plan_ref"], path + ".plan_ref")
    if plan["version"] is not None:
        version(plan["version"], path + ".version")
    for key in ("objective", "channel_and_targeting", "currency", "authorization_ref",
                "metric_and_attribution_basis", "fixed_baseline_ref", "maturity_and_evaluation_conditions",
                "budget_pacing_and_intervention_conditions", "execution_mode", "executor",
                "review_owner", "actual_plan_id"):
        string(plan[key], path + "." + key, nullable=True)
    if plan["status"] not in AD_STATUSES:
        raise StateError(path + ".status 无效")
    for key in ("product_ids", "creative_and_landing_refs", "activation_evidence_refs"):
        array(plan[key], path + "." + key, strings=True)
    for key in ("starts_at", "ends_at", "next_daily_check_at"):
        maybe_time(plan[key], path + "." + key, allow_date=key == "next_daily_check_at")
    if plan["starts_at"] and plan["ends_at"] and instant(plan["starts_at"]) > instant(plan["ends_at"]):
        raise StateError(path + " 投流起止顺序错误")
    for key in ("daily_budget", "total_budget_cap"):
        value = plan[key]
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
            raise StateError(path + "." + key + " 必须是非负有限数或 null")
    array(plan["daily_checks"], path + ".daily_checks")
    last_checked = None
    for index, check in enumerate(plan["daily_checks"]):
        cp = f"{path}.daily_checks[{index}]"
        require(check, "checked_at data_cutoff conclusion evidence_refs", cp)
        checked = instant(check["checked_at"], cp + ".checked_at")
        instant(check["data_cutoff"], cp + ".data_cutoff")
        string(check["conclusion"], cp + ".conclusion")
        array(check["evidence_refs"], cp + ".evidence_refs", strings=True, nonempty=True)
        if last_checked and checked < last_checked:
            raise StateError(cp + " 日检历史须按检查时间排序")
        last_checked = checked
    if plan["status"] == "active":
        string(plan["actual_plan_id"], path + ".actual_plan_id")
        array(plan["activation_evidence_refs"], path + ".activation_evidence_refs", strings=True, nonempty=True)
        for key in AD_FIELDS.split():
            if key not in {"ends_at", "daily_checks"} and (plan[key] is None or plan[key] == [] or plan[key] == ""):
                gap(gaps, "active_ad_plan_gap", path + "." + key, "投流中计划必要依据缺失，先核对")
        if last_checked and plan["next_daily_check_at"] and instant(plan["next_daily_check_at"], allow_date=True) <= last_checked:
            gap(gaps, "ad_schedule_not_advanced", path, "下次日检未晚于已登记检查，须核对排期")


def validate_action(record, path, gaps):
    require(record, ACTION_FIELDS, path)
    version(record["strategy_version"], path + ".strategy_version")
    string(record["product_id_or_draft_ref"], path + ".product_id_or_draft_ref")
    if record["status"] not in ACTION_STATUSES:
        raise StateError(path + ".status 无效")
    for key in ("review_id", "issue_ref", "focus_id", "owner", "executor", "objective_and_hypothesis", "next_step"):
        string(record[key], path + "." + key, nullable=True)
    for key in ("owner", "objective_and_hypothesis"):
        if record[key] is None:
            gap(gaps, "action_context_missing", path + "." + key, "行动负责人或目标待核实")
    if not any(record[key] for key in ("review_id", "issue_ref", "focus_id")):
        gap(gaps, "action_origin_missing", path, "行动未关联经营诊断、问题引用或公司重点依据")
    plan = record["plan"]
    require(plan, "changes steps assets dependencies authorization_ref", path + ".plan")
    for key in ("changes", "steps", "assets", "dependencies"):
        array(plan[key], path + ".plan." + key)
    string(plan["authorization_ref"], path + ".plan.authorization_ref", nullable=True)
    manual = record["manual_handoff"]
    require(manual, "required reason assignee due_at acceptance_and_required_receipt", path + ".manual_handoff")
    if not isinstance(manual["required"], bool):
        raise StateError(path + ".manual_handoff.required 必须是布尔值")
    if record["status"] in MANUAL_EXECUTION | MANUAL_VERIFICATION and not manual["required"]:
        raise StateError(path + " 人工执行/核验状态必须明确 manual_handoff.required=true")
    maybe_time(manual["due_at"], path + ".manual_handoff.due_at", allow_date=True)
    for key in ("reason", "assignee", "acceptance_and_required_receipt"):
        string(manual[key], path + ".manual_handoff." + key, nullable=True)
    manual_pending = MANUAL_REVIEW | MANUAL_EXECUTION | MANUAL_VERIFICATION | {"awaiting_execution", "awaiting_verification"}
    if manual["required"] and record["status"] in manual_pending:
        for key in ("reason", "assignee", "due_at", "acceptance_and_required_receipt"):
            if manual[key] is None:
                gap(gaps, "manual_handoff_gap", path + ".manual_handoff." + key, "人工交接尚有待确认项")
        if not plan["steps"] or not plan["changes"]:
            gap(gaps, "manual_plan_incomplete", path + ".plan", "人工实施步骤或逐字段方案缺失")
    execution = record["execution"]
    require(execution, "effective_at receipt_refs readback_refs display_verification_status", path + ".execution")
    effective = maybe_time(execution["effective_at"], path + ".execution.effective_at")
    for key in ("receipt_refs", "readback_refs"):
        array(execution[key], path + ".execution." + key, strings=True)
    if execution["display_verification_status"] not in {"pending", "verified_by_user", "verified_with_authorization", "not_applicable", "unknown"}:
        raise StateError(path + ".execution.display_verification_status 无效或缺失")
    baseline = record["fixed_baseline"]
    require(baseline, "period metrics evidence_refs", path + ".fixed_baseline")
    period(baseline["period"], path + ".fixed_baseline.period", nullable=True)
    array(baseline["metrics"], path + ".fixed_baseline.metrics")
    array(baseline["evidence_refs"], path + ".fixed_baseline.evidence_refs", strings=True)
    if baseline.get("snapshot_sha256") is not None:
        expected = digest({k: v for k, v in baseline.items() if k != "snapshot_sha256"})
        if baseline["snapshot_sha256"] != expected:
            raise StateError(path + ".fixed_baseline.snapshot_sha256 不符，不能静默滚动重置固定基线")
    observation = record["observation"]
    require(observation, "start end evaluate_at primary_metrics guardrail_metrics sample_and_maturity_basis early_intervention_conditions latest_reconsider_at", path + ".observation")
    times = {key: maybe_time(observation[key], path + ".observation." + key,
                            allow_date=key in {"evaluate_at", "latest_reconsider_at"})
             for key in ("start", "end", "evaluate_at", "latest_reconsider_at")}
    for key in ("primary_metrics", "guardrail_metrics", "early_intervention_conditions"):
        array(observation[key], path + ".observation." + key)
    string(observation["sample_and_maturity_basis"], path + ".observation.sample_and_maturity_basis", nullable=True)
    if times["start"] and times["end"] and times["start"] >= times["end"]:
        raise StateError(path + " 观察起止顺序错误")
    if times["end"] and times["evaluate_at"] and times["evaluate_at"] < times["end"]:
        raise StateError(path + " 评估时间早于观察结束")
    if times["start"] and (not effective or times["start"] < effective):
        raise StateError(path + " 未确认生效或观察起点早于生效时间，不得观察效果")
    if manual["required"] and record["status"] in manual_pending and times["start"]:
        raise StateError(path + " 人工待审核/执行/核验期间观察起点须为空")
    if record["status"] in {"observing", "evaluating"}:
        if not effective or not execution["receipt_refs"] or not times["start"]:
            raise StateError(path + " 观察/评估必须有生效时间、完成回执及观察起点")
        if manual["required"] and not execution["readback_refs"]:
            confirmation = execution.get("effect_verification")
            require(confirmation, "status evidence_refs", path + ".execution.effect_verification")
            if confirmation["status"] != "confirmed":
                raise StateError(path + " 人工生效尚未确认，不能观察")
            array(confirmation["evidence_refs"], path + ".execution.effect_verification.evidence_refs", strings=True, nonempty=True)
        for key in ("end", "evaluate_at", "latest_reconsider_at", "primary_metrics", "sample_and_maturity_basis"):
            if observation[key] is None or observation[key] == []:
                gap(gaps, "observation_conditions_missing", path + ".observation." + key, "有限观察条件缺失，不能无限等待")
        if baseline["period"] is None or not baseline["evidence_refs"]:
            gap(gaps, "fixed_baseline_missing", path + ".fixed_baseline", "行动前固定基线缺失；新品不得伪造零基线增幅")
        elif not baseline["metrics"]:
            gap(gaps, "fixed_baseline_metrics_missing", path + ".fixed_baseline.metrics", "固定基线指标缺失，不能据此比较效果")
        if baseline["period"] and effective and date.fromisoformat(baseline["period"]["end"]) >= effective.date():
            raise StateError(path + " 固定基线必须结束于生效日之前，不得混入改动后数据")
    if effective and not execution["receipt_refs"]:
        raise StateError(path + " 生效时间缺少执行回执")
    if effective and plan["authorization_ref"] is None:
        gap(gaps, "execution_authorization_missing", path, "已登记生效但缺授权引用，须核对既有事实和授权")
    if record["status"] in {"executing", "unknown", "observing", "evaluating"} and record["executor"] is None:
        gap(gaps, "executor_missing", path + ".executor", "执行者未登记，恢复前先核对实际任务")
    array(record["related_action_ids"], path + ".related_action_ids", strings=True)
    array(record["evaluation_history"], path + ".evaluation_history")
    previous = None
    for index, evaluation in enumerate(record["evaluation_history"]):
        ep = f"{path}.evaluation_history[{index}]"
        require(evaluation, "evaluated_at conclusion decision evidence_refs", ep)
        stamp = instant(evaluation["evaluated_at"], ep + ".evaluated_at")
        if previous and stamp < previous:
            raise StateError(ep + " 评估历史须按时间排序")
        previous = stamp
        # A historical evaluation may refer to an earlier, explicitly saved window.
        # Current-window assessments cannot claim a completed observation before its end.
        evaluation_end = (instant(evaluation["observation_end"], ep + ".observation_end")
                          if evaluation.get("observation_end") else times["end"])
        if evaluation_end and stamp < evaluation_end:
            raise StateError(ep + " 评估早于其完整观察窗口结束；提前异常另存，不冒充到期效果评估")
        for key in ("conclusion", "decision"):
            string(evaluation[key], ep + "." + key)
        array(evaluation["evidence_refs"], ep + ".evidence_refs", strings=True, nonempty=True)
        if evaluation.get("scheduled_evaluate_at") is None:
            gap(gaps, "evaluation_original_due_missing", ep, "原评估日期未留存，无法核对延期")
        else:
            instant(evaluation["scheduled_evaluate_at"], ep + ".scheduled_evaluate_at", allow_date=True)
        if evaluation.get("next_evaluate_at") is not None:
            instant(evaluation["next_evaluate_at"], ep + ".next_evaluate_at", allow_date=True)
            string(evaluation.get("extension_reason"), ep + ".extension_reason")
    if record["status"] == "completed":
        if not record["evaluation_history"] or not effective or not execution["receipt_refs"]:
            raise StateError(path + " completed 必须有真实生效/执行回执与验收结论；方案就绪用 plan_ready，决定不做用有据 cancelled")
        if manual["required"] and not execution["readback_refs"]:
            confirmation = execution.get("effect_verification")
            require(confirmation, "status evidence_refs", path + ".execution.effect_verification")
            if confirmation["status"] != "confirmed":
                raise StateError(path + " completed 缺人工生效确认")
            array(confirmation["evidence_refs"], path + ".execution.effect_verification.evidence_refs", strings=True, nonempty=True)
    if record["status"] == "cancelled":
        cancellation = record.get("cancellation")
        require(cancellation, "recorded_at reason evidence_refs", path + ".cancellation")
        instant(cancellation["recorded_at"], path + ".cancellation.recorded_at")
        string(cancellation["reason"], path + ".cancellation.reason")
        array(cancellation["evidence_refs"], path + ".cancellation.evidence_refs", strings=True, nonempty=True)
    for key in ("next_review_at", "data_cutoff"):
        if key in record:
            maybe_time(record[key], path + "." + key, allow_date=key == "next_review_at")
    if record["ad_plan"] is not None:
        validate_ad(record["ad_plan"], path + ".ad_plan", gaps)
    validate_workflow(record, path)


def validate_focus(record, path, gaps):
    require(record, FOCUS_FIELDS, path)
    for key in ("company_instruction_ref", "objective", "owner"):
        string(record[key], path + "." + key)
    instant(record["started_at"], path + ".started_at")
    if record["status"] not in {"active", "paused", "exited"}:
        raise StateError(path + ".status 无效")
    for key in ("product_ids_or_draft_refs", "action_ids", "ad_plan_refs"):
        array(record[key], path + "." + key, strings=True, nonempty=key == "product_ids_or_draft_refs")
    for key in ("next_weekly_review_at", "next_monthly_review_at", "next_ad_daily_check_at"):
        maybe_time(record[key], path + "." + key, allow_date=True)
    if record["status"] == "active":
        for key in ("next_weekly_review_at", "next_monthly_review_at"):
            if record[key] is None:
                gap(gaps, "focus_schedule_missing", path + "." + key, "长期重点缺复查时间，已列入待处理")
    if record["status"] in {"paused", "exited"}:
        string(record["company_exit_decision_ref"], path + ".company_exit_decision_ref")


def validate_ledger(data, root):
    require(data, "schema_version data_mode timezone store_ref strategy history_reconciliation data_cutoff last_conclusion conversion_state_ref reviews actions focus_products", "ledger")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise StateError("不支持该 schema_version；不自动迁移或猜测结构")
    if data["data_mode"] != "operating_ledger" or data["timezone"] != "Asia/Shanghai":
        raise StateError("data_mode 须为 operating_ledger，timezone 须为 Asia/Shanghai；模板不可当真实账本")
    string(data["store_ref"], "store_ref")
    gaps = []
    strategy = strategy_check(data["strategy"], root, gaps)
    history = data["history_reconciliation"]
    require(history, "status reviewed_at evidence_refs outcome unresolved", "history_reconciliation")
    if history["status"] not in {"required", "reconciled"}:
        raise StateError("history_reconciliation.status 无效")
    array(history["evidence_refs"], "history_reconciliation.evidence_refs", strings=True)
    array(history["unresolved"], "history_reconciliation.unresolved", strings=True)
    maybe_time(history["reviewed_at"], "history_reconciliation.reviewed_at")
    if history["status"] == "reconciled":
        instant(history["reviewed_at"], "history_reconciliation.reviewed_at")
        array(history["evidence_refs"], "history_reconciliation.evidence_refs", strings=True, nonempty=True)
        if history["outcome"] not in {"imported", "no_relevant_records"}:
            raise StateError("历史核对结论须为 imported 或 no_relevant_records")
        if history["unresolved"]:
            gap(gaps, "history_unresolved", "history_reconciliation.unresolved", "历史仍有待核对项，相关任务先对账")
    else:
        gap(gaps, "history_reconciliation_required", "history_reconciliation", "未核对历史、既有行动和未知结果；空表不是无任务，不能据此新增派单")
    maybe_time(data["data_cutoff"], "data_cutoff")
    if data["last_conclusion"] is None:
        gap(gaps, "last_conclusion_missing", "last_conclusion", "上次经营结论未登记，需追溯原始报告")
    else:
        conclusion = data["last_conclusion"]
        require(conclusion, "recorded_at summary evidence_refs", "last_conclusion")
        instant(conclusion["recorded_at"], "last_conclusion.recorded_at")
        string(conclusion["summary"], "last_conclusion.summary")
        array(conclusion["evidence_refs"], "last_conclusion.evidence_refs", strings=True, nonempty=True)
    string(data["conversion_state_ref"], "conversion_state_ref", nullable=True)
    for forbidden in ("conversion_issues", "conversion_requests", "conversion_state", "issues", "requests"):
        if forbidden in data:
            raise StateError("不得复制转化状态: " + forbidden + "；只存 conversion_state_ref/issue_ref")
    indices = {}
    for section, id_key, validator in (("reviews", "review_id", validate_review),
                                       ("actions", "action_id", validate_action),
                                       ("focus_products", "focus_id", validate_focus)):
        array(data[section], section)
        indices[section] = {}
        for index, record in enumerate(data[section]):
            path = f"{section}[{index}]"
            validator(record, path, gaps)
            if section == "actions" and "workflow" in record:
                readiness = workflow_readiness(record, root)
                if record["status"] in MANUAL_REVIEW | EXECUTION_STATES | {"plan_ready"} and not readiness["stage_ready"]:
                    gap(gaps, "workflow_stage_not_ready", path + ".workflow", "结构可读但本阶段交付/交接条件未满足；用 check 查看具体条件，不据状态名认定就绪")
                if "investigation_stop_condition_missing" in readiness["blockers"]:
                    gap(gaps, "investigation_stop_condition_missing", path + ".workflow.decision.investigation", "补查须登记停止条件与截止，不无限取证")
            string(record[id_key], path + "." + id_key)
            if record["store_ref"] != data["store_ref"]:
                raise StateError(path + ".store_ref 与账本不一致")
            rid = record[id_key]
            if any(rid in existing for existing in indices.values()):
                raise StateError(path + " 重复或跨表冲突 ID: " + rid)
            indices[section][rid] = record
    if history["status"] == "reconciled" and history["outcome"] == "imported" and not any(indices.values()):
        raise StateError("历史核对为 imported 但三张记录表均为空")
    plans = {}
    for action in data["actions"]:
        aid = action["action_id"]
        if action["status"] not in TERMINAL and str(action["strategy_version"]) != str(data["strategy"]["version"]):
            gap(gaps, "active_action_strategy_differs", aid, "未完成行动依据旧策略，核对继续条件；不重写旧基线或自动重派")
        for key, section in (("review_id", "reviews"), ("focus_id", "focus_products")):
            rid = action[key]
            if rid is not None:
                if rid not in indices[section] or aid not in indices[section][rid]["action_ids"]:
                    raise StateError(aid + "." + key + " 引用不存在或反向 action_ids 关系缺失")
        for rid in action["related_action_ids"]:
            if rid not in indices["actions"] or rid == aid:
                raise StateError(aid + " 的 related_action_ids 无效: " + rid)
        if action["ad_plan"] is not None:
            pid = action["ad_plan"]["plan_ref"]
            if pid in plans:
                raise StateError("ad_plan.plan_ref 重复: " + pid)
            plans[pid] = action["ad_plan"]
    for section, key in (("reviews", "review_id"), ("focus_products", "focus_id")):
        for record in data[section]:
            for aid in record["action_ids"]:
                if aid not in indices["actions"] or indices["actions"][aid][key] != record[key]:
                    raise StateError(record[key] + " 的 action_ids 关系无效: " + aid)
    for focus in data["focus_products"]:
        for pid in focus["ad_plan_refs"]:
            if pid not in plans:
                raise StateError(focus["focus_id"] + " 引用不存在的 ad_plan: " + pid)
        for aid in focus["action_ids"]:
            plan = indices["actions"][aid]["ad_plan"]
            if plan is not None and plan["plan_ref"] not in focus["ad_plan_refs"]:
                raise StateError(focus["focus_id"] + " 缺关联行动的 ad_plan_refs")
    paths = evidence_paths(collect_refs(data), root, gaps)
    readiness = {action["action_id"]: contextual_readiness(action, index, data, strategy, gaps, root)
                 for index, action in enumerate(data["actions"])}
    return {"gaps": gaps, "strategy": strategy, "evidence_paths": paths, "indices": indices, "readiness": readiness}


def freshness(cutoff, at, hours, gaps):
    if cutoff is None:
        gap(gaps, "data_cutoff_missing", "data_cutoff", "数据截止未登记，不能把旧报告视为当前数据")
        return {"cutoff": None, "status": "missing", "age_hours": None, "stale_after_hours": hours}
    age = (at - instant(cutoff)).total_seconds() / 3600
    status = "future_relative_to_query" if age < 0 else "stale" if age > hours else "current"
    if status != "current":
        gap(gaps, "data_cutoff_" + status, "data_cutoff", "截止相对查询时间过旧或位于未来；按所需周期核对，不据此判经营失败")
    return {"cutoff": cutoff, "status": status, "age_hours": round(age, 3), "stale_after_hours": hours}


def action_card(record, root=ROOT, readiness=None):
    keys = ("status", "owner", "strategy_version", "review_id", "focus_id", "issue_ref")
    result = {key: record[key] for key in keys}
    result.update(kind="action", id=record["action_id"], object_ids=[record["product_id_or_draft_ref"]],
                  next_review_at=record.get("next_review_at"),
                  manual_due_at=record["manual_handoff"]["due_at"],
                  evaluate_at=record["observation"]["evaluate_at"],
                  latest_reconsider_at=record["observation"]["latest_reconsider_at"],
                  related_action_count=len(record["related_action_ids"]),
                  ad_plan_ref=record["ad_plan"]["plan_ref"] if record["ad_plan"] else None,
                  evidence_count=len(collect_refs(record)),
                  detail={"command": "object", "id": record["action_id"]})
    readiness = readiness or workflow_readiness(record, root)
    result.update(executor=record["executor"], next_step=excerpt(record["next_step"]) if record["next_step"] else None,
                  readiness={key: readiness[key] for key in ("contract", "stage_ready", "delivery_ready", "handoff_ready", "execution_ready", "closure_ready", "delivery_closed", "user_action_required")})
    if "workflow" in record:
        result.update(deliverable_type=record["workflow"]["deliverable_type"],
                      preparation_ready=readiness["preparation_ready"],
                      investigation_stop_at=record["workflow"]["decision"]["investigation"]["stop_at"],
                      preparation_due_at=record["workflow"]["preparation"]["due_at"])
    evaluation = record["evaluation_history"][-1] if record["evaluation_history"] else None
    result["last_evaluation"] = ({
        "evaluated_at": evaluation["evaluated_at"],
        "conclusion": excerpt(evaluation["conclusion"]),
        "scheduled_evaluate_at": evaluation.get("scheduled_evaluate_at"),
    } if evaluation else None)
    return result


def focus_card(record):
    keys = ("status", "owner", "next_weekly_review_at",
            "next_monthly_review_at", "next_ad_daily_check_at")
    result = {key: record[key] for key in keys}
    result.update(kind="focus", id=record["focus_id"], object_ids=record["product_ids_or_draft_refs"],
                  action_count=len(record["action_ids"]), ad_plan_count=len(record["ad_plan_refs"]),
                  evidence_count=len(collect_refs(record)), detail={"command": "object", "id": record["focus_id"]})
    return result


def excerpt(text, limit=240):
    return {"text": text[:limit], "truncated": len(text) > limit, "characters": len(text)}


def ad_card(action):
    plan = action["ad_plan"]
    return {"kind": "ad_plan", "id": plan["plan_ref"], "action_id": action["action_id"],
            "status": plan["status"], "object_ids": plan["product_ids"], "version": plan["version"],
            "owner": plan["review_owner"], "next_daily_check_at": plan["next_daily_check_at"],
            "last_checked_at": plan["daily_checks"][-1]["checked_at"] if plan["daily_checks"] else None,
            "evidence_count": len(collect_refs(plan)),
            "detail": {"command": "object", "id": action["action_id"]}}


def scan_due(data, at, gaps, root=ROOT, readiness_by_id=None):
    items = []
    def append(card, conditions, immediate=None):
        reasons = list(immediate or [])
        for name, value in conditions:
            if value is not None and instant(value, allow_date=True) <= at:
                reasons.append({"condition": name, "due_at": value})
        if reasons:
            card = dict(card)
            card.update(reasons=reasons, requires_reconciliation=card["status"] == "unknown")
            items.append(card)
    for action in data["actions"]:
        readiness = (readiness_by_id or {}).get(action["action_id"]) or workflow_readiness(action, root)
        delivered = readiness["delivery_closed"] and instant(action["workflow"]["delivered_at"]) <= at
        if action["status"] not in TERMINAL and not delivered:
            conditions = [("next_review_at", action.get("next_review_at"))]
            workflow = action.get("workflow")
            if workflow:
                investigation = workflow["decision"]["investigation"]
                if investigation["status"] == "in_progress":
                    conditions.append(("investigation_stop_at", investigation["stop_at"]))
                if not workflow_readiness(action, root)["preparation_ready"]:
                    conditions.append(("preparation_due_at", workflow["preparation"]["due_at"]))
            if action["status"] in MANUAL_REVIEW | MANUAL_EXECUTION | MANUAL_VERIFICATION | {"awaiting_execution", "awaiting_verification"}:
                conditions.append(("manual_due_at", action["manual_handoff"]["due_at"]))
            if action["status"] in {"observing", "evaluating", "insufficient_evidence"}:
                conditions.extend((key, action["observation"][key]) for key in ("evaluate_at", "latest_reconsider_at"))
            immediate = []
            if action["status"] == "unknown":
                immediate.append({"condition": "unknown_result_reconcile_first", "due_at": None})
            if not any(value for _, value in conditions):
                gap(gaps, "action_schedule_missing", action["action_id"], "未完成行动缺后续日期")
                immediate.append({"condition": "missing_followup_schedule", "due_at": None})
            append(action_card(action, root, (readiness_by_id or {}).get(action["action_id"])), conditions, immediate)
        plan = action["ad_plan"]
        if plan and plan["status"] in {"active", "unknown"}:
            immediate = []
            if plan["status"] == "unknown":
                immediate.append({"condition": "unknown_ad_result_reconcile_first", "due_at": None})
            if not plan["next_daily_check_at"]:
                immediate.append({"condition": "missing_ad_daily_schedule", "due_at": None})
            append(ad_card(action), [("ad_daily_check", plan["next_daily_check_at"])], immediate)
    for focus in data["focus_products"]:
        if focus["status"] == "active":
            conditions = [(key, focus[key]) for key in ("next_weekly_review_at", "next_monthly_review_at", "next_ad_daily_check_at")]
            immediate = [{"condition": "missing_" + key, "due_at": None}
                         for key in ("next_weekly_review_at", "next_monthly_review_at") if focus[key] is None]
            append(focus_card(focus), conditions, immediate)
    items.sort(key=lambda item: (not item["requires_reconciliation"],
                                min((instant(r["due_at"], allow_date=True) for r in item["reasons"] if r["due_at"]),
                                    default=datetime.min.replace(tzinfo=ZONE)), item["kind"], item["id"]))
    return items


def page(items, offset, limit):
    selected = items[offset:offset + limit]
    return {"items": selected, "total": len(items), "offset": offset, "limit": limit,
            "next_offset": offset + len(selected) if offset + len(selected) < len(items) else None}


def conversion_reference(data, root, gaps):
    ref = data["conversion_state_ref"]
    result = {"reference": ref, "status": "not_registered", "owner": "scripts/conversion_state.py",
              "read_separately": True, "instruction": "原模块是转化问题/请求唯一真源。本查询不读取、复制、迁移其内容。另用原模块 summary；日检按原协议 ingest 扫描全部到期。"}
    if ref is None:
        gap(gaps, "conversion_reference_missing", "conversion_state_ref", "转化状态路径未核对，不等于没有转化问题")
    else:
        path = local_path(ref, root)
        result.update(path=str(path), status="referenced" if path.is_file() else "missing")
        if not path.is_file():
            gap(gaps, "conversion_state_missing", "conversion_state_ref", "转化状态文件不存在，须核对原位置/历史")
    return result


def query(data, root, state_path, state_sha256, command="summary", at=None, offset=0, limit=10,
          object_id=None, stale_after_hours=48, gap_offset=0, gap_limit=10, requirement="closure"):
    at = at or datetime.now(ZONE)
    checked = validate_ledger(data, root)
    gaps = checked["gaps"]
    due = scan_due(data, at, gaps, root, checked["readiness"])  # Full validation and scan precede filtering/pagination.
    fresh = freshness(data["data_cutoff"], at, stale_after_hours, gaps)
    conversion = conversion_reference(data, root, gaps)
    history_required = data["history_reconciliation"]["status"] != "reconciled"
    plans = [a["ad_plan"] for a in data["actions"] if a["ad_plan"] is not None]
    unknown_actions = sum(a["status"] == "unknown" for a in data["actions"])
    unknown_plans = sum(p["status"] == "unknown" for p in plans)
    counts = {"reviews": len(data["reviews"]), "actions": len(data["actions"]), "focus_products": len(data["focus_products"]),
              "action_statuses": dict(sorted(Counter(a["status"] for a in data["actions"]).items())),
              "manual_review": sum(a["status"] in MANUAL_REVIEW and ("workflow" not in a or checked["readiness"][a["action_id"]]["user_action_required"]) for a in data["actions"]),
              "preparing_assets": sum(a["status"] == "preparing_assets" for a in data["actions"]),
              "delivered_stages": sum(checked["readiness"][a["action_id"]]["delivery_closed"] for a in data["actions"]),
              "unready_review_handoffs": sum(a["status"] in MANUAL_REVIEW and "workflow" in a and not checked["readiness"][a["action_id"]]["can_request_review"] for a in data["actions"]),
              "manual_execution": sum(a["status"] in MANUAL_EXECUTION or
                                      (a["status"] == "awaiting_execution" and a["manual_handoff"]["required"]) for a in data["actions"]),
              "manual_verification": sum(a["status"] in MANUAL_VERIFICATION or
                                         (a["status"] == "awaiting_verification" and a["manual_handoff"]["required"]) for a in data["actions"]),
              "unknown_results": unknown_actions + unknown_plans, "unknown_action_results": unknown_actions,
              "unknown_ad_results": unknown_plans, "ad_statuses": dict(sorted(Counter(p["status"] for p in plans).items())),
              "active_focus": sum(f["status"] == "active" for f in data["focus_products"]),
              "due_or_unscheduled": len(due), "due_kinds": dict(sorted(Counter(item["kind"] for item in due).items()))}
    base = {"schema_version": 1, "command": command,
            "status": "history_reconciliation_required" if history_required else "needs_attention" if gaps else "ready",
            "initialized": True, "query_at": at.astimezone(ZONE).isoformat(), "timezone": "Asia/Shanghai",
            "state_path": str(state_path), "state_sha256": state_sha256, "derived_only": True,
            "scan_complete": True, "store_ref": data["store_ref"], "strategy": checked["strategy"],
            "data_freshness": fresh,
            "last_conclusion": ({**data["last_conclusion"], "summary": excerpt(data["last_conclusion"]["summary"])}
                                if data["last_conclusion"] else None),
            "history_reconciliation": data["history_reconciliation"], "history_reconciliation_required": history_required,
            "conversion_state": conversion, "counts": counts,
            "gaps": page(gaps, gap_offset, gap_limit),
            "gap_counts": dict(sorted(Counter(item["code"] for item in gaps).items())),
            "dispatch_permitted_by_this_tool": False,
            "recovery_instruction": "先核对所有 unknown 及人工生效回执，再处理到期；查询不派单、不重试业务写入，不把到期解释为失败。"}
    if command == "check":
        if object_id not in checked["indices"]["actions"]:
            raise StateError("check 必须提供现存行动ID --id；不据查询失败认定无任务")
        key = {"stage": "stage_ready", "handoff": "handoff_ready", "delivery": "delivery_ready",
               "execution": "execution_ready", "closure": "closure_ready"}.get(requirement)
        if key is None:
            raise StateError("check 的 --require 无效")
        action = checked["indices"]["actions"][object_id]
        readiness = checked["readiness"][object_id]
        base.update(structurally_valid=True, action_id=object_id, requirement=requirement,
                    readiness=readiness, check_passed=readiness[key],
                    check_status="ready" if readiness[key] else "not_ready", ledger_status=base["status"],
                    check_scope="single_action_local_only", blocking_gaps=readiness["blocking_gaps"])
    elif command == "due":
        base.update(page(due, offset, limit))
    elif command == "object":
        if object_id is None:
            raise StateError("object 必须提供 --id")
        selected = {"actions": set(), "reviews": set(), "focus_products": set()}
        for action in data["actions"]:
            if object_id in {action["action_id"], action["product_id_or_draft_ref"], action["review_id"], action["focus_id"]} or (action["ad_plan"] and object_id == action["ad_plan"]["plan_ref"]):
                selected["actions"].add(action["action_id"])
        for focus in data["focus_products"]:
            if object_id == focus["focus_id"] or object_id in focus["product_ids_or_draft_refs"]:
                selected["focus_products"].add(focus["focus_id"])
                selected["actions"].update(focus["action_ids"])
        if object_id in checked["indices"]["reviews"]:
            selected["reviews"].add(object_id)
        # Expand the connected action set, including same-issue actions and
        # inbound references, so resuming one action cannot hide another.
        changed = True
        while changed:
            before = set(selected["actions"])
            issues = {checked["indices"]["actions"][aid]["issue_ref"] for aid in before}
            issues.discard(None)
            for action in data["actions"]:
                aid = action["action_id"]
                if (aid in before or action["issue_ref"] in issues
                        or any(rid in before for rid in action["related_action_ids"])):
                    selected["actions"].add(aid)
                    selected["actions"].update(action["related_action_ids"])
            changed = before != selected["actions"]
        for aid in selected["actions"]:
            action = checked["indices"]["actions"][aid]
            for section, field in (("reviews", "review_id"), ("focus_products", "focus_id")):
                if action[field]:
                    selected[section].add(action[field])
        records = [{"kind": {"actions": "action", "reviews": "review", "focus_products": "focus"}[section],
                    "id": rid, "record": checked["indices"][section][rid]}
                   for section in ("actions", "focus_products", "reviews") for rid in sorted(selected[section])]
        if not records:
            raise StateError("未找到对象: " + object_id + "；请核对真实ID及历史覆盖，不据此认定无任务")
        selected_ids = set().union(*selected.values())
        related_due = [item for item in due if item["id"] in selected_ids or item.get("action_id") in selected_ids]
        base.update(page(records, offset, limit))
        base.update(object_id=object_id, related_due_total=len(related_due),
                    related_due=page([{"kind": item["kind"], "id": item["id"]} for item in related_due], offset, limit),
                    last_conclusion=data["last_conclusion"])
    elif command == "summary":
        cards = [action_card(a, root, checked["readiness"][a["action_id"]]) for a in data["actions"] if a["status"] not in TERMINAL]
        cards += [focus_card(f) for f in data["focus_products"] if f["status"] != "exited"]
        cards += [ad_card(a) for a in data["actions"] if a["ad_plan"] and a["ad_plan"]["status"] in {"active", "unknown"}]
        priority = {"unknown": 0, "awaiting_manual_verification": 1, "awaiting_verification": 1,
                    "awaiting_manual_review": 2, "awaiting_approval": 2, "awaiting_manual_execution": 3}
        cards.sort(key=lambda c: (c.get("readiness", {}).get("delivery_closed", False), priority.get(c["status"], 4), c["kind"], c["id"]))
        base.update(page(cards, offset, limit))
        base["due"] = page(due, offset, limit)
        base["evidence_paths"] = page(checked["evidence_paths"], offset, limit)
    elif command == "validate":
        base.update(structurally_valid=True, evidence_paths=page(checked["evidence_paths"], offset, limit))
    else:
        raise StateError("未知查询命令")
    return base


def empty_ledger(payload, at):
    require(payload, "store_ref strategy", "init input")
    unknown = set(payload) - {"store_ref", "strategy", "conversion_state_ref"}
    if unknown:
        raise StateError("init 只接受 store_ref/strategy/conversion_state_ref，未知字段: " + ", ".join(sorted(unknown)))
    return {"schema_version": 1, "data_mode": "operating_ledger", "timezone": "Asia/Shanghai",
            "store_ref": payload["store_ref"], "strategy": payload["strategy"], "created_at": at.isoformat(),
            "history_reconciliation": {"status": "required", "reviewed_at": None, "evidence_refs": [], "outcome": None, "unresolved": []},
            "data_cutoff": None, "last_conclusion": None, "conversion_state_ref": payload.get("conversion_state_ref"),
            "reviews": [], "actions": [], "focus_products": []}


def initialize(path, payload, root, at):
    data = empty_ledger(payload, at)
    checked = validate_ledger(data, root)
    if checked["strategy"]["status"] != "verified":
        raise StateError("init 策略引用/版本/文件摘要未核对通过；先核对真实来源")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + ".lock", "a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.exists():
            raise StateError("账本已存在，init 拒绝覆盖: " + str(path))
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                             prefix="." + path.name + ".", suffix=".tmp", delete=False) as handle:
                temporary = handle.name
                json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, path)  # Atomic exclusive publish; never overwrite.
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError as exc:
            raise StateError("初始化原子保存失败: " + str(exc)) from exc
        finally:
            if temporary:
                os.unlink(temporary)
    return data


def missing_state(path, root, at, command):
    return {"status": "uninitialized", "command": command, "initialized": False, "derived_only": True,
            "scan_complete": False, "state_path": str(path), "query_at": at.isoformat(), "timezone": "Asia/Shanghai",
            "history_reconciliation_required": True, "counts": None, "items": None,
            "strategy": {"source": source_metadata(DEFAULT_STRATEGY, root), "status": "source_only_not_reconciled"},
            "data_freshness": {"status": "unknown", "cutoff": None}, "last_conclusion": None,
            "message": "运营账本尚未初始化。先核对历史报告、执行回执、人工待办、未知结果与真实店铺引用；缺账本/空表不表示无任务。",
            "conversion_state": {"reference": None, "read_separately": True, "owner": "scripts/conversion_state.py"},
            "dispatch_permitted_by_this_tool": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help="项目根目录，引用路径以此解析")
    parser.add_argument("--state", default=DEFAULT_STATE, help="单店账本，默认 reports/operating-state/current.json")
    parser.add_argument("--at", help="显式含时区时间戳；默认 Asia/Shanghai 当前时间")
    parser.add_argument("--stale-after-hours", type=float, default=48, help="截止过旧提示阈值，默认48小时，不是经营成败阈值")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("summary", "due", "object", "validate", "check"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--offset", type=int, default=0)
        sub.add_argument("--limit", type=int, default=10)
        sub.add_argument("--gap-offset", type=int, default=0, help="缺口独立分页起点")
        sub.add_argument("--gap-limit", type=int, default=10, help="缺口独立每页条数")
        if command in {"object", "check"}:
            sub.add_argument("--id", required=True)
        if command == "check":
            sub.add_argument("--require", choices=("stage", "handoff", "delivery", "execution", "closure"), default="closure",
                             help="只读就绪检查；默认本次交付收尾，未就绪退出4，不授予业务权限")
    init = subparsers.add_parser("init")
    init.add_argument("--input", required=True, help="真实店铺引用及策略来源；只创建待历史核对空壳")
    args = parser.parse_args(argv)
    try:
        at = instant(args.at, "--at") if args.at else datetime.now(ZONE)
        if not math.isfinite(args.stale_after_hours) or args.stale_after_hours <= 0:
            raise StateError("--stale-after-hours 必须是正有限数")
        root = Path(args.root).expanduser().resolve()
        path = local_path(args.state, root).resolve()
        if args.command != "init" and (args.offset < 0 or args.limit < 1 or args.limit > 1000
                                        or args.gap_offset < 0 or args.gap_limit < 1 or args.gap_limit > 1000):
            raise StateError("--offset/--gap-offset 须非负，--limit/--gap-limit 须为1至1000")
        if args.command == "init":
            payload, _ = read_json(local_path(args.input, root))
            initialize(path, payload, root, at)
            data, state_sha256 = read_json(path)
            result = query(data, root, path, state_sha256, at=at, stale_after_hours=args.stale_after_hours)
            result.update(command="init", message="仅创建空账本；真实历史尚未建档/核对，不表示无任务。")
        elif not path.exists():
            print(json.dumps(missing_state(path, root, at, args.command), ensure_ascii=False, indent=2))
            return 3
        else:
            data, state_sha256 = read_json(path)
            result = query(data, root, path, state_sha256, args.command, at, args.offset, args.limit,
                           getattr(args, "id", None), args.stale_after_hours, args.gap_offset, args.gap_limit,
                           getattr(args, "require", "closure"))
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 4 if args.command == "check" and not result["check_passed"] else 0
    except (StateError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "scan_complete": False,
                          "message": "查询/校验失败，不能据此判断没有待办；未提交部分状态变更。"}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
