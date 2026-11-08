#!/usr/bin/env python3
"""Offline provenance and routing-contract checks; never executes business tools."""
import hashlib
import json
import re
import sys
import tarfile
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

from task_context import validate_loading_contract

ROOT = Path(__file__).resolve().parents[1]
PRESERVATION = 'manifests/routing-refactor-20261028-preservation.json'
CONTEXT_PRESERVATION = 'manifests/routing-refactor-20261028-context-docs.json'
LEGACY_ENTRY_ARCHIVE = 'manifests/legacy-agent-entry-archive-20261028.json'
LEGACY_ARCHIVE_ROOT = 'archive/legacy-agent-entries'
DIRECTOR_ENTRY_MIGRATION = 'manifests/director-entry-consolidation-20261029.json'
DIRECTOR_ARCHIVE_ROOT = 'archive/director-entry-20261029'
CONTEXT_DOCUMENTS = ('01-店铺接手摸底待办.md', '浙江淞泰科技-接手摸底-20261016.md')
CORE_ROLES = {'operations_director', 'product_operations', 'traffic_operations'}
ACTIVE_AGENT_DIRECTORIES = {'product_operations', 'traffic_operations', 'image-agent'}
NATIVE_ROLES = {'product_operations', 'traffic_operations', 'operations_review', 'conversion_analysis'}
CONVERSION_SKILL = '.agents/skills/1688-customer-conversion/SKILL.md'
CONVERSION_ANALYSIS_RULES = {
    'references/business-rules/1688-inquiry-analyst/RULES.md',
    'references/business-rules/1688-crm-manager/RULES.md',
}
CAPABILITY_OWNERS = {
    'operating_cycle': 'operations_director', 'business_analysis': 'operations_director',
    'product_optimization': 'product_operations', 'market_research': 'product_operations',
    'listing': 'product_operations', 'traffic_analysis': 'traffic_operations',
    'platform_knowledge': 'operations_director', 'platform_maintenance': 'operations_director',
    'customer_conversion': 'operations_director', 'erp_inventory': 'operations_director',
    'procurement_research': 'operations_director', 'buyer_transactions': 'operations_director',
    'distribution': 'operations_director', 'image': 'product_operations', 'reporting': 'operations_director',
}
ACTIVE_SKILL_NAMES = {
    '1688-operations-director', '1688-business-analysis', '1688-product-operations',
    '1688-market-research', '1688-listing-publisher', '1688-traffic-operations',
    '1688-platform-knowledge', '1688-platform-maintenance', '1688-customer-conversion',
    '1688-erp-inventory', '1688-procurement-research', '1688-buyer-transactions', '1688-distribution',
}
ROUTE_CAPABILITIES = {
    'daily_operations': 'operating_cycle', 'weekly_review': 'operating_cycle',
    'monthly_review': 'operating_cycle',
    'daily_metrics': 'business_analysis', 'period_analysis': 'business_analysis',
    'profit_analysis': 'business_analysis', 'product_diagnosis': 'product_optimization',
    'title_optimization': 'product_optimization', 'product_change': 'product_optimization',
    'product_images': 'image', 'new_listing': 'listing', 'competition': 'market_research',
    'market_opportunity': 'market_research', 'traffic_and_ads': 'traffic_analysis',
    'platform_rules': 'platform_knowledge', 'connections_and_components': 'platform_maintenance',
    'customer_conversion': 'customer_conversion', 'conversion_monitoring': 'customer_conversion',
    'conversion_analysis': 'customer_conversion', 'erp_inventory': 'erp_inventory',
    'procurement_research': 'procurement_research', 'buyer_transactions': 'buyer_transactions',
    'distribution': 'distribution', 'report_rendering': 'reporting',
}
SPECIALIST_ROUTES = {
    'customer_conversion', 'erp_inventory', 'procurement_research',
    'buyer_transactions', 'distribution',
}
ROUTE_DELEGATION_POLICIES = {
    route_id: ('specialist_required' if route_id == 'conversion_analysis'
               else 'domain_required' if CAPABILITY_OWNERS[capability] != 'operations_director'
               else 'specialist_on_demand' if route_id in SPECIALIST_ROUTES
               else 'director_direct')
    for route_id, capability in ROUTE_CAPABILITIES.items()
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Checks:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.errors = []

    def need(self, condition, message):
        if not condition:
            self.errors.append(message)

    def read(self, rel):
        try:
            return json.loads((self.root / rel).read_text())
        except (OSError, ValueError) as exc:
            self.errors.append('Cannot read JSON: {}: {}'.format(rel, exc))
            return {}

    def file(self, rel, label='Missing file'):
        path = (self.root / rel).resolve()
        valid = path.is_relative_to(self.root) and path.is_file()
        self.need(valid, label + ': ' + str(rel))
        return valid

    def hash(self, rel, expected, label):
        if self.file(rel):
            self.need(sha256(self.root / rel) == expected, label + ': ' + rel)


def active_markdown(root):
    """Historical source/reports/outputs/archive bodies are not active entry points."""
    files = {root / name for name in ('AGENTS.md', 'README.md', 'VALIDATION.md', 'VALIDATION-REVIEW.md')}
    files.add(root / LEGACY_ARCHIVE_ROOT / 'README.md')
    files.add(root / DIRECTOR_ARCHIVE_ROOT / 'README.md')
    files.update(root / name for name in CONTEXT_DOCUMENTS)
    for directory in ('.agents/skills', 'references', 'catalog'):
        files.update((root / directory).rglob('*.md'))
    files.update((root / 'agents').rglob('AGENTS.md'))
    files.update((root / 'agents/image-agent/.agents/skills').rglob('*.md'))
    return sorted(files)


def local_link_target(source, link):
    """Resolve local Markdown destinations, including encoded paths and :line/# anchors."""
    link = link.strip()
    if link.startswith('<'):
        link = link[1:link.find('>')]
    else:
        link = re.sub(r'\s+[\"\'][^\"\']*[\"\']$', '', link)
    if link.startswith('#'):
        return None
    path = unquote(link.split('#', 1)[0].split('?', 1)[0])
    path = re.sub(r':\d+(?::\d+)?$', '', path)
    if not path or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', path):
        return None
    target = Path(path)
    return target if target.is_absolute() else source.parent / target


def check_links(checks):
    for path in active_markdown(checks.root):
        if not path.is_file():
            checks.errors.append('Missing active Markdown: ' + str(path.relative_to(checks.root)))
            continue
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            target = local_link_target(path, link)
            if target is not None:
                checks.need(target.exists(), 'Broken local link: {} -> {}'.format(path.relative_to(checks.root), link))


def read_native_config(path):
    """Parse only this project's top-level TOML string assignments, on Python 3.9.

    Tables, unknown syntax, duplicate keys and all runtime overrides fail closed.
    No configuration is executed; this is not a general-purpose TOML parser.
    """
    text = path.read_text()
    result = {}
    pos = 0
    pattern = re.compile(
        r'([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*'
        r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:\\.|[^"\\\n])*"|\'[^\'\n]*\')'
        r'[ \t]*(?:#[^\n]*)?(?:\n|$)')
    while pos < len(text):
        skip = re.match(r'(?:\s|#[^\n]*(?:\n|$))*', text[pos:])
        pos += skip.end()
        if pos == len(text):
            break
        match = pattern.match(text, pos)
        if not match:
            raise ValueError('Only top-level string assignments are permitted')
        key, value = match.groups()
        if key in result:
            raise ValueError('Duplicate key: ' + key)
        if value.startswith(('"""', "'''")):
            value = value[3:-3]
        elif value.startswith('"'):
            value = json.loads(value)
        else:
            value = value[1:-1]
        result[key] = value
        pos = match.end()
    if set(result) != {'name', 'description', 'developer_instructions'}:
        raise ValueError('Only name/description/developer_instructions are permitted')
    if not all(value.strip() for value in result.values()):
        raise ValueError('Config strings must be nonempty')
    return result


def check_original_snapshot(c, preservation, tools):
    """Compare preserved rules, tool descriptions and schemas with the saved input."""
    backup = preservation.get('backup', '')
    if not c.file(backup, 'Missing pre-refactor backup'):
        return
    try:
        with tarfile.open(c.root / backup, 'r:gz') as archive:
            members = {member.name.removeprefix('./'): member for member in archive.getmembers()}
            old = json.load(archive.extractfile(members['catalog/tool-routing.json']))
            c.need(len(tools) == 205 and len({x['name'] for x in tools}) == 205,
                   'Tool routing must cover exactly 205 distinct snapshot tools')
            c.need({x['name']: x['description'] for x in tools} == {x['name']: x['description'] for x in old['tools']},
                   'Original tool names/descriptions changed')
            current_tools = {x['name']: x for x in tools}
            for original in old['tools']:
                current = current_tools.get(original['name'], {})
                for key, value in original.items():
                    if key == 'primary_agent':
                        c.need(current.get('legacy_primary_agent') == value,
                               'Original tool owner evidence changed: ' + original['name'])
                    elif key == 'planning_hint':
                        c.need({k: v for k, v in current.get(key, {}).items() if k != 'primary_agent'} ==
                               {k: v for k, v in value.items() if k != 'primary_agent'},
                               'Original tool planning constraints changed: ' + original['name'])
                    else:
                        c.need(current.get(key) == value,
                               'Original tool field changed: {}: {}'.format(original['name'], key))
            schema_path = 'catalog/live-tool-schemas.json'
            if c.file(schema_path):
                c.need((c.root / schema_path).read_bytes() == archive.extractfile(members[schema_path]).read(),
                       'Original tool schema snapshot changed')
            for row in preservation.get('business_rule_files', []):
                data = archive.extractfile(members[row['original_path']]).read()
                c.need(hashlib.sha256(data).hexdigest() == row['sha256'],
                       'Preservation manifest differs from backup: ' + row['original_path'])
    except (OSError, ValueError, KeyError, tarfile.TarError) as exc:
        c.errors.append('Cannot verify pre-refactor backup: ' + str(exc))


def context_sections(data):
    """Return immutable bytes around section six; do not normalize whitespace."""
    start = re.search(rb'^' + re.escape('## 六、按需求调用Agent的场景草案'.encode()) + rb'\r?$', data, re.M)
    if start is None:
        raise ValueError('Section six heading missing')
    end = re.search(rb'^' + re.escape('## 七、'.encode()), data[start.end():], re.M)
    if end is None:
        raise ValueError('Section seven heading missing')
    return data[:start.start()], data[start.end() + end.start():]


def check_context_documents(c):
    """Only section-six routing may change; store facts and evidence stay byte-identical."""
    preservation = c.read(CONTEXT_PRESERVATION)
    rows = preservation.get('files', [])
    c.need(len(rows) == 2 and {row.get('path') for row in rows} == set(CONTEXT_DOCUMENTS),
           'Context-document preservation coverage mismatch')
    backup = preservation.get('backup', '')
    if not c.file(backup, 'Missing context-document backup'):
        return 0
    checked = 0
    try:
        with tarfile.open(c.root / backup, 'r:gz') as archive:
            members = {member.name.removeprefix('./'): member for member in archive.getmembers()}
            for row in rows:
                path = row['path']
                original = archive.extractfile(members[path]).read()
                c.need(hashlib.sha256(original).hexdigest() == row['sha256'],
                       'Context-document backup SHA mismatch: ' + path)
                prefix, suffix = context_sections(original)
                for name, data in (('prefix', prefix), ('suffix', suffix)):
                    c.need(hashlib.sha256(data).hexdigest() == row['preserved_' + name + '_sha256'],
                           'Context preservation manifest differs from backup: {}: {}'.format(path, name))
                if c.file(path, 'Missing context document'):
                    current_prefix, current_suffix = context_sections((c.root / path).read_bytes())
                    for name, data in (('prefix', current_prefix), ('suffix', current_suffix)):
                        c.need(hashlib.sha256(data).hexdigest() == row['preserved_' + name + '_sha256'],
                               'Context-document preserved {} SHA mismatch: {}'.format(name, path))
                    checked += 1
    except (OSError, ValueError, KeyError, tarfile.TarError) as exc:
        c.errors.append('Cannot verify context-document preservation: ' + str(exc))
    return checked


def check_conversion_contract(c, registry, task_routing):
    """Constrain the daily analysis path without removing explicit CRM workflows.

    These checks validate local routing declarations, not gateway permissions or
    actual delegation. Runtime tool access and acknowledgements remain separate.
    """
    c.need(registry.get('version') == task_routing.get('version') == '2.4.0',
           'Registry/task-routing version must be 2.4.0')
    specialist_rows = registry.get('on_demand_specialists', [])
    c.need(isinstance(specialist_rows, list) and len(specialist_rows) == 1 and
           isinstance(specialist_rows[0], dict) and specialist_rows[0].get('id') == 'conversion_analysis',
           'On-demand specialists must contain only conditional conversion analysis')
    specialist = specialist_rows[0] if (isinstance(specialist_rows, list) and specialist_rows and
                                       isinstance(specialist_rows[0], dict)) else {}
    for field, expected in (
            ('owner', 'operations_director'), ('capability', 'customer_conversion'),
            ('skill', CONVERSION_SKILL), ('activation', 'conditional'), ('project', None),
            ('mode', 'analysis_only'),
            ('native_config', '.codex/agents/conversion_analysis.toml')):
        c.need(field in specialist and specialist.get(field) == expected,
               'Conversion specialist registry mismatch: ' + field)
    c.need(isinstance(specialist.get('rules'), list) and len(specialist['rules']) == 2 and
           set(specialist['rules']) == CONVERSION_ANALYSIS_RULES,
           'Conversion specialist rules must be inquiry and CRM only')
    c.need(specialist.get('counts_as_core_agent', False) is False,
           'Conversion specialist must not count as a core role')
    routes = {row.get('id'): row for row in task_routing.get('routes', [])}
    for route_id in ('daily_operations', 'weekly_review', 'monthly_review'):
        c.need(routes.get(route_id, {}).get('monitoring_routes') == ['conversion_monitoring'],
               'Operating cycle must include conversion monitoring: ' + route_id)
    for route_id in ('conversion_monitoring', 'conversion_analysis'):
        route = routes.get(route_id, {})
        c.need(route.get('mode') == 'analysis_only', 'Conversion route must be analysis_only: ' + route_id)
        c.need(isinstance(route.get('rules'), list) and len(route['rules']) == 2 and
               set(route['rules']) == CONVERSION_ANALYSIS_RULES,
               'Conversion route rules must be inquiry and CRM only: ' + route_id)
        c.need(route.get('optional_capabilities') == [],
               'Conversion route must not add optional write-capable workflows: ' + route_id)
        for field, expected in (
                ('reference', '.agents/skills/1688-customer-conversion/references/conversion-analysis.md'),
                ('state_contract', 'references/conversion-state.md')):
            c.need(route.get(field) == expected, 'Conversion route reference mismatch: ' + route_id + ': ' + field)
            c.file(expected, 'Missing conversion analysis contract')
    monitor = routes.get('conversion_monitoring', {})
    c.need(monitor.get('analysis_route') == 'conversion_analysis',
           'Conversion monitoring must route deep analysis to conversion_analysis')
    c.need('executor' not in monitor or monitor.get('executor') == 'operations_director',
           'Conversion monitoring executor must remain the director')
    c.need(routes.get('conversion_analysis', {}).get('executor') == 'conversion_analysis',
           'Conversion analysis must name its actual specialist executor')
    # The broad explicit-task route must retain all five original business flows.
    customer = routes.get('customer_conversion', {})
    customer_rules = CONVERSION_ANALYSIS_RULES | {
        'references/business-rules/1688-reception-coach/RULES.md',
        'references/business-rules/1688-quotation-designer/RULES.md',
        'references/business-rules/1688-outreach-operator/RULES.md',
    }
    c.need(isinstance(customer.get('rules'), list) and len(customer['rules']) == 5 and
           set(customer['rules']) == customer_rules,
           'Explicit customer conversion route must preserve all five original workflows')
    policies = task_routing.get('delegation_policies', {})
    expected_policies = {'director_direct', 'domain_required', 'specialist_on_demand', 'specialist_required'}
    c.need(isinstance(policies, dict) and set(policies) == expected_policies and
           all(isinstance(value, str) and value.strip() for value in policies.values()),
           'Delegation policy definitions must include all four declared policies')
    return specialist


def check_routing(root=ROOT):
    """Fast contract check, also used with real-file fixtures by regression tests."""
    c = Checks(root)
    registry = c.read('catalog/agent-registry.json')
    task_routing = c.read('catalog/task-routing.json')
    tool_routing = c.read('catalog/tool-routing.json')
    mapping = c.read('catalog/source-to-agent.json')
    preservation = c.read(PRESERVATION)
    role_rows = registry.get('agents', [])
    roles = {x['id']: x for x in role_rows}
    skill_rows = registry.get('skills', [])
    capabilities = {x['id']: x for x in skill_rows}
    aliases = registry.get('legacy_aliases', {})
    routes = task_routing.get('routes', [])
    c.need(task_routing.get('operating_workflow') == 'references/sales-growth-workflow.md',
           'Operating workflow must reference the current sales growth protocol')
    c.file('references/sales-growth-workflow.md', 'Missing sales growth workflow')
    conversion_specialist = check_conversion_contract(c, registry, task_routing)
    c.errors.extend(validate_loading_contract(c.root, task_routing))
    c.need(len(role_rows) == registry.get('agent_count') == 3 and set(roles) == CORE_ROLES,
           'Core roles must be exactly the director, product and traffic roles')
    agent_root = c.root / 'agents'
    agent_directories = {p.name for p in agent_root.iterdir() if p.is_dir() or p.is_symlink()} if agent_root.is_dir() else set()
    c.need(agent_directories == ACTIVE_AGENT_DIRECTORIES,
           'Active agent directories must contain only product, traffic and image-agent')
    c.need(not any(p.is_symlink() for p in agent_root.iterdir()) if agent_root.is_dir() else False,
           'Active agent entries must not be symlinked legacy aliases')
    c.need(len(skill_rows) == 15 and set(capabilities) == set(CAPABILITY_OWNERS),
           'Capability registry must contain the 15 declared capabilities')
    c.need(tool_routing.get('roles') == role_rows, 'Tool role registry differs from agent registry')
    c.need(registry.get('task_routing') == 'catalog/task-routing.json', 'Wrong task routing source')
    c.need(registry.get('rules_preservation') == PRESERVATION, 'Wrong preservation manifest')
    original_rules = {x['original_path']: x for x in preservation.get('business_rule_files', [])}
    preserved_rules = {x['preserved_path'] for x in original_rules.values() if x['original_path'].endswith('/SKILL.md')}
    c.need(len(original_rules) == len(preservation.get('business_rule_files', [])) == 63,
           'Preservation manifest must contain 63 distinct business-rule files')
    c.need(len(preserved_rules) == 31, 'Preservation must contain all 31 original skills')
    for row in original_rules.values():
        c.hash(row['preserved_path'], row['sha256'], 'Preserved business-rule SHA mismatch')
    legacy_members = Counter()
    registered_rules = set()
    for cap_id, cap in capabilities.items():
        c.need(cap.get('owner') == CAPABILITY_OWNERS.get(cap_id), 'Capability owner mismatch: ' + cap_id)
        c.file(cap.get('skill', ''), 'Missing capability skill')
        c.need(bool(cap.get('rules')), 'Capability rules missing: ' + cap_id)
        for rule in cap.get('rules', []):
            c.need(rule in preserved_rules, 'Unknown preserved rule: ' + rule)
            registered_rules.add(rule)
        legacy_members.update(cap.get('legacy_roles', []))
    c.need(registered_rules == preserved_rules, 'Capability coverage of preserved rules incomplete')
    c.need(len(aliases) == 31 and set(aliases) == set(legacy_members), 'Legacy alias coverage incomplete')
    c.need(all(count == 1 for count in legacy_members.values()), 'Legacy role maps to multiple capabilities')
    for legacy, alias in aliases.items():
        cap = capabilities.get(alias.get('capability'), {})
        expected_entry_mode = 'primary' if legacy == 'operations_director' else 'archived_alias'
        c.need(alias.get('entry_mode') == expected_entry_mode,
               'Legacy alias entry mode mismatch: ' + legacy)
        c.need(alias.get('owner') == cap.get('owner') and alias.get('owner') in CORE_ROLES,
               'Legacy alias owner mismatch: ' + legacy)
        c.need(alias.get('skill') == cap.get('skill') and legacy in cap.get('legacy_roles', []),
               'Legacy alias capability/skill mismatch: ' + legacy)
        original_name = alias.get('original_skill_name', '')
        c.need(original_name == '1688-' + legacy.replace('_', '-'),
               'Legacy alias original skill mismatch: ' + legacy)
        expected_rule = 'references/business-rules/' + original_name + '/RULES.md'
        c.need(alias.get('rules') == [expected_rule] and expected_rule in cap.get('rules', []),
               'Legacy alias rule mismatch: ' + legacy)
        c.need('.agents/skills/' + original_name + '/SKILL.md' in original_rules,
               'Legacy alias not preserved: ' + legacy)
        expected_owner_entry = str(Path(roles.get(alias.get('owner'), {}).get('project', '')) / 'AGENTS.md')
        c.need(alias.get('current_owner_entry') == expected_owner_entry,
               'Legacy alias current owner entry mismatch: ' + legacy)
        c.file(alias.get('current_owner_entry', ''), 'Missing current owner entry')
        c.need(alias.get('legacy_project') == 'agents/' + legacy,
               'Legacy historical project mismatch: ' + legacy)
        if legacy != 'operations_director':
            expected_archive = LEGACY_ARCHIVE_ROOT + '/' + legacy + '/ENTRY.md'
            c.need(alias.get('archived_entry') == expected_archive,
                   'Legacy archive location mismatch: ' + legacy)
            c.file(expected_archive, 'Missing archived legacy entry')
            former = c.root / 'agents' / legacy
            c.need(not former.exists() and not former.is_symlink(),
                   'Legacy directory must not remain active: ' + legacy)
        else:
            c.need('archived_entry' not in alias, 'Primary director must not be archived')
    c.need(registry.get('legacy_entry_archive') == LEGACY_ENTRY_ARCHIVE, 'Wrong legacy entry archive manifest')
    archive = c.read(LEGACY_ENTRY_ARCHIVE)
    archive_rows = archive.get('entries', [])
    retired = set(aliases) - {'operations_director'}
    c.need(len(archive_rows) == 30 and {row.get('legacy_id') for row in archive_rows} == retired,
           'Legacy entry archive must cover exactly 30 retired entries')
    # This manifest records the 2026-10-28 layout, before director consolidation.
    c.need(archive.get('status') == 'archived_not_active' and
           set(archive.get('active_agent_directories', [])) == CORE_ROLES | {'image-agent'},
           'Legacy entry archive status or active directory set mismatch')
    for row in archive_rows:
        legacy = row.get('legacy_id', '')
        expected_archive = LEGACY_ARCHIVE_ROOT + '/' + legacy + '/ENTRY.md'
        c.need(row.get('original_path') == 'agents/' + legacy + '/AGENTS.md' and
               row.get('archived_path') == expected_archive,
               'Legacy entry archive path mismatch: ' + legacy)
        c.hash(expected_archive, row.get('sha256'), 'Archived legacy entry SHA mismatch')
    c.need(registry.get('primary_entry_migration') == DIRECTOR_ENTRY_MIGRATION,
           'Wrong director entry migration manifest')
    migration = c.read(DIRECTOR_ENTRY_MIGRATION)
    expected_migration = {
        'date': '2026-10-29', 'status': 'archived_not_active', 'role': 'operations_director',
        'current_project': '.', 'current_entry': 'AGENTS.md',
        'original_path': 'agents/operations_director/AGENTS.md',
        'archived_path': DIRECTOR_ARCHIVE_ROOT + '/ENTRY.md',
    }
    for key, value in expected_migration.items():
        c.need(migration.get(key) == value, 'Director entry migration mismatch: ' + key)
    director_archive = expected_migration['archived_path']
    if c.file(director_archive, 'Missing archived director entry'):
        c.hash(director_archive, migration.get('sha256'), 'Archived director entry SHA mismatch')
    former_director = c.root / 'agents/operations_director'
    c.need(not former_director.exists() and not former_director.is_symlink(),
           'Director directory must not remain active')
    for relative_archive_root in (LEGACY_ARCHIVE_ROOT, DIRECTOR_ARCHIVE_ROOT):
        archive_root = c.root / relative_archive_root
        active_names = [str(p.relative_to(c.root)) for p in archive_root.rglob('*')
                        if (p.is_file() or p.is_symlink()) and
                        (p.name in {'AGENTS.md', 'AGENTS.override.md', 'SKILL.md'} or p.suffix == '.toml')]
        c.need(not active_names, 'Archive must not contain discoverable agent or skill entry names: ' + str(active_names))
    additional = c.read('catalog/additional-roles.json')
    if not isinstance(additional, list):
        c.errors.append('Additional role compatibility catalog must be a list')
        additional = []
    expected_additional = {'daily_report', 'profit_analyst', 'competition_analyst', 'market_opportunity',
                           'platform_knowledge', 'report_designer', 'title_optimizer', 'company_due_diligence'}
    c.need(len(additional) == 8 and {x.get('legacy_id') for x in additional} == expected_additional,
           'Additional role compatibility coverage mismatch')
    for row in additional:
        alias = aliases.get(row.get('legacy_id'), {})
        c.need(bool(alias) and all(row.get(key) == alias.get(key) for key in ('owner', 'capability', 'skill', 'rules')) and
               row.get('status') == 'capability_alias_not_additional_agent',
               'Additional role alias mismatch: ' + row.get('legacy_id', '?'))
    cross_platform = c.read('catalog/cross-platform-role.json')
    alias = aliases.get('cross_platform_distribution', {})
    c.need(cross_platform.get('legacy_id') == 'cross_platform_distribution' and
           all(cross_platform.get(key) == alias.get(key) for key in ('owner', 'capability', 'skill', 'rules')) and
           cross_platform.get('project') == roles.get(alias.get('owner'), {}).get('project') and
           str(Path(cross_platform.get('project', '')) / 'AGENTS.md') == alias.get('current_owner_entry') and
           cross_platform.get('archived_entry') == alias.get('archived_entry') and
           cross_platform.get('kind') == 'capability_alias' and
           cross_platform.get('status') == 'on_demand_capability_not_core_agent' and cross_platform.get('tools') == [],
           'Cross-platform compatibility alias mismatch')
    for role_id, role in roles.items():
        c.need(bool(role.get('project')), 'Missing role project: ' + role_id)
        c.file(str(Path(role.get('project', '')) / 'AGENTS.md'), 'Missing role entry')
        c.file(role.get('skill', ''), 'Missing role skill')
        c.need(role.get('skill') in {x.get('skill') for x in skill_rows if x.get('owner') == role_id},
               'Role skill is not owned by role: ' + role_id)
        for cap_id in role.get('capabilities', []):
            c.need(capabilities.get(cap_id, {}).get('owner') == role_id, 'Role capability mismatch: ' + role_id)
    director = roles.get('operations_director', {})
    c.need(director.get('project') == '.', 'Director must use the project root as its only entry')
    c.need(director.get('kind') == 'primary' and 'native_agent_config' not in director,
           'Director must remain the primary Agent, not a native subagent')
    review = registry.get('on_demand_review', {})
    c.need(review.get('id') == 'operations_review' and review.get('counts_as_core_agent') is False,
           'Review must be on demand and excluded from core count')
    native_files = {str(p.relative_to(c.root)) for p in (c.root / '.codex/agents').rglob('*.toml')}
    expected_native = {'.codex/agents/' + role + '.toml' for role in NATIVE_ROLES}
    c.need(native_files == expected_native, 'Native configs must contain only product/traffic/review/conversion_analysis')
    for role_id in NATIVE_ROLES:
        rel = '.codex/agents/' + role_id + '.toml'
        role = (review if role_id == 'operations_review' else conversion_specialist
                if role_id == 'conversion_analysis' else roles.get(role_id, {}))
        config_key = 'native_config' if role_id == 'conversion_analysis' else 'native_agent_config'
        c.need(role.get(config_key) == rel, 'Native config registry mismatch: ' + role_id)
        if c.file(rel, 'Missing native agent config'):
            try:
                native = read_native_config(c.root / rel)
                c.need(native['name'] == role_id, 'Native config name mismatch: ' + role_id)
                entry = (CONVERSION_SKILL if role_id == 'conversion_analysis'
                         else 'references/delegation.md' if role_id == 'operations_review'
                         else 'agents/' + role_id + '/AGENTS.md')
                c.need(entry in native['developer_instructions'],
                       'Native config does not load its entry: ' + role_id)
            except (OSError, ValueError) as exc:
                c.errors.append('Invalid native config: {}: {}'.format(rel, exc))
    active_skills = list((c.root / '.agents/skills').rglob('SKILL.md'))
    c.need({str(p.relative_to(c.root / '.agents/skills')) for p in active_skills} ==
           {name + '/SKILL.md' for name in ACTIVE_SKILL_NAMES},
           'Active skill discovery must contain only the 13 consolidated skills')
    for rel in sorted({x.get('skill', '') for x in skill_rows}):
        if not c.file(rel):
            continue
        p = c.root / rel
        text = p.read_text()
        match = re.search(r'^name:\s*([a-z0-9-]+)\s*$', text, re.M)
        c.need(bool(match) and match[1] == p.parent.name, 'Invalid skill name: ' + rel)
        ui = p.parent / 'agents/openai.yaml'
        c.need(ui.is_file(), 'Missing UI metadata: ' + rel)
        if ui.is_file() and match:
            c.need('$' + match[1] in ui.read_text(), 'Default prompt does not invoke skill: ' + rel)
        if rel.startswith('.agents/skills/'):
            c.need('scripts/task_context.py' in text and 'references/context-loading.md' in text,
                   'Active skill does not load staged task routing: ' + rel)
            if rel in original_rules:
                c.need(sha256(p) != original_rules[rel]['sha256'], 'Old skill still active: ' + rel)
    c.need(len(routes) == len(ROUTE_CAPABILITIES) and {x.get('id') for x in routes} == set(ROUTE_CAPABILITIES),
           'Task route coverage mismatch')
    for route in routes:
        route_id = route.get('id', '?')
        cap = capabilities.get(route.get('capability'), {})
        c.need(route.get('capability') == ROUTE_CAPABILITIES.get(route_id), 'Route capability mismatch: ' + route_id)
        c.need(route.get('owner') == cap.get('owner') and route.get('owner') in CORE_ROLES, 'Route owner mismatch: ' + route_id)
        c.need(route.get('skill') == cap.get('skill'), 'Route skill mismatch: ' + route_id)
        c.need(bool(route.get('rules')) and set(route.get('rules', [])).issubset(cap.get('rules', [])),
               'Route rules mismatch: ' + route_id)
        c.need(set(route.get('optional_capabilities', [])).issubset(capabilities), 'Unknown optional capability: ' + route_id)
        c.need(route.get('execution_protocol') == 'references/execution-protocol.md', 'Route execution protocol mismatch: ' + route_id)
        c.need(route.get('delegation_policy') == ROUTE_DELEGATION_POLICIES.get(route_id),
               'Route delegation policy mismatch: ' + route_id)
        c.need(bool(route.get('delegation')) and bool(route.get('rule_loading')), 'Route delegation/rule-loading contract missing: ' + route_id)
    for tool in tool_routing.get('tools', []):
        name = tool.get('name', '?')
        cap = capabilities.get(tool.get('primary_capability'), {})
        c.need(tool.get('primary_agent') == cap.get('owner') and tool.get('primary_agent') in CORE_ROLES,
               'Tool primary role/capability mismatch: ' + name)
        caps = tool.get('capabilities', [])
        c.need(tool.get('primary_capability') in caps and set(caps).issubset(capabilities), 'Tool capability coverage mismatch: ' + name)
        allowed_rules = {rule for cap_id in caps for rule in capabilities.get(cap_id, {}).get('rules', [])}
        c.need(bool(tool.get('rules')) and set(tool.get('rules', [])).issubset(allowed_rules), 'Tool rules mismatch: ' + name)
        alias = aliases.get(tool.get('legacy_primary_agent'), {})
        c.need(bool(alias) and set(alias.get('rules', [])).issubset(tool.get('rules', [])), 'Tool legacy evidence missing: ' + name)
        hint = tool.get('planning_hint', {})
        c.need(hint.get('primary_agent') == tool.get('primary_agent'), 'Tool planning owner mismatch: ' + name)
        c.need(hint.get('live_describe_tool_required') is True, 'Tool live describe guard missing: ' + name)
        c.need(tool.get('execution_protocol') == 'references/execution-protocol.md', 'Tool execution protocol mismatch: ' + name)
        if 'traffic_analysis' in caps:
            c.need(hint.get('operation_classes') == ['query'], 'Unverified traffic write capability: ' + name)
    source_rows = mapping.get('skills', [])
    actual_sources = {str(p.relative_to(c.root)) for p in (c.root / 'source').rglob('SKILL.md')}
    c.need(len(source_rows) == mapping.get('source_skill_count') == 107 and
           {x.get('source') for x in source_rows} == actual_sources, 'Source skill mapping incomplete')
    for row in source_rows:
        alias = aliases.get(row.get('legacy_agent'), {})
        c.need(bool(alias) and row.get('agent') == alias.get('owner') and row.get('capability') == alias.get('capability') and
               row.get('skill') == alias.get('skill') and row.get('preserved_rules') == alias.get('rules'),
               'Source alias routing mismatch: ' + row.get('source', '?'))
    check_original_snapshot(c, preservation, tool_routing.get('tools', []))
    check_links(c)
    return {'passed': not c.errors, 'agent_count': len(roles), 'capability_count': len(capabilities),
            'active_agent_directory_count': len(agent_directories), 'archived_legacy_entry_count': len(archive_rows),
            'on_demand_specialist_count': len(registry.get('on_demand_specialists') or []),
            'native_agent_config_count': len(native_files),
            'task_route_count': len(routes), 'legacy_alias_count': len(aliases), 'source_skill_entries': len(actual_sources),
            'business_rule_files_hash_checked': len(original_rules), 'errors': c.errors}


def check_package(root=ROOT):
    c = Checks(root)
    routing_result = check_routing(c.root)
    c.errors.extend(routing_result['errors'])
    context_document_count = check_context_documents(c)
    checked_files = set()
    for name in ('local-files.json', 'desktop-files.json', 'remote-plugin-files.json',
                 'remote-skills-files.json', 'bridge-files.json', 'desktop-resource-files.json'):
        data = c.read('manifests/' + name)
        rows = data if isinstance(data, list) else data.get('files', [])
        c.need(bool(rows), 'Empty source manifest: ' + name)
        for item in rows:
            rel = item.get('target') or item.get('relative_destination') or item.get('destination')
            if not rel:
                c.errors.append('Missing manifest target: ' + name)
                continue
            c.hash(rel, item['sha256'], 'Source SHA mismatch')
            p = (c.root / rel).resolve()
            if p.is_relative_to(c.root):
                checked_files.add(str(p.relative_to(c.root)))
    templates = c.read('source/desktop/templates/provenance.json')
    for item in templates.get('files', []):
        c.hash('source/desktop/templates/' + item['path'], item['sha256'], 'Template SHA mismatch')
    for category in templates.get('design_categories', []):
        c.need(category['count'] == category['expected_total'] == category['unique_count'], 'Incomplete design category: ' + category['id'])
    c.need(templates.get('design_prompt_count') == 265 and sum(x['count'] for x in templates.get('design_categories', [])) == 265,
           'Design template count must remain 265')
    routing = c.read('catalog/tool-routing.json')
    schemas = c.read('catalog/live-tool-schemas.json')
    tools = routing.get('tools', [])
    names = [x['name'] for x in tools]
    catalog_path = c.root / 'catalog/2026-10-25-tool-catalog.md'
    reference_names = re.findall(r'^\| `([^`]+)` \|', catalog_path.read_text(), re.M) if catalog_path.is_file() else []
    c.need(len(names) == len(set(names)) == 205, 'Tool routing must cover exactly 205 distinct snapshot tools')
    c.need(set(names) == set(reference_names), 'Tool routing differs from user supplied catalog')
    schema_names = [x['name'] for x in schemas.get('tools', [])]
    c.need(len(schema_names) == len(set(schema_names)) == 205 and set(names) == set(schema_names), 'Live schema and routing sets differ')
    preservation = c.read(PRESERVATION)
    protected = preservation.get('protected_unchanged_files', [])
    c.need(len(protected) == len({x['path'] for x in protected}) == 2658,
           'Protected-file manifest must contain 2658 distinct original files')
    for row in protected:
        c.hash(row['path'], row['sha256'], 'Protected file SHA mismatch')
    forbidden = [str(p.relative_to(c.root)) for p in (c.root / 'source').rglob('*')
                 if p.is_file() and (p.name in {'.env', 'Cookies', 'credentials.enc', 'gateway-cli.json'} or p.suffix == '.pyc')]
    c.need(not forbidden, 'Excluded sensitive/cache filenames present: ' + str(forbidden))
    return dict(routing_result, passed=not c.errors, date='2026-10-30', offline_only=True, tool_count=len(names),
                source_files_hash_checked=len(checked_files), protected_files_hash_checked=len(protected),
                context_documents_preservation_checked=context_document_count,
                design_prompt_count=templates.get('design_prompt_count'), errors=c.errors)


if __name__ == '__main__':
    result = check_package()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['passed'] else 1)
