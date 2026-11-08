#!/usr/bin/env python3
"""Offline, allowlisted CRM summary. Python 3.9+; no network or business writes."""
import argparse
from datetime import date, datetime
import html
import json
from pathlib import Path
import re
import sys

MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_DEPTH = 24
MAX_NODES = 20000
STAT_FIELDS = ("totalCount", "site1688CustomerCount", "wecomImportedCustomerCount",
               "recent7dNewCount")
PLAN_TEXT_FIELDS = ("planId", "planName", "planType", "strategyCode", "status")
PLAN_COUNT_FIELDS = ("customerCnt", "pendingReachCnt", "reachedCnt", "pendingReplyCnt",
                     "repliedCnt", "orderedCnt")
WRAPPERS = ("content", "text", "data", "result", "structuredContent", "output", "response")
PLAN_LISTS = ("plans", "planList", "customerPlans")
STATUS_LABELS = {"not_started": "未开启", "running": "运行中", "paused": "已暂停",
                 "finished": "已完成", "ignored": "未采纳"}
SCOPE_LABELS = {
    "all_store": "全店客户范围（调用方已提供主账号全店可见依据）。",
    "assigned": "当前账号名下客户范围，不代表全店客户。",
    "unknown": "主/子账号可见范围未核验，不据此断言全店。",
}
MESSAGES = {
    "INVALID_INPUT": "输入不是有效的快照 JSON 对象。",
    "INPUT_TOO_LARGE": "输入超过 8 MiB 上限。",
    "IO_ERROR": "输入或输出文件不可用；未显示原始错误内容。",
    "OUTPUT_EXISTS": "输出已存在；如需替换请明确使用 --overwrite。",
    "PATH_CONFLICT": "输入与输出路径或两个输出路径不能相同。",
    "SOURCE_MISSING": "未提供此数据源。",
    "BUSINESS_ERROR": "工具或业务回包报告失败，此数据源不作为有效结果。",
    "UNRECOGNIZED_RESPONSE": "未识别到受支持的业务结果，不能据外层成功标记认定业务成功。",
    "LIMIT_EXCEEDED": "响应嵌套或节点数超过解析上限。",
    "INVALID_WRAPPER": "响应包装内容无法解析为 JSON。",
    "MISSING_METRIC": "指标缺失；保留 null，不能当作零。",
    "INVALID_METRIC": "指标不是非负整数；保留 null。",
    "CONFLICTING_STATS": "重复统计值冲突；冲突字段保留 null。",
    "DUPLICATE_PLAN": "相同计划 ID 的相同记录已去重。",
    "CONFLICTING_PLAN": "相同计划 ID 的记录冲突；冲突字段保留 null。",
    "PLAN_ID_MISSING": "计划缺少有效 ID，不能可靠去重或汇总覆盖人数。",
    "PLAN_TYPE_MISSING": "明确计划列表中的记录缺少 planType。",
    "INVALID_PLAN_ENTRY": "明确计划列表包含无法识别的记录。",
    "UNKNOWN_STATUS": "出现未知计划状态；保留原值，不能推断已开启或已完成。",
    "INVALID_TEXT": "文本字段类型或长度不受支持；保留 null。",
    "INVALID_GROUP_DATE": "客群日期不符合日期格式，已忽略。",
    "OBSERVED_AT_MISSING": "未提供带时区的观察时间；本快照不能视为当前数据。",
    "OBSERVED_AT_INVALID": "观察时间缺少时区或格式无效；保留 null。",
    "STORE_ATTRIBUTION_MISSING": "未提供可展示的店铺归属。",
    "INVALID_VISIBILITY_SCOPE": "客户可见范围不是支持的枚举；已标记 unknown。",
}


def warn(warnings, code, source, field=None):
    item = {"code": code, "source": source, "message": MESSAGES[code]}
    if field is not None:
        item["field"] = field
    if item not in warnings:
        warnings.append(item)


def safe_text(value, warnings, source, field, limit=200):
    if value is None:
        return None
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        value = str(value).strip()
        if value and len(value) <= limit:
            return value
    warn(warnings, "INVALID_TEXT", source, field)
    return None


