#!/usr/bin/env python3
"""Local inquiry/conversion issue state; no network or customer operations."""
import argparse
import copy
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid


class StateError(ValueError):
    pass


SCHEMA_VERSION = 2
INPUT_VERSIONS = {1, 2}
COMMANDS = ('init', 'reconcile-history', 'ingest', 'claim', 'record-dispatch',
            'mark-unknown', 'reconcile-request', 'record-result', 'record-action',
            'record-direct-start', 'record-task-end', 'revalidate-request',
            'cancel-pending', 'migrate', 'summary')
ACTIVE_REQUESTS = {'pending', 'claimed', 'dispatched', 'unknown'}
MATURITY_REQUIRED = {'conversion', 'followup', 'order', 'repurchase'}
PROBLEMS = MATURITY_REQUIRED | {'response', 'handoff', 'demand_mismatch',
                              'inquiry_volume', 'inquiry_quality', 'data_gap',
                              'process_commitment'}
UNFINISHED_ACTIONS = {'observing', 'active', 'unknown'}


def digest(value):
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError) as error:
        raise StateError('输入不是有限值 JSON') from error
    return hashlib.sha256(encoded).hexdigest()


def required(obj, field):
    value = obj.get(field)
    if not isinstance(value, str) or not value.strip():
        raise StateError(field + ' 必须是非空字符串')
    return value


def timestamp(value):
    if not isinstance(value, str):
        raise StateError('时间必须是含时区的 ISO 8601 字符串')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise StateError('无效时间: ' + value) from error
    if result.tzinfo is None:
        raise StateError('时间必须带时区: ' + value)
    return result


def refs(obj, key='evidence_refs'):
    value = obj.get(key)
    if not isinstance(value, list) or not value or any(
            not isinstance(item, str) or not item.strip() for item in value):
        raise StateError(key + ' 必须含至少一项证据引用')
    return value


def scope_key(store_ref, scope):
    if not isinstance(scope, dict):
        raise StateError('scope 必须是对象')
    fields = {'object_type', 'object_id', 'problem_type', 'cohort_id', 'metric_id'}
    if set(scope) != fields:
        raise StateError('scope 只接受稳定的 object_type/object_id/problem_type/cohort_id/metric_id')
    for field in fields:
        required(scope, field)
    if scope['object_type'] not in {'shop', 'product', 'channel', 'cohort'}:
        raise StateError('scope 仅支持聚合对象 shop/product/channel/cohort')
    if scope['problem_type'] not in PROBLEMS:
        raise StateError('未知 problem_type')
    return 'ci-' + digest({'store_ref': store_ref, 'scope': scope})[:24]


def evidence_hash(evidence):
    if not isinstance(evidence, dict):
        raise StateError('evidence 必须是对象')
    fields = ('source', 'period_start', 'period_end', 'cutoff', 'definition',
              'version', 'content_fingerprint')
    for field in fields:
        required(evidence, field)
    try:
        start = datetime.strptime(evidence['period_start'], '%Y-%m-%d').date()
        end = datetime.strptime(evidence['period_end'], '%Y-%m-%d').date()
    except ValueError as error:
        raise StateError('证据周期必须是 YYYY-MM-DD') from error
    if start > end or end > timestamp(evidence['cutoff']).date():
        raise StateError('证据周期/截止时间不一致')
    if not re.fullmatch(r'(sha256:)?[0-9a-f]{64}', evidence['content_fingerprint']):
        raise StateError('content_fingerprint 必须是规范化业务内容的 SHA256')
    refs(evidence, 'refs')
    # Artifact path and retrieval time are provenance, never new business evidence.
    return digest({key: evidence[key] for key in fields})


def validate_quality(quality):
    if not isinstance(quality, dict):
        raise StateError('quality 必须是对象')
    choices = {
        'coverage': {'complete', 'partial', 'missing'},
        'comparability': {'comparable', 'mixed', 'unknown'},
        'sample': {'sufficient', 'insufficient', 'unknown'},
        'maturity': {'mature', 'immature', 'unknown', 'not_applicable'},
    }
    for field, allowed in choices.items():
        if quality.get(field) not in allowed:
            raise StateError('quality.' + field + ' 无效或缺失')


def assessment(signal):
    quality = signal['quality']
    if signal['signal'] == 'unknown' or quality['coverage'] != 'complete':
        return 'unknown'
    if quality['comparability'] != 'comparable' or quality['sample'] != 'sufficient':
        return 'unknown'
    if signal['scope']['problem_type'] == 'process_commitment':
        if signal['process_commitment']['observed_status'] == 'unknown':
            return 'unknown'
    if signal['scope']['problem_type'] in MATURITY_REQUIRED:
        if quality['maturity'] == 'immature':
            return 'immature'
        if quality['maturity'] != 'mature':
            return 'unknown'
    return signal['signal']


def validate_action(action):
    if not isinstance(action, dict):
        raise StateError('related_action 必须是对象')
    required(action, 'action_id')
    if action.get('status') not in {'observing', 'active', 'completed', 'unknown'}:
        raise StateError('related_action.status 无效')
    refs(action)
    if action.get('next_review_at'):
        timestamp(action['next_review_at'])


