#!/usr/bin/env python3
"""Render validated daily/weekly/monthly JSON to standalone HTML; local files only."""

import argparse
from calendar import monthrange
from datetime import date, datetime
from html import escape
import json
import math
from pathlib import Path
from string import Template
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ASSETS = Path(__file__).resolve().parents[1] / ".agents/skills/1688-business-analysis/assets"
KINDS = {"fact": "事实", "calculation": "计算", "inference": "推断", "recommendation": "建议", "estimate": "预估"}
COVERAGE = {"complete": "完整", "partial": "部分缺失", "unavailable": "暂不可用"}


class ReportError(ValueError):
    """An input cannot be presented under the report contract."""


def require(condition, message):
    if not condition:
        raise ReportError(message)


def object_at(value, path):
    require(isinstance(value, dict), f"{path} 必须为对象")
    return value


def text_at(value, path):
    require(isinstance(value, str) and bool(value.strip()), f"{path} 必须为非空文本")
    return value


def list_at(value, path):
    require(isinstance(value, list), f"{path} 必须为数组")
    return value


def check_fields(value, fields, path):
    object_at(value, path)
    for field in fields:
        text_at(value.get(field), f"{path}.{field}")


def has_placeholder(value):
    if isinstance(value, str):
        return "__REQUIRED__" in value
    if isinstance(value, dict):
        return any(has_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(has_placeholder(item) for item in value)
    return False


def validate(data, allow_simulation=False):
    object_at(data, "report")
    require(data.get("schema_version") == 1, "schema_version 必须为 1")
    require(data.get("data_mode") in ("actual", "simulation"), "占位模板不可渲染；data_mode 必须为 actual 或 simulation")
    require(not has_placeholder(data), "存在 __REQUIRED__ 占位符，请填写真实数据或明确模拟输入")
    require(data["data_mode"] != "simulation" or allow_simulation, "模拟输入需要 --allow-simulation，不能作为正式实绩输出")
    require(data.get("report_type") in ("daily", "weekly", "monthly"), "report_type 必须为 daily、weekly 或 monthly")
    text_at(data.get("title"), "title")
    check_fields(data.get("storeAttribution"), ("store_ref", "display_name"), "storeAttribution")
    check_fields(data.get("period"), ("start", "end", "timezone"), "period")
    try:
        period = data["period"]
        start, end = date.fromisoformat(period["start"]), date.fromisoformat(period["end"])
        timezone = ZoneInfo(period["timezone"])
        cutoff = datetime.fromisoformat(text_at(data.get("data_cutoff"), "data_cutoff").replace("Z", "+00:00"))
        retrieved = datetime.fromisoformat(text_at(data.get("retrieved_at"), "retrieved_at").replace("Z", "+00:00"))
        require(cutoff.tzinfo is not None and cutoff.utcoffset() is not None, "data_cutoff 必须含时区")
        require(retrieved.tzinfo is not None and retrieved.utcoffset() is not None, "retrieved_at 必须含时区")
    except (ValueError, ZoneInfoNotFoundError) as error:
        raise ReportError(f"日期或时区无效：{error}") from error
    require(start <= end, "统计区间起始日期不能晚于结束日期")
    require(cutoff <= retrieved, "数据实际截止时间不能晚于取数时间")
    if data["report_type"] == "daily":
        require(data.get("period_basis") == "single_day_t_plus_1", "日报必须使用单日 T+1 口径")
        require(start == end, "日报只允许单日；多日区间使用周报或长周期分析")
        require(retrieved.astimezone(timezone).date() > end, "日报为 T+1，取数时间须至少为统计日的次日")
    elif data["report_type"] == "weekly":
        require(data.get("period_basis") == "independent_period", "周报必须独立声明区间口径")
        require(start < end, "周报须填写独立的多日统计区间")
    else:
        require(data.get("period_basis") == "complete_calendar_month", "月报必须使用完整自然月口径")
        require(period["timezone"] == "Asia/Shanghai", "本项目月报按 Asia/Shanghai 划分自然月")
        require(start.day == 1 and start.year == end.year and start.month == end.month
                and end.day == monthrange(start.year, start.month)[1], "月报必须覆盖同一自然月的首日至末日")
        require(retrieved.astimezone(timezone).date() > end, "月报只允许已结束的自然月，取数日期须晚于月末")
    strategy = data.get("strategy_version")
    require(strategy is None or isinstance(strategy, str) and bool(strategy.strip()), "strategy_version 必须为文本或 null")
    coverage = object_at(data.get("coverage"), "coverage")
    require(coverage.get("status") in COVERAGE, "coverage.status 无效")
    notes = list_at(coverage.get("notes"), "coverage.notes")
    for index, note in enumerate(notes):
        text_at(note, f"coverage.notes[{index}]")
    require(coverage["status"] == "complete" or bool(notes), "数据缺失时必须说明 coverage.notes")
    if coverage["status"] == "complete":
        require(cutoff.astimezone(timezone).date() >= end, "声明数据完整时，实际截止日期不能早于统计区间结束日")
    metrics = list_at(data.get("metrics"), "metrics")
    require(bool(metrics), "metrics 至少保留一个指标；缺失数据填写 null 和原因")
    for index, metric in enumerate(metrics):
        path = f"metrics[{index}]"
        check_fields(metric, ("name", "unit", "source", "evidence", "basis", "denominator"), path)
        require("value" in metric, f"{path}.value 缺失")
        value = metric["value"]
        require(value is None or type(value) in (int, float) and math.isfinite(value), f"{path}.value 必须为有限数字或 null")
        if value is None:
            text_at(metric.get("missing_reason"), f"{path}.missing_reason")
        else:
            require(metric.get("missing_reason") in (None, ""), f"{path} 有数值时不能同时声称数据缺失")
    for index, finding in enumerate(list_at(data.get("findings"), "findings")):
        path = f"findings[{index}]"
        check_fields(finding, ("kind", "text", "evidence"), path)
        require(finding["kind"] in KINDS, f"{path}.kind 无效")
    for index, action in enumerate(list_at(data.get("actions"), "actions")):
        check_fields(action, ("action_id", "object", "status", "owner", "description", "evidence", "next_condition"), f"actions[{index}]")
    for index, item in enumerate(list_at(data.get("unfinished"), "unfinished")):
        check_fields(item, ("item", "reason", "owner", "next_condition"), f"unfinished[{index}]")
    return data


def escaped(value):
    return escape(str(value), quote=True)


def evidence_html(value):
    """Only explicit HTTP(S) URLs become links; all other evidence stays text."""
    label = escaped(value)
    try:
        parsed = urlsplit(value)
        safe = parsed.scheme.lower() in ("http", "https") and bool(parsed.hostname)
        safe = safe and parsed.username is None and parsed.password is None
        safe = safe and not any(character.isspace() or ord(character) < 32 for character in value)
    except ValueError:
        safe = False
    return f'<a href="{label}" rel="noreferrer noopener">{label}</a>' if safe else label


def table(headers, rows):
    if not rows:
        return '<p class="empty">本次输入未列出。</p>'
    heading = "".join(f"<th scope=\"col\">{escaped(header)}</th>" for header in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{heading}</tr></thead><tbody>{body}</tbody></table>"


def render_report(data, allow_simulation=False):
    validate(data, allow_simulation)
    period = data["period"]
    store = data["storeAttribution"]
    report_label = {"daily": "单日 T+1 日报", "weekly": "独立区间周报",
                    "monthly": "完整自然月月报"}[data["report_type"]]
    metadata = {
        "店铺": store["display_name"], "店铺引用": store["store_ref"],
        "统计区间": f'{period["start"]} 至 {period["end"]}', "时区": period["timezone"],
        "数据实际截止": data["data_cutoff"], "取数时间": data["retrieved_at"],
        "策略版本": data.get("strategy_version") or "未提供",
    }
    metadata_html = "".join(f"<div>{escaped(key)}：{escaped(value)}</div>" for key, value in metadata.items())
    coverage = f'<p><strong>{COVERAGE[data["coverage"]["status"]]}</strong> · {report_label}</p>'
    coverage += "".join(f"<p>{escaped(note)}</p>" for note in data["coverage"]["notes"])
    metrics = []
    for metric in data["metrics"]:
        if metric["value"] is None:
            value = f'<span class="missing">缺失</span><div class="detail">{escaped(metric["missing_reason"])}</div>'
        else:
            value = f'<span class="value">{escaped(metric["value"])}</span>'
        basis = f'{escaped(metric["basis"])}<div class="detail">分母：{escaped(metric["denominator"])}</div>'
        source = f'{escaped(metric["source"])}<div class="detail">{evidence_html(metric["evidence"])}</div>'
        metrics.append((escaped(metric["name"]), value, escaped(metric["unit"]), basis, source))
    findings = "".join(f'<li><span class="label">{KINDS[item["kind"]]}：</span>{escaped(item["text"])}<div class="detail">依据：{evidence_html(item["evidence"])}</div></li>' for item in data["findings"])
    findings = f"<ul>{findings}</ul>" if findings else '<p class="empty">本次输入未列出。</p>'
    action_rows = []
    for item in data["actions"]:
        action_rows.append((escaped(item["action_id"]), escaped(item["object"]), escaped(item["status"]), escaped(item["owner"]), escaped(item["description"]), evidence_html(item["evidence"]), escaped(item["next_condition"])))
    unfinished_rows = [tuple(escaped(item[key]) for key in ("item", "reason", "owner", "next_condition")) for item in data["unfinished"]]
    values = {
        "title": escaped(data["title"]), "report_label": report_label, "metadata": metadata_html,
        "mode_banner": '<div class="mode">模拟数据，不代表店铺实绩</div>' if data["data_mode"] == "simulation" else "",
        "coverage": coverage, "metrics": table(("指标", "数值", "单位", "口径", "来源与证据"), metrics),
        "findings": findings, "actions": table(("行动 ID", "对象", "状态", "负责人", "措施", "证据", "下次评估条件"), action_rows),
        "unfinished": table(("事项", "原因", "负责人", "下次处理条件"), unfinished_rows),
        "data_mode": "模拟数据" if data["data_mode"] == "simulation" else "实际数据（由输入来源声明）",
    }
    return Template((ASSETS / "operating-report.html").read_text(encoding="utf-8")).substitute(values)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--allow-simulation", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        require(args.input.resolve() != args.output.resolve(), "输入和输出不能是同一文件")
        require(args.output.suffix.lower() == ".html", "输出文件扩展名必须为 .html")
        data = json.loads(args.input.read_text(encoding="utf-8"))
        rendered = render_report(data, args.allow_simulation)
        with args.output.open("w" if args.overwrite else "x", encoding="utf-8") as output:
            output.write(rendered)
    except (OSError, ValueError) as error:
        parser.exit(2, f"报告未生成：{error}\n")
    print(f"已生成本地报告：{args.output.resolve()}（仅完成渲染，待核对数据与布局）")


if __name__ == "__main__":
    main()