def count(value, warnings, source, field):
    if value is None:
        warn(warnings, "MISSING_METRIC", source, field)
        return None
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,18}", value.strip()):
        return int(value.strip())
    warn(warnings, "INVALID_METRIC", source, field)
    return None


def failed(value):
    if value.get("isError") is True or value.get("success") is False:
        return True
    if value.get("error") not in (None, False, "", 0, [], {}):
        return True
    for key in ("errorCode", "code", "statusCode"):
        if key in value and value[key] not in (None, "", 0, 200, "0", "200", "0000", "OK", "SUCCESS", "success"):
            return True
    return False


def collect(raw, source, warnings):
    """Traverse only transport wrappers, never arbitrary records or customer arrays."""
    rows = []
    state = {"nodes": 0, "failed": False, "recognized": False}

    def visit(value, depth=0, explicit_plans=False, allow_empty=True):
        state["nodes"] += 1
        if depth > MAX_DEPTH or state["nodes"] > MAX_NODES:
            warn(warnings, "LIMIT_EXCEEDED", source)
            return
        if isinstance(value, str):
            try:
                decoded = json.loads(value)
            except (ValueError, RecursionError):
                warn(warnings, "INVALID_WRAPPER", source)
                return
            visit(decoded, depth + 1, explicit_plans, allow_empty)
            return
        if isinstance(value, list):
            if source == "plans" and explicit_plans:
                state["recognized"] = True
            # Empty direct query arrays are valid empty plan results.
            if source == "plans" and not value and allow_empty:
                state["recognized"] = True
            for item in value:
                visit(item, depth + 1, explicit_plans, allow_empty)
            return
        if not isinstance(value, dict):
            if explicit_plans:
                warn(warnings, "INVALID_PLAN_ENTRY", source)
            return
        if failed(value):
            state["failed"] = True
            warn(warnings, "BUSINESS_ERROR", source)
            return
        if source == "stats" and any(key in value for key in STAT_FIELDS):
            rows.append(value)
            state["recognized"] = True
            return
        if source == "plans" and ("planType" in value or
                                   (explicit_plans and any(k in value for k in ("planId", "planName")))):
            rows.append(value)
            state["recognized"] = True
            return  # In particular, do not descend into currentGroupList/historyGroupList.
        traversed = False
        for key in WRAPPERS:
            if key in value:
                traversed = True
                visit(value[key], depth + 1, explicit_plans, key != "content")
        if source == "plans":
            for key in PLAN_LISTS:
                if key in value:
                    traversed = True
                    if isinstance(value[key], (list, str)):
                        visit(value[key], depth + 1, True)
                    else:
                        warn(warnings, "INVALID_PLAN_ENTRY", source)
        if explicit_plans and not traversed:
            warn(warnings, "INVALID_PLAN_ENTRY", source)

    if raw is None:
        warn(warnings, "SOURCE_MISSING", source)
    else:
        visit(raw, explicit_plans=source == "plans" and isinstance(raw, (list, str)))
    if not state["recognized"] and not state["failed"]:
        warn(warnings, "UNRECOGNIZED_RESPONSE", source)
    if state["failed"]:
        rows = []  # Never display a failed response's incidental data as success.
    return rows, state


def group_dates(plan, warnings):
    dates = set()
    for key in ("currentGroupList",):
        groups = plan.get(key, [])
        if not isinstance(groups, list):
            warn(warnings, "INVALID_GROUP_DATE", "plans", "groupDates")
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            raw = group.get("ds", group.get("groupDate"))
            if raw is None:
                continue
            value = str(raw)
            if re.fullmatch(r"\d{8}", value):
                value = "{}-{}-{}".format(value[:4], value[4:6], value[6:])
            try:
                dates.add(date.fromisoformat(value).isoformat())
            except (TypeError, ValueError):
                warn(warnings, "INVALID_GROUP_DATE", "plans", "groupDates")
    return sorted(dates)