def payload_actions(payload):
    """Accept the old singular input, but never replace the complete action set."""
    if payload.get('related_action') is not None and 'related_actions' in payload:
        raise StateError('related_action 与 related_actions 不能同时提供')
    actions = ([payload['related_action']] if payload.get('related_action') is not None
               else payload.get('related_actions', []))
    if not isinstance(actions, list):
        raise StateError('related_actions 必须是数组')
    seen, normalized = set(), []
    for original in actions:
        validate_action(original)
        action = copy.deepcopy(original)
        key = action['action_id']
        if key in seen:
            raise StateError('同一输入不能重复 action_id')
        seen.add(key)
        # Legacy single-action callers supplied the action review at top level.
        if 'next_review_at' not in action and payload.get('related_action') is not None:
            action['next_review_at'] = payload.get('next_review_at')
        if action['status'] in UNFINISHED_ACTIONS and not action.get('next_review_at'):
            raise StateError('每项未完成行动必须有自己的 next_review_at')
        normalized.append(action)
    return normalized


def unknown_actions(issue):
    return [action for action in issue['actions'].values() if action['status'] == 'unknown']


def observing_actions(issue):
    return [action for action in issue['actions'].values() if action['status'] in {'observing', 'active'}]


def update_actions(issue, actions, at, monitor=False):
    for action in actions:
        previous = issue['actions'].get(action['action_id'])
        if monitor and previous is not None and previous != action:
            raise StateError('不能由每日信号覆盖既有行动；先以 record-action/record-result 明确更新')
        issue['actions'][action['action_id']] = copy.deepcopy(action)
    if actions and not monitor:
        issue['last_action_at'] = at


def validate_process(signal):
    if signal['scope']['problem_type'] != 'process_commitment':
        if 'process_commitment' in signal:
            raise StateError('过程承诺须单列 process_commitment 问题，不改变既有成交指标语义')
        return
    fact = signal.get('process_commitment')
    if not isinstance(fact, dict):
        raise StateError('过程问题须有明确 process_commitment 事实')
    if fact.get('stage') not in {'followup', 'quotation', 'sample', 'fulfillment'}:
        raise StateError('不支持的过程阶段')
    for name in ('commitment_ref', 'expected_event'):
        required(fact, name)
    due, checked = timestamp(required(fact, 'due_at')), timestamp(required(fact, 'checked_at'))
    observed = fact.get('observed_status')
    if observed not in {'fulfilled', 'missed', 'unknown', 'not_due'}:
        raise StateError('过程事实状态无效')
    if signal['quality']['maturity'] != 'not_applicable':
        raise StateError('过程承诺按明确时限核实，maturity 须为 not_applicable')
    if observed == 'missed' and checked < due:
        raise StateError('承诺未到期，不能记为 missed')
    if observed == 'not_due' and checked >= due:
        raise StateError('已到期的承诺不能记为 not_due')
    if observed != 'unknown' and checked > timestamp(signal['evidence']['cutoff']):
        raise StateError('过程事实核验时点不能晚于证据实际覆盖截止')
    if signal['signal'] == 'anomaly' and observed != 'missed':
        raise StateError('过程异常须有已到期且未履行的明确事实；缺记录记 unknown')
    if signal['signal'] == 'normal' and observed not in {'fulfilled', 'not_due'}:
        raise StateError('过程正常须有已履行或尚未到期的明确事实')
    if signal.get('commitment_change') is not None:
        if not isinstance(signal['commitment_change'], dict):
            raise StateError('commitment_change 必须有原因和证据引用')
        required(signal['commitment_change'], 'reason')
        refs(signal['commitment_change'])


def check_commitment_change(issue, signal):
    previous = issue['latest']['signal'].get('process_commitment') if issue['latest'] else None
    current = signal.get('process_commitment')
    if previous and current and any(previous[key] != current[key] for key in ('stage', 'due_at', 'expected_event')):
        if not signal.get('commitment_change'):
            raise StateError('同一过程承诺内容/时限变更须有 commitment_change 原因和依据，不能静默延期')


def validate_signal(store_ref, signal):
    if not isinstance(signal, dict):
        raise StateError('signal 必须是对象')
    key = scope_key(store_ref, signal.get('scope'))
    if signal.get('signal') not in {'normal', 'anomaly', 'unknown'}:
        raise StateError('signal 只接受 normal/anomaly/unknown')
    evidence_hash(signal.get('evidence'))
    validate_quality(signal.get('quality'))
    validate_process(signal)
    if not isinstance(signal.get('criteria'), dict):
        raise StateError('criteria 必须记录依据，不能内置任意经营阈值')
    required(signal['criteria'], 'source')
    required(signal['criteria'], 'condition')
    if signal.get('next_review_at'):
        timestamp(signal['next_review_at'])
    payload_actions(signal)
    for name in ('new_fact', 'intervention'):
        if signal.get(name) is not None:
            event = signal[name]
            if not isinstance(event, dict):
                raise StateError(name + ' 必须是对象')
            required(event, 'id')
            required(event, 'reason')
            refs(event)
            if name == 'intervention':
                required(event, 'criteria_source')
    return key


