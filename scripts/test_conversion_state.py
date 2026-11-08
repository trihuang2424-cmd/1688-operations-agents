"""State/dispatch regression tests; all data and files are isolated simulations."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from conversion_state import StateError, digest, evidence_hash, execute


STORE = 'simulation-only-store'
SCRIPT = Path(__file__).with_name('conversion_state.py')


def at(day=1, hour=9):
    return '2026-11-%02dT%02d:00:00+08:00' % (day, hour)


def signal(value='anomaly', content='base', day=1, problem='conversion'):
    return {
        'scope': {'object_type': 'product', 'object_id': 'simulation-product',
                  'problem_type': problem, 'cohort_id': 'comparable-mature-cohort',
                  'metric_id': 'inquiry-order-rate'},
        'signal': value,
        'evidence': {'source': 'simulation', 'period_start': '2026-10-21',
                     'period_end': '2026-10-27', 'cutoff': at(day, 8),
                     'definition': 'same scoped mature cohort', 'version': 'v1',
                     'content_fingerprint': digest(content), 'refs': ['simulation-receipt.json']},
        'quality': {'coverage': 'complete', 'comparability': 'comparable',
                    'sample': 'sufficient', 'maturity': 'mature'},
        'criteria': {'source': 'simulation-policy-v1', 'condition': 'test supplied condition'},
    }


def action(status='observing'):
    return {'action_id': 'simulation-action', 'status': status, 'evidence_refs': ['simulation-action.json']}


def process_signal(stage='quotation', status='missed', day=1):
    item = signal('unknown' if status == 'unknown' else 'normal' if status in {'fulfilled', 'not_due'} else 'anomaly',
                  content=stage + status, day=day, problem='process_commitment')
    item['scope']['metric_id'] = stage + '-commitment'
    item['quality']['maturity'] = 'not_applicable'
    item['process_commitment'] = {'stage': stage, 'commitment_ref': 'confirmed-commitment.json',
                                  'due_at': at(1, 7), 'checked_at': at(day, 8),
                                  'expected_event': stage + ' confirmation', 'observed_status': status}
    return item


class ConversionStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / 'state.json'
        self.command('init')

    def command(self, command, **payload):
        return execute(self.path, command, {'store_ref': STORE, **payload})

    def reconcile(self, issues=None):
        return self.command('reconcile-history', reviewed_at=at(), evidence_refs=['simulation-history.json'],
                            outcome='imported' if issues else 'no_relevant_actions', issues=issues or [])

    def ingest(self, number=1, item=None, day=1, **extra):
        return self.command('ingest', schema_version=1, run_id='run-%s' % number,
                            observed_at=at(day), signals=[item or signal()], **extra)

    def state(self):
        return json.loads(self.path.read_text())

    def pending(self, item=None):
        self.reconcile()
        output = self.ingest(item=item)
        return output['outcomes'][0]['request_id']

    def dispatched(self, request_id=None):
        request_id = request_id or self.pending()
        claim = self.command('claim', request_id=request_id, claimed_at=at(1, 10), claimant='simulation-executor')
        token = claim['claim']['token']
        self.command('record-dispatch', request_id=request_id, claim_token=token,
                     agent_id='simulation-agent', task_id='simulation-task',
                     receipt_ref='simulation-spawn.json', dispatched_at=at(1, 10))
        return request_id

    def result(self, request_id, outcome='observe', evaluation=None, day=1, **extra):
        payload = dict(request_id=request_id, outcome=outcome, completed_at=at(day, 11),
                       conclusion='simulation conclusion', decision_source='simulation-policy',
                       evidence_refs=['simulation-analysis.json'], evaluation=evaluation or signal())
        if outcome != 'resolved':
            payload['next_review_at'] = at(day + 5)
        payload.update(extra)
        return self.command('record-result', **payload)

    def revalidate(self, request_id, day=2, **extra):
        card = self.command('summary')['issues'][0]
        payload = dict(request_id=request_id, reviewed_at=at(day, 10), reason='current evidence and actions reviewed',
                       evidence_refs=['context-review.json'], context_digest=card['context_digest'])
        payload.update(extra)
        return self.command('revalidate-request', **payload)

    def ingest_empty(self, day=2):
        return self.command('ingest', schema_version=2, run_id='empty-%s' % day, observed_at=at(day), signals=[])

    def test_bootstrap_requires_evidenced_history_reconciliation(self):
        result = self.ingest()
        self.assertEqual(result['outcomes'][0]['decision'], 'reconcile_history')
        self.assertFalse(self.state()['requests'])
        with self.assertRaises(StateError):
            self.command('reconcile-history', reviewed_at=at(), outcome='no_relevant_actions', issues=[])
        self.reconcile()
        self.assertEqual(self.ingest(2)['outcomes'][0]['decision'], 'analysis_requested')

    def test_same_run_replay_is_idempotent_and_changed_payload_is_rejected(self):
        self.reconcile()
        result = self.ingest()
        before = self.path.read_bytes()
        self.assertEqual(self.ingest(), result)
        self.assertEqual(before, self.path.read_bytes())
        with self.assertRaises(StateError):
            self.ingest(item=signal(content='different'))
        self.assertEqual(before, self.path.read_bytes())

    def test_scope_survives_daily_windows_and_pending_is_not_dispatched(self):
        request_id = self.pending()
        next_signal = signal(day=2, content='new day rates')
        result = self.ingest(2, next_signal, day=2)
        self.assertEqual(result['outcomes'][0]['request_id'], request_id)
        self.assertEqual(len(self.state()['issues']), 1)
        self.assertIsNone(self.state()['requests'][request_id]['dispatch'])

    def test_retrieval_time_and_file_path_do_not_make_new_evidence(self):
        original = signal()
        changed = copy.deepcopy(original)
        changed['evidence'].update(retrieved_at=at(2), refs=['another-path.json'])
        self.assertEqual(evidence_hash(original['evidence']), evidence_hash(changed['evidence']))
        request_id = self.dispatched(self.pending(original))
        self.result(request_id)
        changed['new_fact'] = {'id': 'not-a-real-new-fact', 'reason': 'new retrieval',
                               'evidence_refs': ['another-path.json']}
        self.assertEqual(self.ingest(2, changed, day=2)['outcomes'][0]['decision'], 'hold')
        self.assertEqual(len(self.state()['requests']), 1)

    def test_rolling_evidence_without_material_change_does_not_repeat_analysis(self):
        request_id = self.dispatched()
        self.result(request_id, outcome='open')
        self.assertEqual(self.ingest(2, signal(day=2, content='new rates'), day=2)['outcomes'][0]['decision'], 'hold')
        self.assertEqual(len(self.state()['requests']), 1)

    def test_existing_action_blocks_repeated_bad_metrics_until_review(self):
        item = signal()
        item.update(related_action=action(), next_review_at=at(6))
        self.reconcile([item])
        for day in (2, 3, 4):
            result = self.ingest(day, signal(day=day, content='day-%s' % day), day)
            self.assertEqual(result['outcomes'][0]['decision'], 'observe_existing_action')
        self.assertFalse(self.state()['requests'])
        result = self.ingest(6, signal(day=6), 6)
        self.assertEqual(result['outcomes'][0]['decision'], 'analysis_requested')
        self.ingest(7, signal(day=7), 7)
        self.assertEqual(len(self.state()['requests']), 1)

    def test_material_fact_or_intervention_can_break_observation(self):
        for name in ('new_fact', 'intervention'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                self.path = Path(temporary) / 'state.json'
                self.command('init')
                item = signal()
                item.update(related_action=action(), next_review_at=at(9))
                self.reconcile([item])
                changed = signal(day=2, content='new actual error')
                changed[name] = {'id': 'new-error', 'reason': 'material factual error',
                                 'evidence_refs': ['new-fact.json'], 'criteria_source': 'policy-v1'}
                result = self.ingest(2, changed, 2)
                self.assertEqual(result['outcomes'][0]['decision'], 'analysis_requested')

    def test_missing_mixed_and_small_samples_never_become_business_failure(self):
        for field, value in (('coverage', 'missing'), ('comparability', 'mixed'), ('sample', 'insufficient')):
            with self.subTest(field=field):
                item = signal()
                item['scope']['metric_id'] = field
                item['quality'][field] = value
                item['next_review_at'] = at(3)
                self.reconcile() if self.state()['history_reconciliation']['status'] == 'required' else None
                result = self.ingest(field, item)
                self.assertEqual(result['outcomes'][0]['assessment'], 'unknown')
                self.assertIsNone(result['outcomes'][0]['request_id'])
        self.assertFalse(self.state()['requests'])

    def test_immature_conversion_observes_but_factual_response_can_analyze(self):
        self.reconcile()
        item = signal()
        item['quality']['maturity'] = 'immature'
        item['next_review_at'] = at(3)
        self.assertEqual(self.ingest(1, item)['outcomes'][0]['decision'], 'observe_immature')
        factual = signal(problem='response')
        factual['quality']['maturity'] = 'not_applicable'
        self.assertEqual(self.ingest(2, factual)['outcomes'][0]['decision'], 'analysis_requested')

    def test_not_applicable_cannot_bypass_conversion_maturity(self):
        self.reconcile()
        item = signal()
        item['quality']['maturity'] = 'not_applicable'
        item['next_review_at'] = at(3)
        self.assertEqual(self.ingest(item=item)['outcomes'][0]['assessment'], 'unknown')

    def test_unknown_and_immature_review_due_only_once(self):
        for quality in ('missing', 'immature'):
            with self.subTest(quality=quality), tempfile.TemporaryDirectory() as temporary:
                self.path = Path(temporary) / 'state.json'
                self.command('init')
                self.reconcile()
                item = signal()
                item['quality']['coverage' if quality == 'missing' else 'maturity'] = quality
                item['next_review_at'] = at(2)
                self.ingest(item=item)
                due = self.ingest(2, item, 2)
                self.assertEqual(due['outcomes'][0]['decision'], 'analysis_requested')
                self.ingest(3, item, 3)
                self.assertEqual(len(self.state()['requests']), 1)

    def test_unfinished_signal_and_historical_actions_need_review_date(self):
        for item in (signal('unknown'), {**signal(), 'related_action': action()}):
            with self.subTest(item=item):
                before = self.path.read_bytes()
                with self.assertRaises(StateError):
                    self.reconcile([item])
                self.assertEqual(before, self.path.read_bytes())

    def test_empty_or_normal_input_does_not_auto_resolve(self):
        self.pending()
        self.command('ingest', schema_version=1, run_id='empty', observed_at=at(2), signals=[])
        self.ingest(3, signal('normal', day=3), 3)
        self.assertNotEqual(next(iter(self.state()['issues'].values()))['status'], 'resolved')

    def test_result_requires_real_dispatch_and_full_normal_evidence(self):
        request_id = self.pending()
        with self.assertRaises(StateError):
            self.result(request_id)
        self.dispatched(request_id)
        bad = signal('normal')
        bad['quality']['coverage'] = 'partial'
        with self.assertRaises(StateError):
            self.result(request_id, 'resolved', bad)
        self.result(request_id, 'resolved', signal('normal', content='recovered'))
        summary = self.command('summary')
        self.assertEqual(summary['issue_counts']['resolved'], 1)
        self.assertFalse(summary['issues'])
        issue = next(iter(self.state()['issues'].values()))
        self.assertEqual(issue['latest']['assessment'], 'normal')

    def test_resolved_issue_can_recur_on_new_mature_evidence(self):
        request_id = self.dispatched()
        self.result(request_id, 'resolved', signal('normal', content='recovered'))
        result = self.ingest(2, signal(content='new regression', day=2), 2)
        self.assertEqual(result['outcomes'][0]['decision'], 'analysis_requested')
        self.assertEqual(len(self.state()['issues']), 1)
        self.assertEqual(len(self.state()['requests']), 2)

    def test_stale_cached_anomaly_cannot_reopen_resolved_issue(self):
        request_id = self.dispatched()
        good = signal('normal', content='recovered', day=2)
        self.result(request_id, 'resolved', good, day=2)
        result = self.ingest(3, signal(), 3)
        self.assertEqual(result['outcomes'][0]['decision'], 'stale_evidence')
        self.assertEqual(len(self.state()['requests']), 1)
        issue = next(iter(self.state()['issues'].values()))
        self.assertEqual(issue['status'], 'resolved')
        self.assertEqual(issue['latest']['assessment'], 'normal')

    def test_old_results_cannot_override_latest_monitoring(self):
        request_id = self.dispatched()
        self.ingest(2, signal(content='new anomaly', day=2), 2)
        with self.assertRaises(StateError):
            self.result(request_id, 'resolved', signal('normal'), day=1)
        with self.assertRaises(StateError):
            self.result(request_id, 'resolved', signal('normal'), day=2)

    def test_every_nonterminal_result_needs_a_future_review(self):
        request_id = self.dispatched()
        for outcome in ('observe', 'open', 'needs_evidence'):
            for review in (None, at(1)):
                with self.subTest(outcome=outcome, review=review), self.assertRaises(StateError):
                    self.result(request_id, outcome, next_review_at=review)

    def test_observing_action_can_be_reconciled_without_fabricating_agent(self):
        item = signal()
        item.update(related_action=action('unknown'), next_review_at=at(4))
        self.reconcile([item])
        self.assertEqual(self.ingest()['outcomes'][0]['decision'], 'reconcile_action')
        key = next(iter(self.state()['issues']))
        self.command('record-action', issue_id=key, recorded_at=at(1, 10), reason='verified action receipt',
                     evidence_refs=['action-readback.json'], related_action=action('completed'), next_review_at=at(3))
        self.assertFalse(self.state()['requests'])
        self.assertEqual(self.ingest(2, signal(day=2), 2)['outcomes'][0]['decision'], 'analysis_requested')

    def test_stale_action_and_monitoring_cannot_override_newer_action(self):
        self.pending()
        key = next(iter(self.state()['issues']))
        self.command('record-action', issue_id=key, recorded_at=at(1, 10), reason='new action verified',
                     evidence_refs=['new-action.json'], related_action=action(), next_review_at=at(4))
        before = self.path.read_bytes()
        with self.assertRaises(StateError):
            self.command('record-action', issue_id=key, recorded_at=at(1, 9), reason='stale action receipt',
                         evidence_refs=['old-action.json'], related_action=action('completed'), next_review_at=at(3))
        self.assertEqual(before, self.path.read_bytes())
        with self.assertRaises(StateError):
            self.ingest(2, signal(), 1)
        self.assertEqual(before, self.path.read_bytes())
        self.ingest(3, signal(day=2), 2)
        self.assertEqual(self.state()['issues'][key]['actions']['simulation-action'],
                         {**action(), 'next_review_at': at(4)})

    def test_claim_crash_requires_reconciliation_and_invalidates_old_token(self):
        request_id = self.pending()
        claim = self.command('claim', request_id=request_id, claimant='one', claimed_at=at(1, 10))
        self.command('mark-unknown', request_id=request_id, recorded_at=at(1, 11), reason='interrupted', evidence_refs=['host.json'])
        self.ingest(2, signal(day=2), 2)
        with self.assertRaises(StateError):
            self.command('claim', request_id=request_id, claimant='two', claimed_at=at(2, 10))
        self.command('reconcile-request', request_id=request_id, reviewed_at=at(2, 10), reason='host confirms no spawn',
                     evidence_refs=['host-empty.json'], outcome='not_dispatched')
        self.revalidate(request_id)
        new_claim = self.command('claim', request_id=request_id, claimant='two', claimed_at=at(2, 10))
        self.assertNotEqual(claim['claim']['token'], new_claim['claim']['token'])
        with self.assertRaises(StateError):
            self.command('record-dispatch', request_id=request_id, claim_token=claim['claim']['token'], agent_id='stale',
                         task_id='stale', receipt_ref='stale.json', dispatched_at=at(2, 10))

    def test_dispatched_unknown_cannot_be_reissued_as_not_dispatched(self):
        request_id = self.dispatched()
        self.command('mark-unknown', request_id=request_id, recorded_at=at(1, 11), reason='lost result', evidence_refs=['host.json'])
        with self.assertRaises(StateError):
            self.command('reconcile-request', request_id=request_id, reviewed_at=at(2), reason='not allowed',
                         evidence_refs=['host.json'], outcome='not_dispatched')
        self.assertEqual(self.state()['requests'][request_id]['status'], 'unknown')

    def test_failed_task_requires_stopped_evidence_before_retry(self):
        request_id = self.dispatched()
        with self.assertRaises(StateError):
            self.command('record-task-end', request_id=request_id, ended_at=at(1, 11), termination='failed',
                         task_stopped=False, reason='maybe timeout', evidence_refs=['host.json'], next_review_at=at(2))
        self.command('record-task-end', request_id=request_id, ended_at=at(1, 11), termination='failed',
                     task_stopped=True, reason='host confirmed ended', evidence_refs=['host.json'], next_review_at=at(2))
        self.assertEqual(self.state()['requests'][request_id]['status'], 'failed')
        self.assertIsNone(self.state()['requests'][request_id]['result'])
        self.assertEqual(self.ingest(2, signal(day=2), 2)['outcomes'][0]['decision'], 'analysis_requested')

    def test_transparent_direct_fallback_does_not_fabricate_dispatch(self):
        request_id = self.pending()
        claim = self.command('claim', request_id=request_id, claimant='director', claimed_at=at(1, 10))
        self.command('record-direct-start', request_id=request_id, claim_token=claim['claim']['token'],
                     reason='no_subagent_tools', executor_ref='simulation-current-task',
                     capability_check_ref='host-capabilities.json', started_at=at(1, 10))
        card = self.command('summary')['issues'][0]
        self.assertEqual(card['request']['execution_mode'], 'director_fallback')
        self.assertIsNone(self.state()['requests'][request_id]['dispatch'])
        self.result(request_id)

    def test_recommended_owner_does_not_change_actual_coordination_owner(self):
        request_id = self.dispatched()
        self.result(request_id, recommended_owner='sales_owner')
        card = self.command('summary')['issues'][0]
        self.assertEqual(card['owner'], 'operations_director')
        self.assertEqual(card['recommended_owner'], 'sales_owner')
        self.assertIn('quality', card)
        self.assertIn('criteria', card)

    def test_result_replay_is_idempotent_but_conflicting_decision_rejected(self):
        request_id = self.dispatched()
        first = self.result(request_id)
        before = self.path.read_bytes()
        self.assertEqual(self.result(request_id), first)
        self.assertEqual(before, self.path.read_bytes())
        with self.assertRaises(StateError):
            self.result(request_id, conclusion='different decision')
        self.assertEqual(before, self.path.read_bytes())

    def test_dispatch_receipt_replay_cannot_replace_actual_task(self):
        request_id = self.dispatched()
        request = self.state()['requests'][request_id]
        payload = {'request_id': request_id, 'claim_token': request['claim']['token'], **request['dispatch']}
        before = self.path.read_bytes()
        self.command('record-dispatch', **payload)
        self.assertEqual(before, self.path.read_bytes())
        with self.assertRaises(StateError):
            self.command('record-dispatch', **{**payload, 'task_id': 'different-task'})
        self.assertEqual(before, self.path.read_bytes())

    def test_store_isolation_and_atomic_bad_batch(self):
        self.reconcile()
        before = self.path.read_bytes()
        with self.assertRaises(StateError):
            self.command('summary', store_ref='other-store')
        broken = signal()
        broken['quality'].pop('coverage')
        with self.assertRaises(StateError):
            self.command('ingest', schema_version=1, run_id='bad', observed_at=at(), signals=[signal(), broken])
        self.assertEqual(before, self.path.read_bytes())

    def test_different_scopes_separate_and_duplicate_scopes_rejected(self):
        self.reconcile()
        second = signal()
        second['scope']['object_id'] = 'different-product'
        self.command('ingest', schema_version=1, run_id='two', observed_at=at(), signals=[signal(), second])
        self.assertEqual(len(self.state()['issues']), 2)
        before = self.path.read_bytes()
        with self.assertRaises(StateError):
            self.command('ingest', schema_version=1, run_id='dup', observed_at=at(), signals=[signal(), signal()])
        self.assertEqual(before, self.path.read_bytes())

    def test_old_runs_and_naive_timestamps_rejected(self):
        self.reconcile()
        self.ingest(2, day=2)
        with self.assertRaises(StateError):
            self.ingest(1, day=1)
        with self.assertRaises(StateError):
            self.command('ingest', schema_version=1, run_id='naive', observed_at='2026-11-03T09:00:00', signals=[])

    def test_historical_import_does_not_replace_newer_monitoring(self):
        newer = signal(content='new observation', day=2)
        self.ingest(2, newer, 2)
        old = signal()
        old.update(related_action=action(), next_review_at=at(5))
        self.reconcile([old])
        issue = next(iter(self.state()['issues'].values()))
        self.assertEqual(issue['latest']['evidence_hash'], evidence_hash(newer['evidence']))
        self.assertEqual(issue['actions']['simulation-action'], {**action(), 'next_review_at': at(5)})
        self.assertFalse(self.state()['requests'])

    def test_confirmed_process_deadlines_do_not_wait_for_order_maturity(self):
        self.reconcile()
        for stage in ('followup', 'quotation', 'sample', 'fulfillment'):
            result = self.ingest(stage, process_signal(stage))
            self.assertEqual(result['outcomes'][0]['decision'], 'analysis_requested')
            self.assertEqual(result['outcomes'][0]['assessment'], 'anomaly')
        for problem in ('conversion', 'followup', 'order', 'repurchase'):
            item = signal(problem=problem)
            item['quality']['maturity'] = 'not_applicable'
            item['next_review_at'] = at(3)
            result = self.ingest('outcome-' + problem, item)
            self.assertEqual(result['outcomes'][0]['assessment'], 'unknown')
            self.assertIsNone(result['outcomes'][0]['request_id'])

    def test_process_deadline_requires_real_due_fact_and_present_time(self):
        self.reconcile()
        for change in ('future_due', 'future_check', 'no_commitment', 'unknown_as_missed'):
            item = process_signal()
            fact = item['process_commitment']
            if change == 'future_due':
                fact['due_at'] = at(2)
            elif change == 'future_check':
                fact['checked_at'] = at(2)
            elif change == 'no_commitment':
                fact.pop('commitment_ref')
            else:
                fact['observed_status'] = 'unknown'
            before = self.path.read_bytes()
            with self.subTest(change=change), self.assertRaises(StateError):
                self.ingest(change, item)
            self.assertEqual(self.path.read_bytes(), before)
        missing = process_signal(status='unknown')
        missing['next_review_at'] = at(2)
        result = self.ingest('missing', missing)
        self.assertEqual(result['outcomes'][0]['assessment'], 'unknown')
        self.assertIsNone(result['outcomes'][0]['request_id'])

    def test_process_remediation_preserves_original_missed_commitment(self):
        original = process_signal()
        request_id = self.dispatched(self.pending(original))
        fixed = process_signal(status='fulfilled', day=2)
        self.result(request_id, 'resolved', fixed, day=2)
        issue = next(iter(self.state()['issues'].values()))
        self.assertEqual(issue['status'], 'resolved')
        self.assertEqual(issue['observations'][0]['assessment'], 'anomaly')
        self.assertEqual(issue['latest']['signal']['process_commitment']['due_at'], original['process_commitment']['due_at'])

    def test_empty_run_reviews_due_issues_without_fabricating_new_evidence(self):
        self.reconcile()
        item = signal('unknown')
        item['next_review_at'] = at(2)
        self.ingest(item=item)
        before = next(iter(self.state()['issues'].values()))
        due = self.ingest_empty(2)
        self.assertEqual(due['outcomes'], [])
        self.assertEqual(due['due_reviews'][0]['decision'], 'analysis_requested')
        after = next(iter(self.state()['issues'].values()))
        for field in ('latest', 'observations', 'last_observed_at'):
            self.assertEqual(before[field], after[field])
        replay = self.ingest_empty(2)
        self.assertEqual(replay, due)
        self.ingest_empty(3)
        self.assertEqual(len(self.state()['requests']), 1)

    def test_due_missing_product_is_checked_when_other_product_returns(self):
        self.reconcile()
        item = signal('unknown')
        item['next_review_at'] = at(2)
        self.ingest(item=item)
        other = signal('normal', day=2)
        other['scope']['object_id'] = 'other-product'
        result = self.ingest(2, other, 2)
        self.assertEqual(result['outcomes'][0]['decision'], 'normal_no_issue')
        self.assertEqual(result['due_reviews'][0]['decision'], 'analysis_requested')

    def test_missing_signal_does_not_bypass_unknown_action_or_history_check(self):
        item = signal()
        item.update(related_action=action('unknown'), next_review_at=at(2))
        self.ingest(item=item)
        self.assertEqual(self.ingest_empty(2)['due_reviews'][0]['decision'], 'reconcile_history')
        self.reconcile()
        self.assertEqual(self.ingest_empty(3)['due_reviews'][0]['decision'], 'reconcile_action')
        self.assertFalse(self.state()['requests'])

    def test_multiple_actions_keep_unknown_protection_and_independent_dates(self):
        old = {**action('unknown'), 'action_id': 'product-change', 'next_review_at': at(3)}
        second = {**action(), 'action_id': 'reception-change', 'next_review_at': at(5)}
        item = {**signal(), 'related_actions': [old], 'next_review_at': at(4)}
        self.reconcile([item])
        key = next(iter(self.state()['issues']))
        self.command('record-action', issue_id=key, recorded_at=at(1, 10), reason='independent reception change',
                     evidence_refs=['reception.json'], related_actions=[second])
        self.command('record-action', issue_id=key, recorded_at=at(1, 11), reason='reception complete',
                     evidence_refs=['reception-done.json'], related_actions=[{**second, 'status': 'completed'}])
        actions = self.state()['issues'][key]['actions']
        self.assertEqual(actions['product-change'], old)
        self.assertEqual(actions['reception-change']['next_review_at'], at(5))
        result = self.ingest_empty(3)
        self.assertEqual(result['due_reviews'][0]['decision'], 'reconcile_action')
        self.assertFalse(self.state()['requests'])

    def test_multiple_observations_have_separate_due_triggers_without_duplicate_request(self):
        actions = [{**action(), 'action_id': 'product', 'next_review_at': at(3)},
                   {**action(), 'action_id': 'traffic', 'next_review_at': at(5)}]
        self.reconcile([{**signal(), 'related_actions': actions}])
        self.assertEqual(self.ingest(2, signal(day=2), 2)['outcomes'][0]['decision'], 'observe_existing_action')
        due = self.ingest_empty(3)
        request_id = due['due_reviews'][0]['request_id']
        self.assertEqual(due['due_reviews'][0]['due_triggers'], ['action-review:product:' + at(3)])
        self.ingest_empty(5)
        self.assertEqual(len(self.state()['requests']), 1)
        self.assertEqual(self.state()['requests'][request_id]['status'], 'pending')

    def test_resolved_cannot_hide_unfinished_actions(self):
        request_id = self.dispatched()
        key = next(iter(self.state()['issues']))
        self.command('record-action', issue_id=key, recorded_at=at(1, 10), reason='real action now observing',
                     evidence_refs=['change.json'], related_actions=[{**action(), 'next_review_at': at(4)}])
        before = self.path.read_bytes()
        with self.assertRaises(StateError):
            self.result(request_id, 'resolved', signal('normal'))
        self.assertEqual(self.path.read_bytes(), before)
        self.result(request_id, 'resolved', signal('normal'),
                    related_actions=[{**action('completed'), 'next_review_at': None}])
        self.assertEqual(self.command('summary')['issue_counts']['resolved'], 1)

    def test_result_must_explicitly_reassess_each_due_action(self):
        item = {**signal(), 'related_actions': [{**action(), 'next_review_at': at(2)}]}
        self.reconcile([item])
        request_id = self.ingest_empty(2)['due_reviews'][0]['request_id']
        claim = self.command('claim', request_id=request_id, claimant='worker', claimed_at=at(2, 10))
        self.command('record-dispatch', request_id=request_id, claim_token=claim['claim']['token'],
                     agent_id='worker', task_id='task', receipt_ref='receipt.json', dispatched_at=at(2, 10))
        with self.assertRaises(StateError):
            self.result(request_id, day=2)
        self.result(request_id, day=2, related_actions=[{**action(), 'next_review_at': at(4)}])
        self.assertEqual(self.command('summary')['issues'][0]['related_actions'][0]['next_review_at'], at(4))

    def test_pending_changed_evidence_requires_explicit_revalidation(self):
        request_id = self.pending()
        self.ingest(2, signal(content='new facts', day=2), 2)
        with self.assertRaises(StateError):
            self.command('claim', request_id=request_id, claimant='worker', claimed_at=at(2, 10))
        with self.assertRaises(StateError):
            self.revalidate(request_id, context_digest='stale-context')
        self.revalidate(request_id)
        self.assertEqual(self.command('claim', request_id=request_id, claimant='worker', claimed_at=at(2, 10))['status'], 'claimed')

    def test_completed_action_old_review_date_does_not_spawn_extra_analysis(self):
        request_id = self.dispatched()
        self.result(request_id, outcome='open',
                    related_actions=[{**action('completed'), 'next_review_at': at(1)}])
        self.assertFalse(self.ingest_empty(2)['due_reviews'])
        self.assertEqual(len(self.state()['requests']), 1)
        self.assertEqual(self.ingest_empty(6)['due_reviews'][0]['decision'], 'analysis_requested')

    def test_process_commitment_cannot_be_silently_postponed(self):
        self.reconcile()
        original = process_signal()
        self.ingest(item=original)
        changed = process_signal(status='not_due', day=2)
        changed['process_commitment']['due_at'] = at(3)
        with self.assertRaises(StateError):
            self.ingest(2, changed, 2)
        changed['commitment_change'] = {'reason': 'buyer accepted a new documented deadline',
                                        'evidence_refs': ['agreed-deadline.json']}
        self.ingest(2, changed, 2)
        history = next(iter(self.state()['issues'].values()))['observations']
        self.assertEqual(history[0]['process_commitment']['observed_status'], 'missed')
        self.assertEqual(history[0]['process_commitment']['due_at'], at(1, 7))
        self.assertEqual(history[-1]['commitment_change'], changed['commitment_change'])

    def test_pending_changed_action_requires_review_and_unknown_cannot_be_waived(self):
        request_id = self.pending()
        key = next(iter(self.state()['issues']))
        self.command('record-action', issue_id=key, recorded_at=at(1, 10), reason='new execution unknown',
                     evidence_refs=['timeout.json'], related_actions=[{**action('unknown'), 'next_review_at': at(4)}])
        with self.assertRaises(StateError):
            self.command('claim', request_id=request_id, claimant='worker', claimed_at=at(1, 11))
        with self.assertRaises(StateError):
            self.revalidate(request_id, day=1)
        self.command('record-action', issue_id=key, recorded_at=at(2), reason='readback confirms applied',
                     evidence_refs=['readback.json'], related_actions=[{**action(), 'next_review_at': at(4)}])
        self.revalidate(request_id)
        self.command('claim', request_id=request_id, claimant='worker', claimed_at=at(2, 10))

    def test_pending_cancel_and_strategy_replacement_keep_evidence(self):
        request_id = self.pending()
        result = self.command('cancel-pending', request_id=request_id, recorded_at=at(1, 10),
                              outcome='superseded', replacement_ref='strategy-v2.json', reason='different product priority',
                              evidence_refs=['approved-strategy.json'], next_review_at=at(4))
        self.assertEqual(result['status'], 'superseded')
        self.assertEqual(result['cancellation']['replacement_ref'], 'strategy-v2.json')
        self.assertFalse(self.command('summary')['pending_requests'])
        with self.assertRaises(StateError):
            self.command('claim', request_id=request_id, claimant='worker', claimed_at=at(2))
        self.assertFalse(self.ingest_empty(2)['due_reviews'])
        new_id = self.ingest_empty(4)['due_reviews'][0]['request_id']
        self.assertNotEqual(new_id, request_id)
        self.command('cancel-pending', request_id=new_id, recorded_at=at(4, 10), outcome='cancelled',
                     reason='await company facts', evidence_refs=['company.json'], next_review_at=at(7))
        self.assertEqual(self.state()['requests'][new_id]['status'], 'cancelled')

    def test_pending_cancel_cannot_bypass_claimed_or_unknown_recovery(self):
        request_id = self.pending()
        self.command('claim', request_id=request_id, claimant='worker', claimed_at=at(1, 10))
        for state in ('claimed', 'unknown'):
            if state == 'unknown':
                self.command('mark-unknown', request_id=request_id, recorded_at=at(1, 11), reason='host interrupted',
                             evidence_refs=['host.json'])
            with self.subTest(state=state), self.assertRaises(StateError):
                self.command('cancel-pending', request_id=request_id, recorded_at=at(2), outcome='cancelled',
                             reason='cannot assume unstarted', evidence_refs=['host.json'], next_review_at=at(4))

    def test_v1_migration_preserves_old_actions_requests_and_run_replay(self):
        request_id = self.pending()
        legacy = self.state()
        legacy['schema_version'] = 1
        issue = next(iter(legacy['issues'].values()))
        issue.pop('actions')
        issue['related_action'] = action('completed')
        issue['next_review_at'] = at(4)
        issue['decisions'].append({'type': 'action_record', 'at': at(1, 8), 'reason': 'prior product change',
                                   'evidence_refs': ['prior.json'],
                                   'related_action': {**action(), 'action_id': 'earlier-action'}})
        for request in legacy['requests'].values():
            request.pop('validated_context_digest')
            request.pop('covered_triggers')
        # A v1 run returned no due_reviews; replay must return its original receipt.
        legacy['runs']['run-1']['result'].pop('due_reviews')
        self.path.write_text(json.dumps(legacy))
        before = self.path.read_bytes()
        with self.assertRaises(StateError):
            self.command('summary', store_ref='wrong-store')
        self.assertEqual(before, self.path.read_bytes())
        summary = self.command('summary')
        migrated = self.state()
        self.assertEqual(migrated['schema_version'], 2)
        self.assertEqual(migrated['migrations'][0]['source_snapshot'], legacy)
        self.assertEqual(migrated['requests'][request_id]['status'], 'pending')
        migrated_issue = next(iter(migrated['issues'].values()))
        self.assertEqual(migrated_issue['actions']['simulation-action']['next_review_at'], at(4))
        self.assertEqual(migrated_issue['actions']['earlier-action']['status'], 'unknown')
        self.assertEqual(summary['issues'][0]['request']['needs_revalidation'], True)
        self.assertEqual(self.ingest(), legacy['runs']['run-1']['result'])
        self.command('summary')
        self.assertEqual(len(self.state()['migrations']), 1)

    def test_v1_claim_recovery_keeps_token_and_receipt(self):
        request_id = self.dispatched()
        legacy = self.state()
        legacy['schema_version'] = 1
        issue = next(iter(legacy['issues'].values()))
        issue.pop('actions')
        issue['related_action'] = None
        request = legacy['requests'][request_id]
        request.pop('validated_context_digest')
        request.pop('covered_triggers')
        self.path.write_text(json.dumps(legacy))
        self.command('summary')
        migrated = self.state()['requests'][request_id]
        self.assertEqual(migrated['claim'], request['claim'])
        self.assertEqual(migrated['dispatch'], request['dispatch'])
        self.result(request_id)

    def test_concurrent_processes_only_one_claim_succeeds(self):
        request_id = self.pending()
        paths = []
        for number in range(8):
            path = Path(self.temporary.name) / ('claim-%s.json' % number)
            path.write_text(json.dumps({'store_ref': STORE, 'request_id': request_id,
                                       'claimant': 'worker-%s' % number, 'claimed_at': at(1, 10)}))
            paths.append(path)
        def claim(path):
            return subprocess.run([sys.executable, str(SCRIPT), '--state', str(self.path), 'claim',
                                   '--input', str(path)], capture_output=True)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(claim, paths))
        self.assertEqual(sum(result.returncode == 0 for result in results), 1)
        self.assertTrue(all(result.returncode in (0, 2) for result in results))
        self.assertEqual(self.state()['requests'][request_id]['status'], 'claimed')


if __name__ == '__main__':
    unittest.main()
