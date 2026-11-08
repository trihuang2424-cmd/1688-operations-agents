#!/usr/bin/env python3
"""Normalize local ITEM /item/skuStockWarning receipts; never mutate source data."""
import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


class ReceiptError(ValueError):
    pass


class NoCandidates(ReceiptError):
    pass


def quantity(value):
    """Missing/invalid is None; an actual numeric zero remains zero."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number < 0:
        return None
    return number


def json_number(value):
    if value is None:
        return None
    return int(value) if value == value.to_integral_value() else float(value)


def identifier(value):
    if isinstance(value, bool) or value is None:
        return None
    text = str(value)
    return text if text.isascii() and text.isdigit() and int(text) > 0 else None


def unpack(receipt):
    """Unwrap supported tool envelopes, keeping attribution and query time."""
    metadata = {}
    current = receipt
    for _ in range(20):
        if not isinstance(current, dict):
            raise ReceiptError('回执不是支持的对象结构；未生成当前预警结论')
        for key in ('storeAttribution', 'queriedAt'):
            if key in current:
                if key in metadata and metadata[key] != current[key]:
                    raise ReceiptError(f'{key}在回执层级间不一致；请先核对证据归属/时间')
                metadata[key] = current[key]
        codes = {str(current.get(key, '')).strip().upper() for key in ('errorCode', 'code')}
        if codes & {'INVALID_PARAM', 'PROVIDER_ERROR', 'INTERNAL_ERROR'}:
            raise ReceiptError('接口返回错误码；未形成当前库存结论')
        if 'NO_DATA' in codes:
            raise NoCandidates('本次查询无返回候选；不据此判断全店库存风险')
        if current.get('isError') is True or current.get('success') is False:
            raise ReceiptError('接口调用失败；未形成当前库存结论')
        if '库存预警列表' in current:
            if not isinstance(current['库存预警列表'], list):
                raise ReceiptError('库存预警列表不是数组')
            return current, metadata
        for key in ('result', 'structuredContent', 'data'):
            if isinstance(current.get(key), dict):
                current = current[key]
                break
        else:
            candidates = []
            blocks = current.get('content', [])
            if not isinstance(blocks, list):
                raise ReceiptError('content不是数组；无法解析库存回执')
            for block in blocks:
                if not isinstance(block, dict) or block.get('type') != 'text':
                    continue
                try:
                    item = json.loads(block.get('text', ''))
                except (ValueError, TypeError):
                    continue
                if isinstance(item, dict):
                    candidates.append(item)
            if len(candidates) != 1:
                raise ReceiptError('没有唯一可解析的库存回执；未生成当前预警结论')
            current = candidates[0]
    raise ReceiptError('回执嵌套过深')


def normalize_row(row):
    if not isinstance(row, dict):
        raise ReceiptError('库存预警行不是对象')
    real = quantity(row.get('实时可售库存'))
    recommended = quantity(row.get('建议库存'))
    item_id, sku_id = identifier(row.get('商品ID')), identifier(row.get('SKU ID'))
    scope = row.get('实时库存口径')
    state, active, gap = '待核验', None, None
    if not item_id or not sku_id:
        reason = '缺少有效商品ID或SKU ID，不能确认预警对象'
    elif scope != '该SKU的可售库存':
        reason = '实时库存不是明确的同SKU口径；商品级回退或口径缺失需补查商品/SKU映射'
    elif real is None:
        reason = '实时可售库存缺失或无效；不得按0判断'
    elif real == 0:
        state, active = '当前可售为0', True
        gap = recommended
        reason = '同SKU实时可售为0；只代表页面可售口径'
        if recommended is None:
            reason += '；建议库存缺失或无效，当前缺口未知'
    elif recommended is None:
        reason = '建议库存缺失或无效；实时库存虽大于0，仍不能判定是否达到建议阈值'
    elif real >= recommended:
        state, active, gap = '已达建议库存', False, Decimal(0)
        reason = '同SKU实时可售已达到建议库存，离线旧预警不再成立；不推断补货事件'
    else:
        state, active, gap = '低于建议库存', True, recommended - real
        reason = '同SKU实时可售低于建议库存；当前缺口按实时数值重算'
    return {
        '商品ID': item_id,
        'SKU ID': sku_id,
        '商品标题': row.get('商品标题'),
        'SKU规格': row.get('SKU规格'),
        '单品货号': row.get('单品货号'),
        '离线预警等级': row.get('预警等级'),
        '离线可用库存': json_number(quantity(row.get('可用库存(离线)'))),
        '离线建议库存': json_number(recommended),
        '离线库存缺口': json_number(quantity(row.get('库存缺口'))),
        '实时可售库存': json_number(real),
        '实时库存口径': scope,
        '当前预警状态': state,
        '当前库存缺口': json_number(gap),
        '列入当前库存风险': active,
        '校验说明': reason,
    }


def normalize(receipt, source=None):
    data, metadata = unpack(receipt)
    rows = [normalize_row(row) for row in data['库存预警列表']]
    identities = set()
    for row in rows:
        identity = (row['商品ID'], row['SKU ID'])
        if all(identity):
            if identity in identities:
                raise ReceiptError('同一商品/SKU重复返回；请核对重复或冲突证据后再生成当前状态，不能重复计数')
            identities.add(identity)
    return {
        '规则版本': '1.0',
        '证据文件': source,
        'queriedAt': metadata.get('queriedAt'),
        'storeAttribution': metadata.get('storeAttribution'),
        '接口': 'ITEM /item/skuStockWarning',
        '范围': '仅本次回执返回的记录；当前状态对应取数时点，不代表全店或实物库存',
        '离线预警总数': data.get('预警总数'),
        '页码': data.get('页码'),
        '每页条数': data.get('每页条数'),
        '本页校验记录数': len(rows),
        '本页当前有效预警数': sum(r['列入当前库存风险'] is True for r in rows),
        '本页待核验记录数': sum(r['列入当前库存风险'] is None for r in rows),
        '本页已解除预警数': sum(r['列入当前库存风险'] is False for r in rows),
        '库存校验列表': rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.output and args.input.resolve() == args.output.resolve():
            raise ReceiptError('输出不能覆盖原始回执')
        if args.output and args.output.exists():
            raise ReceiptError('输出文件已存在，请指定新文件以保留证据')
        receipt = json.loads(args.input.read_text(encoding='utf-8'))
        result = normalize(receipt, str(args.input.resolve()))
        content = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(content)
        else:
            print(content, end='')
    except NoCandidates as error:
        print(f'库存接口返回NO_DATA：{error}', file=sys.stderr)
        return 3
    except (OSError, ValueError) as error:
        print(f'库存校验未完成：{error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