def new_state(store_ref):
    return {'schema_version': SCHEMA_VERSION, 'store_ref': store_ref,
            'history_reconciliation': {'status': 'required'},
            'last_observed_at': None, 'issues': {}, 'requests': {}, 'runs': {}}


def make_issue(key, signal, at):
    return {'issue_id': key, 'scope': copy.deepcopy(signal['scope']),
            'owner': 'operations_director', 'recommended_owner': None,
            'status': 'open', 'created_at': at, 'last_observed_at': at,
            'latest': None, 'observations': [], 'request_ids': [],
            'consumed_triggers': [], 'actions': {},
            'next_review_at': None, 'decisions': []}


def active_request(state, issue):
    active = [state['requests'][key] for key in issue['request_ids']
              if state['requests'][key]['status'] in ACTIVE_REQUESTS]
    if len(active) > 1:
        raise StateError('同一问题存在多个未完成请求，请先核对状态')
    return active[0] if active else None


def latest_issue_time(issue):
    """An action readback can be newer than the last business observation."""
    return max(timestamp(issue['last_observed_at']),
               timestamp(issue.get('last_action_at') or issue['last_observed_at']))


def context_digest(issue):
    """Business context available locally; external strategy changes remain a caller check."""
    latest = issue['latest']
    signal = latest['signal']
    return digest({'evidence_hash': latest['evidence_hash'], 'assessment': latest['assessment'],
                   'quality': signal['quality'], 'criteria': signal['criteria'],
                   'process_commitment': signal.get('process_commitment'),
                   'actions': issue['actions'], 'next_review_at': issue['next_review_at'],
                   'status': issue['status'], 'last_action_at': issue.get('last_action_at')})


def due_triggers(issue, at):
    due = []
    if issue['next_review_at'] and timestamp(at) >= timestamp(issue['next_review_at']):
        due.append('review:' + issue['next_review_at'])
    for key, action in sorted(issue['actions'].items()):
        review = action.get('next_review_at')
        if action['status'] in UNFINISHED_ACTIONS and review and timestamp(at) >= timestamp(review):
            due.append('action-review:' + key + ':' + review)
    return [trigger for trigger in due if trigger not in issue['consumed_triggers']]


def scan_due_reviews(state, at):
    """Clock-driven local checks; never invent an observation for an absent signal."""
    results = []
    for issue in state['issues'].values():
        if issue['status'] == 'resolved':
            continue
        if timestamp(at) < latest_issue_time(issue):
            continue
        due = due_triggers(issue, at)
        if not due:
            continue
        active = active_request(state, issue)
        if active:
            decision, request_id = 'request_' + active['status'], active['request_id']
        elif state['history_reconciliation']['status'] != 'complete':
            decision, request_id = 'reconcile_history', None
        elif unknown_actions(issue):
            decision, request_id = 'reconcile_action', None
        else:
            request_id = request_analysis(state, issue, due[0], at,
                                          '既定复查到期；即使本轮数据缺席也核实补证/观察条件', due)
            decision = 'analysis_requested'
        results.append({'issue_id': issue['issue_id'], 'decision': decision,
                        'request_id': request_id, 'due_triggers': due,
                        'evidence_hash': issue['latest']['evidence_hash']})
    return results


def request_analysis(state, issue, trigger, at, reason, covered_triggers=None):
    request_id = 'ca-' + digest({'issue_id': issue['issue_id'], 'trigger': trigger})[:24]
    if request_id in state['requests']:
        raise StateError('分析请求标识冲突')
    state['requests'][request_id] = {
        'request_id': request_id, 'issue_id': issue['issue_id'],
        'status': 'pending', 'created_at': at, 'trigger': trigger,
        'reason': reason, 'evidence_hash': issue['latest']['evidence_hash'],
        'validated_context_digest': context_digest(issue),
        'covered_triggers': covered_triggers or [trigger],
        'claim': None, 'dispatch': None, 'direct_execution': None, 'events': [], 'result': None,
    }
    issue['request_ids'].append(request_id)
    issue['consumed_triggers'].extend(covered_triggers or [trigger])
    return request_id