def normalize_plan(row, warnings):
    result = {key: safe_text(row.get(key), warnings, "plans", key) for key in PLAN_TEXT_FIELDS}
    for key in PLAN_COUNT_FIELDS:
        result[key] = count(row.get(key), warnings, "plans", key)
    result["groupDates"] = group_dates(row, warnings)
    if result["planId"] is None:
        warn(warnings, "PLAN_ID_MISSING", "plans")
    if result["planType"] is None:
        warn(warnings, "PLAN_TYPE_MISSING", "plans")
    if result["status"] not in STATUS_LABELS:
        warn(warnings, "UNKNOWN_STATUS", "plans", "status")
    return result


def build_snapshot(payload):
    """Return a new strictly allowlisted dictionary; never mutate input or perform I/O."""
    warnings = []
    if not isinstance(payload, dict):
        payload = {}
        warn(warnings, "INVALID_INPUT", "input")
    visibility_scope = payload.get("visibilityScope", "unknown")
    if not isinstance(visibility_scope, str) or visibility_scope not in SCOPE_LABELS:
        visibility_scope = "unknown"
        warn(warnings, "INVALID_VISIBILITY_SCOPE", "input", "visibilityScope")
    attribution = payload.get("storeAttribution")
    if isinstance(attribution, dict):
        # Only a caller-supplied display label; no loginId/store_ref/auth dictionaries.
        attribution = attribution.get("label", attribution.get("displayName"))
    attribution = safe_text(attribution, warnings, "input", "storeAttribution")
    if attribution is None:
        warn(warnings, "STORE_ATTRIBUTION_MISSING", "input")
    observed = payload.get("observedAt")
    if observed is None:
        warn(warnings, "OBSERVED_AT_MISSING", "input")
    else:
        try:
            if not isinstance(observed, str):
                raise ValueError()
            parsed = datetime.fromisoformat(observed.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError()
            observed = parsed.isoformat()
        except (TypeError, ValueError, OverflowError):
            observed = None
            warn(warnings, "OBSERVED_AT_INVALID", "input")
    stats_rows, stats_state = collect(payload.get("stats"), "stats", warnings)
    plan_rows, plans_state = collect(payload.get("plans"), "plans", warnings)
    stats = dict.fromkeys(STAT_FIELDS)
    for key in STAT_FIELDS:
        values = [count(row.get(key), warnings, "stats", key) for row in stats_rows]
        if values:
            if all(value == values[0] for value in values):
                stats[key] = values[0]
            else:
                warn(warnings, "CONFLICTING_STATS", "stats", key)
    plans = []
    by_id = {}
    conflicts = set()
    for row in plan_rows:
        plan = normalize_plan(row, warnings)
        identifier = plan["planId"]
        if identifier is None or identifier not in by_id:
            plans.append(plan)
            if identifier is not None:
                by_id[identifier] = plan
            continue
        previous = by_id[identifier]
        if previous == plan:
            warn(warnings, "DUPLICATE_PLAN", "plans")
            continue
        conflicts.add(identifier)
        warn(warnings, "CONFLICTING_PLAN", "plans")
        for key in previous:
            if key != "planId" and previous[key] != plan[key]:
                previous[key] = None
    sources = {}
    for source, state in (("stats", stats_state), ("plans", plans_state)):
        if state["failed"]:
            status = "error"
        elif not state["recognized"]:
            status = "unknown"
        elif any(w["source"] == source and w["code"] != "DUPLICATE_PLAN" for w in warnings):
            status = "partial"
        else:
            status = "available"
        sources[source] = {"status": status}
    counts_valid = (sources["plans"]["status"] == "available" and not conflicts and
                    all(p["planId"] is not None and p["customerCnt"] is not None for p in plans))
    statuses = [source["status"] for source in sources.values()]
    if all(status in ("error", "unknown") for status in statuses):
        overall = "error"
    elif all(status == "available" for status in statuses) and not any(w["source"] == "input" for w in warnings):
        overall = "complete"
    else:
        overall = "partial"
    return {
        "schemaVersion": 1, "snapshotType": "static-read-only", "status": overall,
        "storeAttribution": attribution, "observedAt": observed, "visibilityScope": visibility_scope, "sources": sources,
        "customerStats": stats, "plans": plans,
        "planCoverage": {"listedPlanCount": len(plans) if plans_state["recognized"] and not plans_state["failed"] else None,
                         "summedCustomerCnt": sum(p["customerCnt"] for p in plans) if counts_valid else None,
                         "uniqueCustomerCount": None,
                         "note": "计划人数为各计划客群口径，可能重叠；不能相加作为总客户库或去重覆盖人数。"},
        "warnings": warnings,
    }


def render_html(snapshot):
    """Render a standalone static page. All dynamic text is escaped; no scripts/buttons."""
    def esc(value):
        return html.escape("未知" if value is None else str(value), quote=True)

    stats = snapshot["customerStats"]
    cards = "".join('<section class="card"><span>{}</span><strong>{}</strong></section>'.format(esc(label), esc(stats[key]))
                    for label, key in (("当前授权可见客户", "totalCount"), ("1688 客户", "site1688CustomerCount"),
                                       ("企微导入客户", "wecomImportedCustomerCount"), ("近 7 天新增", "recent7dNewCount")))
    plan_cards = []
    rows = []
    for plan in snapshot["plans"]:
        state = STATUS_LABELS.get(plan["status"], plan["status"] or "未知")
        dates = "、".join(plan["groupDates"]) if plan["groupDates"] else "未知"
        plan_cards.append('<section class="card"><h3>{}</h3><strong>{}</strong><p>计划客群人数 · {}</p><small>客群日期：{}</small></section>'.format(
            esc(plan["planName"]), esc(plan["customerCnt"]), esc(state), esc(dates)))
        values = (plan["planId"], plan["planName"], state, plan["customerCnt"], plan["pendingReachCnt"],
                  plan["reachedCnt"], plan["repliedCnt"], plan["orderedCnt"], dates)
        rows.append("<tr>" + "".join("<td>{}</td>".format(esc(value)) for value in values) + "</tr>")
    status_label = {"complete": "已解析快照", "partial": "数据部分可用 · 请检查提示", "error": "数据不可用 · 不能视为查询成功"}.get(snapshot["status"], "状态未知")
    source_labels = {"available": "已识别", "partial": "部分可用", "error": "失败", "unknown": "未识别"}
    source_line = "；".join("{}：{}".format(label, source_labels.get(snapshot["sources"][key]["status"], "未知"))
                            for key, label in (("stats", "客户统计"), ("plans", "计划查询")))
    source_line += "；" + SCOPE_LABELS.get(snapshot.get("visibilityScope"), SCOPE_LABELS["unknown"])
    warnings_html = "".join("<li><code>{}</code> {}（{}{}）</li>".format(
        esc(w["code"]), esc(w["message"]), esc(w["source"]), " / " + esc(w["field"]) if w.get("field") else "")
        for w in snapshot["warnings"])
    return '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>1688 客户运营 · 只读快照</title><style>
*{box-sizing:border-box}body{margin:0;background:#f7faf9;color:#202b29;font:15px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}
main{max-width:1320px;margin:40px auto;padding:0 28px}header{margin-bottom:26px}h1{font-size:28px;margin:0}h2{font-size:20px;margin:24px 0 12px}h3{font-size:17px;margin:0 0 8px}p{margin:8px 0;color:#596963}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:16px}.card{background:white;border:1px solid #e0e8e4;border-radius:16px;padding:22px}.card strong{display:block;font-size:30px;line-height:1.5}.strategies{margin-top:22px;background:#e9f9f1;padding:20px;border-radius:18px}.notice{border-left:4px solid #e1ac47;background:#fff8e6;padding:12px 16px;border-radius:8px;margin-top:18px}small{color:#667972}.table-wrap{overflow:auto;border:1px solid #e0e8e4;border-radius:14px;background:white}table{border-collapse:collapse;width:100%;min-width:900px;text-align:left}th,td{padding:14px 16px;border-bottom:1px solid #edf1ef}th{background:#f0f5f2;white-space:nowrap}td{overflow-wrap:anywhere}li{margin:8px 0}code{font-size:12px}footer{margin:24px 0;color:#667972}
</style></head><body><main><header><h1>客户运营</h1><p>静态只读快照 · 不会自动刷新</p><p>店铺归属：''' + esc(snapshot["storeAttribution"]) + '''<br>数据观察时间：''' + esc(snapshot["observedAt"]) + '''</p><div class="notice"><strong>''' + esc(status_label) + '''</strong><br>''' + esc(source_line) + '''</div></header><h2>客户库</h2><div class="grid">''' + cards + '''</div><section class="strategies"><h2>客群策略</h2><div class="grid">''' + ("".join(plan_cards) or "<p>本快照没有可展示的计划记录；请结合数据源状态判断。</p>") + '''</div><p>''' + esc(snapshot["planCoverage"]["note"]) + '''</p></section><h2>计划状态</h2><div class="table-wrap"><table><thead><tr>''' + "".join("<th>{}</th>".format(label) for label in ("计划 ID", "计划名称", "状态", "客群人数", "待触达", "已触达", "已回复", "已成单客户", "客群日期")) + '''</tr></thead><tbody>''' + ("".join(rows) or '<tr><td colspan="9">无可展示记录</td></tr>') + '''</tbody></table></div>''' + ("<h2>数据提示</h2><ul>" + warnings_html + "</ul>" if warnings_html else "") + '''<footer>所有数字仅代表标注观察时间的工具回包。缺失值显示为“未知”，不代表 0。此页面只展示聚合数据和计划状态，不提供配置、发送或其他业务操作。</footer></main></body></html>'''


def _error_snapshot(code):
    result = build_snapshot({})
    warn(result["warnings"], code, "input")
    result["status"] = "error"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="离线生成 1688 客户运营脱敏 JSON / 静态 HTML 快照。仅处理本地输入，不联网、不读凭证、不修改计划、不触达客户。Python 3.9+。")
    parser.add_argument("--input", default="-", help="JSON 文件路径，或 - 读取 stdin（默认）；最大 8 MiB。输入键：storeAttribution、带时区 observedAt、stats、plans；visibilityScope 可选 all_store/assigned/unknown，仅有真实依据时指定前两者。")
    parser.add_argument("--json-out", help="脱敏 JSON 输出路径；省略时输出到 stdout。")
    parser.add_argument("--html-out", help="可选静态只读 HTML 输出路径；无脚本、无操作按钮，不自动刷新。")
    parser.add_argument("--overwrite", action="store_true", help="明确允许替换已有输出文件；始终禁止覆盖输入。")
    args = parser.parse_args(argv)
    destinations = [Path(value).expanduser().resolve() for value in (args.json_out, args.html_out) if value]
    source_path = Path(args.input).expanduser().resolve() if args.input != "-" else None
    code = None
    if len(set(destinations)) != len(destinations) or source_path in destinations:
        code = "PATH_CONFLICT"
    elif not args.overwrite and any(path.exists() for path in destinations):
        code = "OUTPUT_EXISTS"
    if code:
        print(json.dumps(_error_snapshot(code), ensure_ascii=False, indent=2))
        return 2
    try:
        if source_path is None:
            raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        else:
            with source_path.open("rb") as stream:
                raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            snapshot = _error_snapshot("INPUT_TOO_LARGE")
        else:
            try:
                payload = json.loads(raw.decode("utf-8-sig"))
                snapshot = build_snapshot(payload)
            except (UnicodeError, ValueError, RecursionError):
                snapshot = _error_snapshot("INVALID_INPUT")
        encoded = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
        for output, body in ((args.json_out, encoded), (args.html_out, render_html(snapshot))):
            if output:
                with Path(output).expanduser().open("w" if args.overwrite else "x", encoding="utf-8") as stream:
                    stream.write(body)
        if not args.json_out:
            print(encoded, end="")
        return 2 if snapshot["status"] == "error" else 0
    except (OSError, ValueError):
        print(json.dumps(_error_snapshot("IO_ERROR"), ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
