#!/usr/bin/env python3
"""Offline regressions against copied real routing files; no business or model calls."""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from validate_package import (
    ROOT, PRESERVATION, CONTEXT_PRESERVATION, CONTEXT_DOCUMENTS, LEGACY_ENTRY_ARCHIVE,
    DIRECTOR_ENTRY_MIGRATION, DIRECTOR_ARCHIVE_ROOT, Checks,
    active_markdown, check_context_documents, check_package, check_routing,
    local_link_target, read_native_config,
)


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


class RoutingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Copy current files, not hand-written fake skills. A missing real entry
        # must fail the baseline instead of being concealed by a fixture stub.
        cls.base_temp = tempfile.TemporaryDirectory(prefix='1688-routing-base-')
        cls.base = Path(cls.base_temp.name)
        for name in ('.agents', '.codex', 'agents', 'references', 'catalog', 'scripts',
                     'archive/legacy-agent-entries', DIRECTOR_ARCHIVE_ROOT):
            if (ROOT / name).is_dir():
                shutil.copytree(ROOT / name, cls.base / name)
        for name in ('AGENTS.md', 'README.md', 'VALIDATION.md', 'VALIDATION-REVIEW.md',
                     PRESERVATION, CONTEXT_PRESERVATION, LEGACY_ENTRY_ARCHIVE,
                     DIRECTOR_ENTRY_MIGRATION) + CONTEXT_DOCUMENTS:
            if (ROOT / name).is_file():
                copy_file(ROOT / name, cls.base / name)
        preservation = json.loads((ROOT / PRESERVATION).read_text())
        copy_file(ROOT / preservation['backup'], cls.base / preservation['backup'])
        context_preservation = json.loads((ROOT / CONTEXT_PRESERVATION).read_text())
        copy_file(ROOT / context_preservation['backup'], cls.base / context_preservation['backup'])
        for path in (ROOT / 'source').rglob('SKILL.md'):
            copy_file(path, cls.base / path.relative_to(ROOT))
        for path in active_markdown(ROOT):
            if not path.is_file():
                continue
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                target = local_link_target(path, link)
                if target is None:
                    continue
                target = target.resolve()
                if target.is_file() and target.is_relative_to(ROOT):
                    copy_file(target, cls.base / target.relative_to(ROOT))
                elif target.is_dir() and target.is_relative_to(ROOT):
                    (cls.base / target.relative_to(ROOT)).mkdir(parents=True, exist_ok=True)
        # Phase manifests also reference source chapters not directly linked by an
        # active Markdown entry. Copy the actual inputs, never dummy fixtures.
        loading = json.loads((ROOT / 'catalog/task-routing.json').read_text())
        def copy_manifest_paths(value):
            if isinstance(value, dict):
                for nested in value.values():
                    copy_manifest_paths(nested)
            elif isinstance(value, list):
                for nested in value:
                    copy_manifest_paths(nested)
            elif isinstance(value, str) and value.startswith(('source/', 'references/', 'agents/', '.agents/', 'scripts/', 'AGENTS.md')):
                candidate = (ROOT / value.split('#', 1)[0]).resolve()
                if candidate.is_relative_to(ROOT) and candidate.is_file():
                    copy_file(candidate, cls.base / candidate.relative_to(ROOT))
        copy_manifest_paths(loading)
        result = check_routing(cls.base)
        if not result['passed']:
            cls.base_temp.cleanup()
            raise AssertionError('Real fixture is not valid: ' + '\n'.join(result['errors']))

    @classmethod
    def tearDownClass(cls):
        cls.base_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='1688-routing-case-')
        self.root = Path(self.temp.name) / 'project'
        shutil.copytree(self.base, self.root)
        self.addCleanup(self.temp.cleanup)

    def edit_json(self, rel, change):
        path = self.root / rel
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    def assert_contract_error(self, prefix):
        result = check_routing(self.root)
        self.assertFalse(result['passed'])
        self.assertTrue(any(error.startswith(prefix) for error in result['errors']), result['errors'])

    def test_real_fixture_and_full_package(self):
        self.assertTrue(check_routing(self.root)['passed'])
        # Full provenance check is read-only and deliberately uses the real package.
        result = check_package(ROOT)
        self.assertTrue(result['passed'], result['errors'])
        self.assertEqual(result['tool_count'], 205)
        self.assertEqual(result['design_prompt_count'], 265)
        self.assertEqual(result['protected_files_hash_checked'], 2658)

    def test_staged_loading_cannot_disappear(self):
        def mutate(data):
            next(row for row in data['routes'] if row['id'] == 'title_optimization').pop('phase_loading')
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Missing or unsupported phase loading: title_optimization')

    def test_title_execute_cannot_lose_execution_protocol(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'title_optimization')
            row['phase_loading']['execute']['executor_read'].remove('references/execution-protocol.md')
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Missing mandatory execution protocol: title_optimization/execute')

    def test_ad_monitor_cannot_lose_corrected_policy(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'traffic_and_ads')
            row['phase_loading']['monitor']['automatic_conditions'].remove('ads')
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Advertising policy must be automatic: traffic_and_ads/monitor')

    def test_ad_plan_cannot_lose_decision_completion_requirements(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'traffic_and_ads')
            row['phase_loading']['plan'].pop('completion_contract')
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Missing mandatory completion contract: traffic_and_ads/plan')

    def test_handoff_cannot_point_to_wrong_owner_or_grant_authorization(self):
        for mutation, prefix in (({'target_owner': 'traffic_operations'}, 'Conditional handoff owner mismatch'),
                                 ({'authorization': 'granted'}, 'Conditional handoff must not grant authorization'),
                                 ({'automatic_execution': True}, 'Conditional handoff must not grant authorization')):
            with self.subTest(mutation=mutation):
                def mutate(data):
                    row = next(row for row in data['routes'] if row['id'] == 'product_images')
                    handoff = row['phase_loading']['plan']['conditional_handoffs'][0]
                    handoff.update(target_owner='product_operations', authorization='inherit_only', automatic_execution=False)
                    handoff.update(mutation)
                self.edit_json('catalog/task-routing.json', mutate)
                self.assert_contract_error(prefix)

    def test_image_application_cannot_be_treated_as_asset_generation(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'product_images')
            row['phase_loading']['execute']['completion_contract']['deliverables']['execution']['required_conditions'] = []
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Image execution deliverable must require apply_images')

    def test_full_source_loading_index_cannot_drop_preserved_rule(self):
        self.edit_json('catalog/task-routing.json', lambda data:
                       data['context_loading']['rule_sources'].pop('references/business-rules/1688-title-optimizer/RULES.md'))
        self.assert_contract_error('Full source-loading index must cover exactly')

    def test_title_route_cannot_be_owned_by_director(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'title_optimization')
            row['owner'] = 'operations_director'
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Route owner mismatch: title_optimization')

    def test_monthly_review_must_use_director_cycle(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'monthly_review')
            row['owner'] = 'traffic_operations'
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Route owner mismatch: monthly_review')

    def test_growth_workflow_reference_cannot_drift(self):
        self.edit_json('catalog/task-routing.json', lambda data: data.update(operating_workflow='old.md'))
        self.assert_contract_error('Operating workflow must reference')

    def test_product_route_cannot_skip_domain_delegation(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'title_optimization')
            row['delegation_policy'] = 'director_direct'
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Route delegation policy mismatch: title_optimization')

    def test_specialist_route_cannot_become_director_direct(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'erp_inventory')
            row['delegation_policy'] = 'director_direct'
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Route delegation policy mismatch: erp_inventory')

    def test_operating_cycles_cannot_drop_conversion_monitoring(self):
        for route_id in ('daily_operations', 'weekly_review', 'monthly_review'):
            for replacement in ([], ['customer_conversion'], ['conversion_analysis']):
                with self.subTest(route=route_id, replacement=replacement):
                    def mutate(data):
                        row = next(row for row in data['routes'] if row['id'] == route_id)
                        row['monitoring_routes'] = replacement
                    self.edit_json('catalog/task-routing.json', mutate)
                    self.assert_contract_error('Operating cycle must include conversion monitoring: ' + route_id)
                    copy_file(self.base / 'catalog/task-routing.json', self.root / 'catalog/task-routing.json')

    def test_conversion_analysis_cannot_become_optional_or_direct(self):
        for policy in ('director_direct', 'specialist_on_demand'):
            with self.subTest(policy=policy):
                def mutate(data):
                    row = next(row for row in data['routes'] if row['id'] == 'conversion_analysis')
                    row['delegation_policy'] = policy
                self.edit_json('catalog/task-routing.json', mutate)
                self.assert_contract_error('Route delegation policy mismatch: conversion_analysis')

    def test_conversion_analysis_cannot_route_to_director_or_customer_outreach(self):
        for executor in ('operations_director', 'outreach_operator', None):
            with self.subTest(executor=executor):
                def mutate(data):
                    row = next(row for row in data['routes'] if row['id'] == 'conversion_analysis')
                    row['executor'] = executor
                self.edit_json('catalog/task-routing.json', mutate)
                self.assert_contract_error('Conversion analysis must name its actual specialist executor')

    def test_monitoring_cannot_escalate_to_broad_customer_operations(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'conversion_monitoring')
            row['analysis_route'] = 'customer_conversion'
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Conversion monitoring must route deep analysis to conversion_analysis')

    def test_analysis_paths_cannot_gain_write_mode_or_customer_write_rules(self):
        for route_id in ('conversion_monitoring', 'conversion_analysis'):
            for field, replacement, error in (
                ('mode', 'customer_operations', 'Conversion route must be analysis_only: '),
                ('rules', ['references/business-rules/1688-outreach-operator/RULES.md'],
                 'Conversion route rules must be inquiry and CRM only: '),
                ('optional_capabilities', ['listing'],
                 'Conversion route must not add optional write-capable workflows: '),
            ):
                with self.subTest(route=route_id, field=field):
                    def mutate(data):
                        row = next(row for row in data['routes'] if row['id'] == route_id)
                        row[field] = replacement
                    self.edit_json('catalog/task-routing.json', mutate)
                    self.assert_contract_error(error + route_id)
                    copy_file(self.base / 'catalog/task-routing.json', self.root / 'catalog/task-routing.json')

    def test_explicit_customer_operations_keep_existing_business_flows(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'customer_conversion')
            row['rules'] = [rule for rule in row['rules'] if 'outreach-operator' not in rule]
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Explicit customer conversion route must preserve all five original workflows')

    def test_conversion_specialist_cannot_become_a_resident_project_or_fourth_core_role(self):
        for field, value, error in (
            ('activation', 'core', 'Conversion specialist registry mismatch: activation'),
            ('project', 'agents/conversion_analysis', 'Conversion specialist registry mismatch: project'),
            ('counts_as_core_agent', True, 'Conversion specialist must not count as a core role'),
            ('owner', 'product_operations', 'Conversion specialist registry mismatch: owner'),
            ('mode', 'customer_operations', 'Conversion specialist registry mismatch: mode'),
            ('skill', '.agents/skills/1688-product-operations/SKILL.md', 'Conversion specialist registry mismatch: skill'),
            ('rules', ['references/business-rules/1688-outreach-operator/RULES.md'],
             'Conversion specialist rules must be inquiry and CRM only'),
        ):
            with self.subTest(field=field):
                self.edit_json('catalog/agent-registry.json', lambda data:
                               data['on_demand_specialists'][0].update({field: value}))
                self.assert_contract_error(error)
                copy_file(self.base / 'catalog/agent-registry.json', self.root / 'catalog/agent-registry.json')

    def test_missing_or_duplicate_conversion_specialist_is_rejected(self):
        for replacement in ([], None):
            with self.subTest(replacement=replacement):
                self.edit_json('catalog/agent-registry.json', lambda data:
                               data.update(on_demand_specialists=replacement))
                self.assert_contract_error('On-demand specialists must contain only conditional conversion analysis')
                copy_file(self.base / 'catalog/agent-registry.json', self.root / 'catalog/agent-registry.json')
        self.edit_json('catalog/agent-registry.json', lambda data:
                       data['on_demand_specialists'].append(data['on_demand_specialists'][0].copy()))
        self.assert_contract_error('On-demand specialists must contain only conditional conversion analysis')

    def test_new_specialist_policy_must_be_defined(self):
        self.edit_json('catalog/task-routing.json', lambda data:
                       data['delegation_policies'].pop('specialist_required'))
        self.assert_contract_error('Delegation policy definitions must include all four declared policies')

    def test_conversion_contract_must_remain_reachable(self):
        def mutate(data):
            row = next(row for row in data['routes'] if row['id'] == 'conversion_monitoring')
            row.pop('state_contract')
        self.edit_json('catalog/task-routing.json', mutate)
        self.assert_contract_error('Conversion route reference mismatch: conversion_monitoring: state_contract')
        copy_file(self.base / 'catalog/task-routing.json', self.root / 'catalog/task-routing.json')
        (self.root / 'references/conversion-state.md').unlink()
        self.assert_contract_error('Missing conversion analysis contract: references/conversion-state.md')

    def test_conversion_native_must_reuse_customer_skill_and_inherit_runtime(self):
        path = self.root / '.codex/agents/conversion_analysis.toml'
        original = path.read_text()
        path.write_text(original.replace('.agents/skills/1688-customer-conversion/SKILL.md', 'different-entry.md'))
        self.assert_contract_error('Native config does not load its entry: conversion_analysis')
        for override in ('model = "other"', 'model_provider = "other"',
                         'sandbox_mode = "danger-full-access"', '[mcp_servers.extra]'):
            with self.subTest(override=override):
                path.write_text(original + '\n' + override + '\n')
                self.assert_contract_error('Invalid native config: .codex/agents/conversion_analysis.toml')
        path.write_text(original)

    def test_alias_cannot_change_owner(self):
        self.edit_json('catalog/agent-registry.json', lambda data:
                       data['legacy_aliases']['title_optimizer'].update(owner='traffic_operations'))
        self.assert_contract_error('Legacy alias owner mismatch: title_optimizer')

    def test_legacy_alias_cannot_restore_independent_role(self):
        self.edit_json('catalog/agent-registry.json', lambda data:
                       data['legacy_aliases']['title_optimizer'].update(entry_mode='independent_agent'))
        self.assert_contract_error('Legacy alias entry mode mismatch: title_optimizer')

    def test_old_role_directory_cannot_reappear_in_agents(self):
        copy_file(self.root / 'archive/legacy-agent-entries/title_optimizer/ENTRY.md',
                  self.root / 'agents/title_optimizer/AGENTS.md')
        self.assert_contract_error('Active agent directories must contain only product, traffic and image-agent')

    def test_old_role_cannot_return_as_a_symlink(self):
        (self.root / 'agents/title_optimizer').symlink_to(
            self.root / 'archive/legacy-agent-entries/title_optimizer', target_is_directory=True)
        self.assert_contract_error('Legacy directory must not remain active: title_optimizer')

    def test_legacy_compatibility_entry_mode_cannot_return(self):
        self.edit_json('catalog/agent-registry.json', lambda data:
                       data['legacy_aliases']['title_optimizer'].update(entry_mode='compatibility_capability_entry'))
        self.assert_contract_error('Legacy alias entry mode mismatch: title_optimizer')

    def test_archived_entry_cannot_be_missing_or_changed(self):
        path = self.root / 'archive/legacy-agent-entries/title_optimizer/ENTRY.md'
        original = path.read_bytes()
        path.unlink()
        self.assert_contract_error('Missing archived legacy entry:')
        path.write_bytes(original + b'\n')
        self.assert_contract_error('Archived legacy entry SHA mismatch:')

    def test_archive_cannot_restore_discoverable_instructions(self):
        for archive in ('archive/legacy-agent-entries/title_optimizer', DIRECTOR_ARCHIVE_ROOT):
            folder = self.root / archive
            for name in ('AGENTS.md', 'AGENTS.override.md', 'SKILL.md', 'restored.toml'):
                with self.subTest(archive=archive, name=name):
                    path = folder / name
                    copy_file(folder / 'ENTRY.md', path)
                    self.assert_contract_error('Archive must not contain discoverable agent or skill entry names:')
                    path.unlink()

    def test_director_project_cannot_return_to_an_alternate_entry(self):
        alternate = 'agents/operations_director'
        copy_file(self.root / DIRECTOR_ARCHIVE_ROOT / 'ENTRY.md', self.root / alternate / 'AGENTS.md')

        def restore_director_project(data):
            next(row for row in data['agents'] if row['id'] == 'operations_director')['project'] = alternate
            for alias in data['legacy_aliases'].values():
                if alias['owner'] == 'operations_director':
                    alias['current_owner_entry'] = alternate + '/AGENTS.md'

        self.edit_json('catalog/agent-registry.json', restore_director_project)
        self.assert_contract_error('Director must use the project root as its only entry')

    def test_director_directory_cannot_return_as_directory_or_symlink(self):
        former = self.root / 'agents/operations_director'
        archive = self.root / DIRECTOR_ARCHIVE_ROOT
        for mode in ('directory', 'symlink'):
            with self.subTest(mode=mode):
                if mode == 'directory':
                    copy_file(archive / 'ENTRY.md', former / 'AGENTS.md')
                else:
                    former.symlink_to(archive, target_is_directory=True)
                self.assert_contract_error('Director directory must not remain active')
                if former.is_symlink():
                    former.unlink()
                else:
                    shutil.rmtree(former)

    def test_director_aliases_must_use_the_canonical_root_entry(self):
        for legacy in ('operations_director', 'store_analyst'):
            for entry in ('agents/operations_director/AGENTS.md', './AGENTS.md'):
                with self.subTest(legacy=legacy, entry=entry):
                    self.edit_json('catalog/agent-registry.json', lambda data:
                                   data['legacy_aliases'][legacy].update(current_owner_entry=entry))
                    self.assert_contract_error('Legacy alias current owner entry mismatch: ' + legacy)
                    copy_file(self.base / 'catalog/agent-registry.json', self.root / 'catalog/agent-registry.json')

    def test_director_archive_cannot_be_missing_or_changed(self):
        path = self.root / DIRECTOR_ARCHIVE_ROOT / 'ENTRY.md'
        original = path.read_bytes()
        path.unlink()
        self.assert_contract_error('Missing archived director entry:')
        path.write_bytes(original + b'\n')
        self.assert_contract_error('Archived director entry SHA mismatch:')

    def test_director_migration_must_point_to_root_and_remain_registered(self):
        self.edit_json(DIRECTOR_ENTRY_MIGRATION, lambda data:
                       data.update(current_entry='agents/operations_director/AGENTS.md'))
        self.assert_contract_error('Director entry migration mismatch: current_entry')
        copy_file(self.base / DIRECTOR_ENTRY_MIGRATION, self.root / DIRECTOR_ENTRY_MIGRATION)
        self.edit_json('catalog/agent-registry.json', lambda data: data.pop('primary_entry_migration'))
        self.assert_contract_error('Wrong director entry migration manifest')

    def test_legacy_current_entry_must_match_its_owner(self):
        self.edit_json('catalog/agent-registry.json', lambda data:
                       data['legacy_aliases']['title_optimizer'].update(
                           current_owner_entry='agents/traffic_operations/AGENTS.md'))
        self.assert_contract_error('Legacy alias current owner entry mismatch: title_optimizer')

    def test_legacy_role_cannot_belong_to_two_capabilities(self):
        def mutate(data):
            row = next(row for row in data['skills'] if row['id'] == 'market_research')
            row['legacy_roles'].append('title_optimizer')
        self.edit_json('catalog/agent-registry.json', mutate)
        self.assert_contract_error('Legacy role maps to multiple capabilities')

    def test_preserved_business_rule_must_be_byte_identical(self):
        path = self.root / 'references/business-rules/1688-title-optimizer/RULES.md'
        path.write_bytes(path.read_bytes() + b'\n')
        self.assert_contract_error('Preserved business-rule SHA mismatch:')

    def test_context_facts_outside_section_six_must_remain_identical(self):
        baseline = Checks(self.root)
        self.assertEqual(check_context_documents(baseline), 2)
        self.assertFalse(baseline.errors, baseline.errors)
        for name in CONTEXT_DOCUMENTS:
            path = self.root / name
            original = path.read_bytes()
            for section, changed in (('prefix', b'changed\n' + original),
                                     ('suffix', original + b'\nchanged\n')):
                with self.subTest(document=name, section=section):
                    path.write_bytes(changed)
                    checks = Checks(self.root)
                    check_context_documents(checks)
                    self.assertTrue(any(error.startswith('Context-document preserved ' + section + ' SHA mismatch:')
                                        for error in checks.errors), checks.errors)
                    path.write_bytes(original)

    def test_source_routing_must_match_alias(self):
        def mutate(data):
            row = next(row for row in data['skills'] if row['legacy_agent'] == 'title_optimizer')
            row['capability'] = 'traffic_analysis'
        self.edit_json('catalog/source-to-agent.json', mutate)
        self.assert_contract_error('Source alias routing mismatch:')

    def test_traffic_query_cannot_claim_write_capability(self):
        def mutate(data):
            row = next(row for row in data['tools'] if row['name'] == 'get_ad_channel_detail')
            row['planning_hint']['operation_classes'] = ['query', 'write']
        self.edit_json('catalog/tool-routing.json', mutate)
        self.assert_contract_error('Unverified traffic write capability: get_ad_channel_detail')

    def test_tool_owner_and_capability_must_agree(self):
        def mutate(data):
            row = next(row for row in data['tools'] if row['name'] == 'get_ad_channel_detail')
            row['primary_agent'] = 'product_operations'
        self.edit_json('catalog/tool-routing.json', mutate)
        self.assert_contract_error('Tool primary role/capability mismatch: get_ad_channel_detail')

    def test_original_tool_description_cannot_change(self):
        self.edit_json('catalog/tool-routing.json', lambda data: data['tools'][0].update(description='changed'))
        self.assert_contract_error('Original tool names/descriptions changed')

    def test_schema_snapshot_cannot_change(self):
        path = self.root / 'catalog/live-tool-schemas.json'
        path.write_bytes(path.read_bytes() + b'\n')
        self.assert_contract_error('Original tool schema snapshot changed')

    def test_director_must_not_become_native_subagent(self):
        source = self.root / '.codex/agents/product_operations.toml'
        copy_file(source, self.root / '.codex/agents/operations_director.toml')
        self.assert_contract_error('Native configs must contain only product/traffic/review/conversion_analysis')

    def test_runtime_override_is_rejected(self):
        path = self.root / '.codex/agents/product_operations.toml'
        for override in ('model = "other"', 'model_provider = "other"',
                         'sandbox_mode = "danger-full-access"', '[mcp_servers.extra]'):
            with self.subTest(override=override):
                original = path.read_text()
                path.write_text(original + '\n' + override + '\n')
                self.assert_contract_error('Invalid native config:')
                path.write_text(original)

    def test_duplicate_native_name_is_rejected(self):
        path = self.root / '.codex/agents/product_operations.toml'
        path.write_text(path.read_text() + '\nname = "another"\n')
        with self.assertRaises(ValueError):
            read_native_config(path)

    def test_legacy_skill_cannot_reenter_active_discovery(self):
        copy_file(self.root / 'references/business-rules/1688-title-optimizer/RULES.md',
                  self.root / '.agents/skills/1688-title-optimizer/SKILL.md')
        self.assert_contract_error('Active skill discovery must contain only the 13 consolidated skills')

    def test_reused_skill_name_cannot_restore_original_body(self):
        copy_file(self.root / 'references/business-rules/1688-listing-publisher/RULES.md',
                  self.root / '.agents/skills/1688-listing-publisher/SKILL.md')
        self.assert_contract_error('Old skill still active:')

    def test_broken_reference_link_is_detected(self):
        path = self.root / 'references/execution-protocol.md'
        path.write_text(path.read_text() + '\n[missing](missing-file.md#section)\n')
        self.assert_contract_error('Broken local link: references/execution-protocol.md')

    def test_url_fragments_line_numbers_and_encoded_paths(self):
        source = self.root / 'references/execution-protocol.md'
        expected = source.parent / '有 空格.md'
        for link in ('有%20空格.md:12#section', '<有 空格.md:12>', '有%20空格.md#L12'):
            with self.subTest(link=link):
                self.assertEqual(local_link_target(source, link), expected)
        self.assertIsNone(local_link_target(source, 'https://example.com/a#b'))
        self.assertIsNone(local_link_target(source, 'mailto:example@example.com'))
        self.assertIsNone(local_link_target(source, '#section'))
        self.assertEqual(local_link_target(source, 'runtime.md:12#section'), source.parent / 'runtime.md')


if __name__ == '__main__':
    unittest.main(verbosity=2)