def ingest_signals(state, signals, at, allow_requests=True):
    if not isinstance(signals, list):
        raise StateError('signals 必须是数组；空数组不代表旧问题已解决')
    seen, outcomes = set(), []
    for signal in signals:
        key = validate_signal(state['store_ref'], signal)
        if (signal['scope']['problem_type'] == 'process_commitment' and
                timestamp(signal['process_commitment']['checked_at']) > timestamp(at)):
            raise StateError('过程事实核验时点不能晚于本轮监测时间')
        if key in seen:
            raise StateError('同一轮不能重复提供相同问题 scope')
        seen.add(key)
        current = assessment(signal)
        issue = state['issues'].get(key)
        if issue is None and current == 'normal' and not payload_actions(signal):
            outcomes.append({'issue_id': key, 'decision': 'normal_no_issue'})
            continue
        if issue is None:
            issue = make_issue(key, signal, at)
            state['issues'][key] = issue
        if allow_requests and timestamp(at) < latest_issue_time(issue):
            raise StateError('监测时间早于该问题最新评估，拒绝覆盖')
        old_hash = issue['latest']['evidence_hash'] if issue['latest'] else None
        new_hash = evidence_hash(signal['evidence'])
        check_commitment_change(issue, signal)
        update_actions(issue, payload_actions(signal), at, monitor=True)
        if signal.get('next_review_at'):
            if issue['next_review_at'] and issue['next_review_at'] != signal['next_review_at']:
                raise StateError('不能由每日信号改写复查日期；先以 record-action/record-result 明确更新')
            issue['next_review_at'] = signal['next_review_at']
        if not issue['next_review_at'] and current in {'unknown', 'immature'}:
            raise StateError('证据缺失、未成熟或未完成行动须提供 next_review_at，不能无限观察')
        stale_evidence = (issue['latest'] and
                          timestamp(signal['evidence']['cutoff']) <
                          timestamp(issue['latest']['signal']['evidence']['cutoff']))
        if stale_evidence:
            current = 'unknown'
            issue['last_observed_at'] = max(at, issue['last_observed_at'], key=timestamp)
        elif issue['latest'] and timestamp(at) < timestamp(issue['last_observed_at']):
            # Historical action import may follow today's preliminary monitoring.
            # Preserve the newer monitoring snapshot, but retain the history below.
            current = issue['latest']['assessment']
        else:
            issue['last_observed_at'] = at
            issue['latest'] = {'assessment': current, 'evidence_hash': new_hash,
                               'signal': copy.deepcopy(signal)}
        issue['observations'].append({'at': at, 'assessment': current,
                                      'stale_evidence': bool(stale_evidence),
                                      'evidence_hash': new_hash,
                                      'evidence_refs': signal['evidence']['refs'],
                                      **({'process_commitment': copy.deepcopy(signal['process_commitment']),
                                          'commitment_change': copy.deepcopy(signal.get('commitment_change'))}
                                         if signal.get('process_commitment') else {})})
        active = active_request(state, issue)
        decision = 'hold'
        trigger = reason = None
        if active:
            decision = 'request_' + active['status']
        elif not allow_requests or state['history_reconciliation']['status'] != 'complete':
            decision = 'reconcile_history'
        elif unknown_actions(issue):
            decision = 'reconcile_action'
        elif current == 'unknown':
            decision = 'stale_evidence' if stale_evidence else 'needs_evidence'
            if issue['status'] != 'resolved':
                issue['status'] = 'needs_evidence'
        elif current == 'immature':
            decision = 'observe_immature'
            if issue['status'] != 'resolved':
                issue['status'] = 'observing'
        else:
            # An explicit significant fact needs genuinely changed evidence;
            # a rolling window or a new retrieval timestamp alone never triggers it.
            for name in ('intervention', 'new_fact'):
                event = signal.get(name)
                candidate = name + ':' + event['id'] if event else None
                if event and new_hash != old_hash and candidate not in issue['consumed_triggers']:
                    trigger, reason = candidate, event['reason']
                    break
            if (trigger is None and current == 'anomaly' and issue['status'] == 'resolved' and
                    new_hash != issue.get('resolved_evidence_hash')):
                trigger, reason = 'recurrence:' + new_hash, '已结案的问题出现有新证据的成熟异常'
            if trigger is None and current == 'anomaly' and not issue['request_ids']:
                if observing_actions(issue):
                    decision = 'observe_existing_action'
                    issue['status'] = 'observing'
                else:
                    trigger, reason = 'initial', '可比较且样本/成熟度满足要求的首个异常'
            if trigger is None and current == 'normal':
                decision = 'normal_requires_explicit_resolution'
        if trigger:
            if issue['status'] == 'resolved':
                issue['status'] = 'open'
            request_id = request_analysis(state, issue, trigger, at, reason)
            decision = 'analysis_requested'
        else:
            request_id = active['request_id'] if active else None
        outcomes.append({'issue_id': key, 'decision': decision,
                         'assessment': current, 'request_id': request_id})
    return outcomes


def get_request(state, payload):
    key = required(payload, 'request_id')
    request = state['requests'].get(key)
    if request is None:
        raise StateError('未知 request_id')
    return request, state['issues'][request['issue_id']]


def summary(state):
    cards = []
    for issue in state['issues'].values():
        if issue['status'] == 'resolved':
            continue
        request = active_request(state, issue)
        latest = issue['latest']
        cards.append({'issue_id': issue['issue_id'], 'scope': issue['scope'],
                      'owner': issue['owner'], 'recommended_owner': issue['recommended_owner'],
                      'status': issue['status'], 'assessment': latest['assessment'],
                      'quality': latest['signal']['quality'], 'criteria': latest['signal']['criteria'],
                      'last_monitoring': issue['observations'][-1] if issue['observations'] else None,
                      'evidence_refs': latest['signal']['evidence']['refs'],
                      'related_actions': list(issue['actions'].values()),
                      'next_review_at': issue['next_review_at'],
                      'context_digest': context_digest(issue),
                      'last_decision': issue['decisions'][-1] if issue['decisions'] else None,
                      'request': ({**{key: request[key] for key in ('request_id', 'status', 'reason')},
                                   'needs_revalidation': (request['status'] == 'pending' and
                                                          request['validated_context_digest'] != context_digest(issue)),
                                   'execution_mode': ('director_fallback' if request['direct_execution'] else
                                                      'subagent' if request['dispatch'] else 'not_dispatched')}
                                  if request else None)})
    return {'schema_version': SCHEMA_VERSION, 'store_ref': state['store_ref'],
            'migrations': [{key: value for key, value in migration.items() if key != 'source_snapshot'}
                           for migration in state.get('migrations', [])],
            'history_reconciliation': state['history_reconciliation'],
            'last_observed_at': state['last_observed_at'], 'issues': cards,
            'issue_counts': {'open': len(cards),
                             'resolved': sum(issue['status'] == 'resolved' for issue in state['issues'].values())},
            'pending_requests': [key for key, value in state['requests'].items()
                                 if value['status'] == 'pending'],
            'reconciliation_requests': [key for key, value in state['requests'].items()
                                        if value['status'] in {'claimed', 'unknown'}]}


def migrate_state(state):
    """Upgrade once, retaining the exact v1 state and all old IDs/replay receipts."""
    if state.get('schema_version') == SCHEMA_VERSION:
        return state
    if state.get('schema_version') != 1:
        raise StateError('不支持的状态 schema_version')
    original = copy.deepcopy(state)
    for issue in state['issues'].values():
        candidates = []
        for decision in issue.get('decisions', []):
            if decision.get('related_action'):
                candidates.append((decision['at'], decision['related_action'], decision.get('next_review_at')))
        for request_id in issue.get('request_ids', []):
            result = state['requests'][request_id].get('result')
            record = result['record'] if result else {}
            if record.get('related_action'):
                candidates.append((record['completed_at'], record['related_action'], record.get('next_review_at')))
        current = issue.pop('related_action', None)
        current_id = current['action_id'] if current else None
        actions = {}
        for _, item, review in sorted(candidates, key=lambda item: timestamp(item[0])):
            validate_action(item)
            action = copy.deepcopy(item)
            action['next_review_at'] = action.get('next_review_at') or review or issue.get('next_review_at')
            actions[action['action_id']] = action
        if current:
            validate_action(current)
            actions[current_id] = {**copy.deepcopy(current),
                                   'next_review_at': current.get('next_review_at') or issue.get('next_review_at')}
        for key, action in actions.items():
            if action['status'] in UNFINISHED_ACTIONS:
                if key != current_id:
                    action['status'] = 'unknown'
                    action['migration_review_required'] = True
                if not action.get('next_review_at'):
                    action['next_review_at'] = issue['last_observed_at']
                    action['migration_review_required'] = True
        issue['actions'] = actions
        if issue['status'] == 'resolved' and any(a['status'] in UNFINISHED_ACTIONS for a in actions.values()):
            issue['status'] = 'needs_evidence'
            issue['decisions'].append({'type': 'migration_review', 'at': issue['last_observed_at'],
                                      'reason': '旧结案问题仍关联未完成行动；保留历史结论，先核对行动'})
    for request in state['requests'].values():
        # A v1 request has no safe, reconstructable action snapshot at creation.
        request['validated_context_digest'] = None
        request['covered_triggers'] = [request['trigger']]
    state['schema_version'] = SCHEMA_VERSION
    state.setdefault('migrations', []).append({
        'from_version': 1, 'to_version': SCHEMA_VERSION, 'source_digest': digest(original),
        'reason': '按行动ID保留多项措施；旧pending需显式复核；原始回执与完整旧状态保留',
        'source_snapshot': original})
    return state


def apply_command(state, command, payload):
    if payload.get('schema_version', SCHEMA_VERSION) not in INPUT_VERSIONS:
        raise StateError('不支持的输入 schema_version')
    if required(payload, 'store_ref') != state['store_ref']:
        raise StateError('store_ref 不一致；每个店铺须使用独立状态文件')
    if command in {'init', 'summary', 'migrate'}:
        return summary(state)
    if command == 'reconcile-history':
        if state['history_reconciliation']['status'] == 'complete':
            if state['history_reconciliation']['payload_digest'] != digest(payload):
                raise StateError('历史已对账，不可用新声明覆盖；通过后续问题/结果记录更新')
            return summary(state)
        at = required(payload, 'reviewed_at')
        timestamp(at)
        refs(payload)
        outcome = payload.get('outcome')
        seeds = payload.get('issues', [])
        if outcome not in {'no_relevant_actions', 'imported'} or not isinstance(seeds, list):
            raise StateError('历史对账须明确 no_relevant_actions 或 imported')
        if (outcome == 'no_relevant_actions' and seeds) or (outcome == 'imported' and not seeds):
            raise StateError('历史对账结论与导入问题不一致')
        ingest_signals(state, seeds, at, allow_requests=False)
        state['history_reconciliation'] = {
            'status': 'complete', 'reviewed_at': at, 'outcome': outcome,
            'evidence_refs': payload['evidence_refs'], 'payload_digest': digest(payload)}
        return summary(state)
    if command == 'ingest':
        if payload.get('schema_version') not in INPUT_VERSIONS:
            raise StateError('ingest 必须声明 schema_version=2；兼容旧输入1')
        run_id, at = required(payload, 'run_id'), required(payload, 'observed_at')
        timestamp(at)
        fingerprint = digest(payload)
        previous = state['runs'].get(run_id)
        if previous:
            if previous['payload_digest'] != fingerprint:
                raise StateError('run_id 已被不同输入使用，拒绝覆盖')
            return copy.deepcopy(previous['result'])
        if state['last_observed_at'] and timestamp(at) < timestamp(state['last_observed_at']):
            raise StateError('拒绝乱序旧运行覆盖当前证据；历史资料请作为引用对账')
        outcomes = ingest_signals(state, payload.get('signals'), at)
        due_reviews = scan_due_reviews(state, at)
        due_by_issue = {item['issue_id']: item for item in due_reviews}
        for item in outcomes:
            if item['issue_id'] in due_by_issue:
                item.update({key: due_by_issue[item['issue_id']][key] for key in ('decision', 'request_id')})
        state['last_observed_at'] = at
        result = {'run_id': run_id, 'store_ref': state['store_ref'], 'outcomes': outcomes,
                  'due_reviews': due_reviews,
                  'history_reconciliation_status': state['history_reconciliation']['status']}
        state['runs'][run_id] = {'payload_digest': fingerprint, 'result': copy.deepcopy(result)}
        return result
    if command == 'record-action':
        issue = state['issues'].get(required(payload, 'issue_id'))
        if issue is None:
            raise StateError('未知 issue_id')
        at = required(payload, 'recorded_at')
        if timestamp(at) < latest_issue_time(issue):
            raise StateError('行动记录早于最新问题状态，请先核对')
        refs(payload)
        required(payload, 'reason')
        actions = payload_actions(payload)
        if not actions:
            raise StateError('record-action 至少更新一项行动')
        review = payload.get('next_review_at')
        if issue['status'] != 'resolved' and not (review or issue['next_review_at'] or
                                                 any(a.get('next_review_at') for a in actions)):
            raise StateError('未结案问题的行动变更须明确复查时间')
        if review and timestamp(review) <= timestamp(at):
            raise StateError('行动复查时间必须晚于记录时间')
        for action in actions:
            if action['status'] in UNFINISHED_ACTIONS and timestamp(action['next_review_at']) <= timestamp(at):
                raise StateError('每项未完成行动的复查时间必须晚于记录时间')
        update_actions(issue, actions, at)
        if 'next_review_at' in payload:
            issue['next_review_at'] = review
        if unknown_actions(issue):
            issue['status'] = 'needs_evidence'
        elif observing_actions(issue):
            issue['status'] = 'observing'
        issue['decisions'].append({'type': 'action_record', 'at': at,
                                   'reason': payload['reason'], 'evidence_refs': payload['evidence_refs'],
                                   'related_actions': copy.deepcopy(actions), 'next_review_at': review})
        return summary(state)
    request, issue = get_request(state, payload)
    if command in {'cancel-pending', 'revalidate-request'}:
        if request['status'] != 'pending':
            raise StateError('只能处理未认领pending；已领取/派发/未知须先走原任务对账')
        at = required(payload, 'recorded_at' if command == 'cancel-pending' else 'reviewed_at')
        if timestamp(at) < max(latest_issue_time(issue), timestamp(request['created_at'])):
            raise StateError('请求决定早于最新问题/请求状态')
        refs(payload)
        required(payload, 'reason')
        if command == 'cancel-pending':
            outcome = payload.get('outcome')
            if outcome not in {'cancelled', 'superseded'}:
                raise StateError('取消结果须为 cancelled 或 superseded')
            if outcome == 'superseded':
                required(payload, 'replacement_ref')
            review = required(payload, 'next_review_at')
            if timestamp(review) <= timestamp(at):
                raise StateError('取消分析不等于业务问题结案；须明确未来复查时间')
            request['status'] = outcome
            request['cancellation'] = copy.deepcopy(payload)
            issue['next_review_at'] = review
            issue['decisions'].append({'type': 'request_' + outcome, 'at': at,
                                      'request_id': request['request_id'], 'reason': payload['reason'],
                                      'evidence_refs': payload['evidence_refs'],
                                      'replacement_ref': payload.get('replacement_ref')})
        else:
            if unknown_actions(issue):
                raise StateError('存在结果未知行动，先回读对账，不以请求复核绕过')
            current = context_digest(issue)
            if required(payload, 'context_digest') != current:
                raise StateError('复核上下文已变化；读取最新摘要后重新核对')
            request['validated_context_digest'] = current
            request['events'].append({'type': 'revalidated', 'record': copy.deepcopy(payload)})
        return copy.deepcopy(request)
    if command == 'claim':
        if request['status'] != 'pending':
            raise StateError('请求已被认领/派出/待对账，不得重复 spawn')
        at, claimant = required(payload, 'claimed_at'), required(payload, 'claimant')
        if timestamp(at) < max(latest_issue_time(issue), timestamp(request['created_at'])):
            raise StateError('认领时间早于最新问题/请求状态')
        if unknown_actions(issue):
            raise StateError('存在结果未知行动，先回读对账')
        if request['validated_context_digest'] != context_digest(issue):
            raise StateError('请求后行动或证据已变化；先 revalidate-request 留证复核或 cancel-pending')
        request['claim'] = {'token': uuid.uuid4().hex, 'claimant': claimant, 'at': at}
        request['status'] = 'claimed'
        return copy.deepcopy(request)
    if command == 'record-direct-start':
        if request['status'] != 'claimed' or not request['claim'] or request['claim']['token'] != required(payload, 'claim_token'):
            raise StateError('透明代行须先成功认领当前请求')
        if payload.get('reason') != 'no_subagent_tools':
            raise StateError('仅真实缺少子代理工具时允许总控透明代行')
        execution = {key: required(payload, key) for key in
                     ('executor_ref', 'capability_check_ref', 'started_at', 'reason')}
        timestamp(execution['started_at'])
        request['direct_execution'] = execution
        request['status'] = 'dispatched'
        return copy.deepcopy(request)
    if command == 'record-task-end':
        if request['status'] not in {'dispatched', 'unknown'} or not (request['dispatch'] or request['direct_execution']):
            raise StateError('须有真实派发或代行记录，再核对任务已停止')
        if payload.get('termination') not in {'failed', 'cancelled'} or payload.get('task_stopped') is not True:
            raise StateError('失败/取消须明确任务已停止，不能把未知当失败重试')
        refs(payload)
        required(payload, 'reason')
        at = required(payload, 'ended_at')
        review = required(payload, 'next_review_at')
        if timestamp(review) <= timestamp(at):
            raise StateError('任务终止后的复查时间必须在终止之后')
        request['status'] = payload['termination']
        request['events'].append({'type': 'task_end', 'record': copy.deepcopy(payload)})
        issue['status'], issue['next_review_at'] = 'needs_evidence', review
        return copy.deepcopy(request)
    if command == 'record-dispatch':
        if request['direct_execution']:
            raise StateError('该请求已记录透明代行，不能又登记真实派发')
        token = required(payload, 'claim_token')
        if not request['claim'] or request['claim']['token'] != token:
            raise StateError('认领 token 不匹配')
        receipt = {key: required(payload, key) for key in
                   ('agent_id', 'task_id', 'receipt_ref', 'dispatched_at')}
        timestamp(receipt['dispatched_at'])
        if request['dispatch']:
            if request['dispatch'] != receipt:
                raise StateError('已有不同派发回执')
            return copy.deepcopy(request)
        if request['status'] not in {'claimed', 'unknown'}:
            raise StateError('只能在成功认领且真实 spawn 后登记派发')
        request['dispatch'] = receipt
        request['status'] = 'dispatched'
        return copy.deepcopy(request)
    if command == 'mark-unknown':
        if request['status'] not in {'claimed', 'dispatched', 'unknown'}:
            raise StateError('仅认领或派发中的请求可标记结果未知')
        required(payload, 'reason')
        refs(payload)
        at = required(payload, 'recorded_at')
        timestamp(at)
        request['status'] = 'unknown'
        request['events'].append({'type': 'unknown', 'at': at,
                                  'reason': payload['reason'], 'evidence_refs': payload['evidence_refs']})
        return copy.deepcopy(request)
    if command == 'reconcile-request':
        if request['status'] not in {'claimed', 'unknown'}:
            raise StateError('仅认领中断/未知请求需要派发对账')
        refs(payload)
        required(payload, 'reason')
        at = required(payload, 'reviewed_at')
        timestamp(at)
        outcome = payload.get('outcome')
        if outcome == 'not_dispatched':
            if request['dispatch'] or request['direct_execution']:
                raise StateError('已有真实派发/代行回执，不能以未派发重试；须读取原任务结果')
            request['claim'] = None
            request['status'] = 'pending'
        elif outcome == 'dispatched':
            if request['direct_execution']:
                request['status'] = 'dispatched'
                request['events'].append({'type': 'reconciled_direct_execution', 'at': at,
                                          'reason': payload['reason'], 'evidence_refs': payload['evidence_refs']})
                return copy.deepcopy(request)
            receipt = {key: required(payload, key) for key in
                       ('agent_id', 'task_id', 'receipt_ref', 'dispatched_at')}
            timestamp(receipt['dispatched_at'])
            if request['dispatch'] and request['dispatch'] != receipt:
                raise StateError('对账回执与已记录派发不一致')
            request['dispatch'], request['status'] = receipt, 'dispatched'
        else:
            raise StateError('对账只能明确 dispatched 或 not_dispatched；仍未知时保留原状态')
        request['events'].append({'type': 'reconciled', 'at': at, 'outcome': outcome,
                                  'reason': payload['reason'], 'evidence_refs': payload['evidence_refs']})
        return copy.deepcopy(request)
    if command == 'record-result':
        fingerprint = digest(payload)
        if request['result']:
            if request['result']['payload_digest'] != fingerprint:
                raise StateError('已有不同分析结果；不能覆盖已验收决定')
            return copy.deepcopy(request)
        if request['status'] not in {'dispatched', 'unknown'} or not (request['dispatch'] or request['direct_execution']):
            raise StateError('须有真实派发或有据透明代行记录后才能登记分析结果')
        at = required(payload, 'completed_at')
        if timestamp(at) < latest_issue_time(issue):
            raise StateError('结果早于最新监测，须先核对本轮新增证据再验收')
        refs(payload)
        required(payload, 'conclusion')
        required(payload, 'decision_source')
        evaluation = payload.get('evaluation')
        if validate_signal(state['store_ref'], evaluation) != issue['issue_id']:
            raise StateError('分析结果 scope 与请求不一致')
        check_commitment_change(issue, evaluation)
        if (evaluation['scope']['problem_type'] == 'process_commitment' and
                timestamp(evaluation['process_commitment']['checked_at']) > timestamp(at)):
            raise StateError('过程事实核验时点不能晚于结果时间')
        current = assessment(evaluation)
        outcome = payload.get('outcome')
        if outcome not in {'observe', 'resolved', 'needs_evidence', 'open'}:
            raise StateError('分析结果 outcome 无效')
        if (outcome == 'resolved' and
                timestamp(evaluation['evidence']['cutoff']) < timestamp(issue['latest']['signal']['evidence']['cutoff'])):
            raise StateError('旧截止时间的结果不能结案最新问题')
        if outcome == 'resolved' and current != 'normal':
            raise StateError('只有完整、可比、成熟的正常证据及明确决定才能结案')
        review = payload.get('next_review_at')
        if review:
            if timestamp(review) <= timestamp(at):
                raise StateError('新的复查时间必须晚于结果时间')
        if outcome != 'resolved' and not review:
            raise StateError('未结案结果必须明确下一次复查时间，避免永久停滞')
        update_actions(issue, payload_actions(payload), at)
        unfinished = [a for a in issue['actions'].values() if a['status'] in UNFINISHED_ACTIONS]
        if outcome == 'resolved' and unfinished:
            raise StateError('仍有关联行动未完成/观察中/结果未知，先逐项核实，不能结案隐藏')
        if any(timestamp(a['next_review_at']) <= timestamp(at) for a in unfinished):
            raise StateError('到期行动须逐项给出结论或新的复查时间，不能只延后问题总日期')
        if payload.get('recommended_owner') is not None:
            if payload['recommended_owner'] not in {'operations_director', 'product_operations',
                                                    'traffic_operations', 'sales_owner', 'company_owner', 'unknown'}:
                raise StateError('recommended_owner 不是支持的建议去向')
            issue['recommended_owner'] = payload['recommended_owner']
        if timestamp(evaluation['evidence']['cutoff']) >= timestamp(issue['latest']['signal']['evidence']['cutoff']):
            issue['latest'] = {'assessment': current, 'evidence_hash': evidence_hash(evaluation['evidence']),
                               'signal': copy.deepcopy(evaluation)}
            issue['last_observed_at'] = at
        if outcome == 'resolved':
            issue['resolved_evidence_hash'] = evidence_hash(evaluation['evidence'])
        issue['next_review_at'] = review
        issue['status'] = {'observe': 'observing', 'resolved': 'resolved',
                           'needs_evidence': 'needs_evidence', 'open': 'open'}[outcome]
        request['status'] = 'completed'
        request['result'] = {'payload_digest': fingerprint, 'record': copy.deepcopy(payload)}
        issue['decisions'].append({'request_id': request['request_id'], 'at': at,
                                   'outcome': outcome, 'conclusion': payload['conclusion'],
                                   'evidence_refs': payload['evidence_refs']})
        return copy.deepcopy(request)
    raise StateError('未知命令: ' + command)


def save_atomic(path, state):
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=str(path.parent))
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def execute(state_path, command, payload):
    """Serialize THIS file's local transitions, not host/network/business operations."""
    if command not in COMMANDS or not isinstance(payload, dict):
        raise StateError('命令或输入格式错误')
    store_ref = required(payload, 'store_ref')
    path = Path(state_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Never unlink a lock file: concurrent processes must lock the same inode.
    with open(str(path) + '.lock', 'a+', encoding='utf-8') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if path.exists():
            state = json.loads(path.read_text(encoding='utf-8'))
            before = digest(state)
            migrate_state(state)
        elif command == 'init':
            state = new_state(store_ref)
            before = digest(state)
        else:
            raise StateError('状态不存在；先 init，再读取历史并 reconcile-history')
        result = apply_command(state, command, copy.deepcopy(payload))
        if not path.exists() or digest(state) != before:
            save_atomic(path, state)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('command', choices=COMMANDS)
    parser.add_argument('--input', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.state.resolve():
            raise StateError('命令输入不能是状态文件本身')
        result = execute(args.state, args.command, json.loads(args.input.read_text(encoding='utf-8')))
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('转化状态操作未完成: ' + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
