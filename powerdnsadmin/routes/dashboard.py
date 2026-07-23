import datetime
import json
from collections import namedtuple
from flask import Blueprint, render_template, url_for, current_app, request, jsonify, redirect, g, session, abort
from flask_login import login_required, current_user, login_manager
from sqlalchemy import not_
from sqlalchemy.orm import joinedload

from ..decorators import (
    can_access_domain, can_configure_dnssec, operator_role_required)
from ..models.user import User, Anonymous
from ..models.account import Account
from ..models.account_user import AccountUser
from ..models.domain import Domain
from ..models.dnssec_rollover import DnssecRollover, DnssecRolloverKey
from ..models.domain_user import DomainUser
from ..models.setting import Setting
from ..models.history import History
from ..models.server import Server
from ..models.base import db
from ..services.dnssec import check_parent_ds, dnssec_key_identity

dashboard_bp = Blueprint('dashboard',
                         __name__,
                         template_folder='templates',
                         url_prefix='/dashboard')


DNSSEC_KEY_TYPES = (
    {'value': 'csk', 'label': 'CSK — Combined Signing Key (recommended)'},
    {'value': 'ksk', 'label': 'KSK — Key Signing Key'},
    {'value': 'zsk', 'label': 'ZSK — Zone Signing Key'},
)

DNSSEC_ALGORITHMS = (
    {
        'value': 'ecdsa256',
        'label': 'ECDSA P-256 / SHA-256 (algorithm 13)',
        'bits': (256,),
        'default_bits': 256,
    },
    {
        'value': 'ecdsa384',
        'label': 'ECDSA P-384 / SHA-384 (algorithm 14)',
        'bits': (384,),
        'default_bits': 384,
    },
    {
        'value': 'ed25519',
        'label': 'Ed25519 (algorithm 15)',
        'bits': (256,),
        'default_bits': 256,
    },
    {
        'value': 'ed448',
        'label': 'Ed448 (algorithm 16)',
        'bits': (456,),
        'default_bits': 456,
    },
    {
        'value': 'rsasha256',
        'label': 'RSA / SHA-256 (algorithm 8)',
        'bits': (1024, 2048, 3072, 4096),
        'default_bits': 2048,
    },
    {
        'value': 'rsasha512',
        'label': 'RSA / SHA-512 (algorithm 10)',
        'bits': (1024, 2048, 3072, 4096),
        'default_bits': 2048,
    },
)

DNSSEC_ROLLOVER_TYPES = (
    {
        'value': 'csk',
        'label': 'CSK rollover',
        'description': 'Add a second active, published CSK.',
    },
    {
        'value': 'ksk',
        'label': 'KSK rollover',
        'description': 'Add a second active, published KSK.',
    },
    {
        'value': 'zsk',
        'label': 'ZSK rollover',
        'description': 'Pre-publish a new inactive ZSK.',
    },
    {
        'value': 'algorithm',
        'label': 'Algorithm rollover',
        'description': 'Stage an active, unpublished replacement key.',
    },
)

DNSSEC_ALGORITHM_ALIASES = {
    'ecdsa256': {'ecdsa256', 'ecdsap256sha256', '13'},
    'ecdsa384': {'ecdsa384', 'ecdsap384sha384', '14'},
    'ed25519': {'ed25519', '15'},
    'ed448': {'ed448', '16'},
    'rsasha256': {'rsasha256', '8'},
    'rsasha512': {'rsasha512', '10'},
}


def _validate_dnssec_key_parameters(data):
    """Validate a v2 DNSSEC key request against the choices shown in the UI."""
    key_types = {item['value'] for item in DNSSEC_KEY_TYPES}
    algorithms = {item['value']: item for item in DNSSEC_ALGORITHMS}
    keytype = str(data.get('keytype', '')).lower()
    algorithm = str(data.get('algorithm', '')).lower()

    if keytype not in key_types:
        return None, 'Select a supported DNSSEC key type.'
    if algorithm not in algorithms:
        return None, 'Select a supported DNSSEC algorithm.'

    try:
        bits = int(data.get('bits'))
    except (TypeError, ValueError):
        return None, 'Select a valid DNSSEC key size.'
    if bits not in algorithms[algorithm]['bits']:
        return None, 'The selected key size is not valid for this algorithm.'

    return {
        'keytype': keytype,
        'algorithm': algorithm,
        'bits': bits,
        'active': True,
        'published': True,
    }, None


def _serialize_dnssec_key(key):
    """Return public cryptokey fields used by the dashboard v2 client."""
    return {
        'id': key.get('id'),
        'keytype': key.get('keytype'),
        'active': bool(key.get('active')),
        'published': bool(key.get('published')),
        'algorithm': key.get('algorithm'),
        'bits': key.get('bits'),
        'dnskey': key.get('dnskey'),
        'ds': key.get('ds') or [],
        'cds': key.get('cds') or [],
    }


def _validate_dnssec_rollover_parameters(data, existing_keys):
    """Validate and derive the safe initial state for a rollover key."""
    parameters, error = _validate_dnssec_key_parameters(data)
    if error:
        return None, error

    rollover_type = str(data.get('rollover_type', '')).lower()
    rollover_types = {item['value'] for item in DNSSEC_ROLLOVER_TYPES}
    if rollover_type not in rollover_types:
        return None, 'Select a supported rollover type.'

    if rollover_type != 'algorithm':
        parameters['keytype'] = rollover_type

    old_keys = [
        key for key in existing_keys
        if key.get('active')
        and str(key.get('keytype', '')).lower() == parameters['keytype']
    ]
    if not old_keys:
        return None, (
            'A {0} rollover requires an existing active {0} key.'.format(
                parameters['keytype'].upper()))

    if rollover_type != 'algorithm':
        selected_aliases = DNSSEC_ALGORITHM_ALIASES[parameters['algorithm']]
        if any(str(key.get('algorithm', '')).lower() not in selected_aliases
               for key in old_keys):
            return None, (
                'Changing algorithms requires the Algorithm rollover option.')
    else:
        selected_aliases = DNSSEC_ALGORITHM_ALIASES[parameters['algorithm']]
        if all(str(key.get('algorithm', '')).lower() in selected_aliases
               for key in old_keys):
            return None, 'Select a different algorithm for an algorithm rollover.'

    if rollover_type == 'zsk':
        parameters['active'] = False
        parameters['published'] = True
    elif rollover_type == 'algorithm':
        parameters['active'] = True
        parameters['published'] = False
    else:
        parameters['active'] = True
        parameters['published'] = True

    return {
        'rollover_type': rollover_type,
        'key_parameters': parameters,
        'old_key_ids': [int(key['id']) for key in old_keys],
    }, None


def _active_dnssec_rollover(domain_id):
    return DnssecRollover.query.filter(
        DnssecRollover.domain_id == domain_id,
        DnssecRollover.active.is_(True),
    ).order_by(DnssecRollover.started_at.desc()).first()


def _reconcile_dnssec_rollover(rollover, current_keys):
    """Resolve backend-local IDs from stable public DNSKEY fingerprints."""
    if not rollover.key_references:
        return {
            'state': 'needs_reconciliation',
            'changed': False,
            'issues': [{
                'reason': 'legacy_reference',
                'message': (
                    'This rollover predates stable key fingerprints and '
                    'cannot be matched safely from numeric IDs alone.'),
            }],
            'keys': [],
        }

    current_identities = []
    issues = []
    for key in current_keys:
        try:
            current_identities.append(dnssec_key_identity(key))
        except (KeyError, TypeError, ValueError) as error:
            issues.append({
                'reason': 'invalid_backend_key',
                'backendKeyId': key.get('id'),
                'message': str(error),
            })

    identities_by_fingerprint = {}
    for identity in current_identities:
        identities_by_fingerprint.setdefault(
            identity['fingerprint'], []).append(identity)

    changed = False
    reconciled_keys = []
    for reference in rollover.key_references:
        matches = identities_by_fingerprint.get(reference.fingerprint, [])
        if len(matches) == 0:
            issues.append({
                'reason': 'missing_key',
                'role': reference.role,
                'fingerprint': reference.fingerprint,
                'backendKeyId': reference.backend_key_id,
                'message': 'The referenced public DNSKEY is missing from PowerDNS.',
            })
            continue
        if len(matches) > 1:
            issues.append({
                'reason': 'ambiguous_key',
                'role': reference.role,
                'fingerprint': reference.fingerprint,
                'backendKeyIds': [match['backendKeyId'] for match in matches],
                'message': (
                    'More than one PowerDNS key has the referenced public DNSKEY.'),
            })
            continue

        match = matches[0]
        previous_backend_id = reference.backend_key_id
        if previous_backend_id != match['backendKeyId']:
            reference.backend_key_id = match['backendKeyId']
            changed = True
        reconciled_keys.append({
            'role': reference.role,
            'fingerprint': reference.fingerprint,
            'keyTag': reference.key_tag,
            'previousBackendKeyId': previous_backend_id,
            'backendKeyId': match['backendKeyId'],
            'backendIdChanged': previous_backend_id != match['backendKeyId'],
        })

    if issues:
        return {
            'state': 'needs_reconciliation',
            'changed': changed,
            'issues': issues,
            'keys': reconciled_keys,
        }

    rollover.old_keys = [
        reference.backend_key_id for reference in rollover.key_references
        if reference.role == 'old'
    ]
    rollover.new_keys = [
        reference.backend_key_id for reference in rollover.key_references
        if reference.role == 'new'
    ]
    return {
        'state': 'ok',
        'changed': changed,
        'issues': [],
        'keys': reconciled_keys,
    }


def _rollover_guidance(rollover, delegation, reconciliation=None):
    if reconciliation and reconciliation.get('state') != 'ok':
        return {
            'message': (
                'The rollover key identities cannot be reconciled safely with '
                'PowerDNS. Cancellation and key retirement are blocked until '
                'the missing or ambiguous public keys are resolved.'),
            'newKeyPropagated': False,
            'cancellationAllowed': False,
            'retirementBlocked': True,
        }
    new_key_states = [
        expectation for expectation in delegation.get('expectedKeys', [])
        if expectation.get('keyId') in rollover.new_keys
    ]
    new_key_propagated = bool(new_key_states) and all(
        expectation.get('propagated') for expectation in new_key_states)
    new_key_seen = any(
        expectation.get('matchedNameservers', 0) > 0
        for expectation in new_key_states)
    cancellation_allowed = (
        delegation.get('state') == 'undelegated'
        or (delegation.get('state') != 'error'
            and delegation.get('summary', {}).get(
                'failedNameservers', 0) == 0
            and not new_key_seen))

    if rollover.rollover_type in ('ksk', 'csk'):
        if delegation.get('state') == 'undelegated':
            message = (
                'This zone is not delegated by a public parent. The new key '
                'is staged, but no registrar DS action is available.')
        elif new_key_propagated:
            message = (
                'The new key DS is present on every parent nameserver. The '
                'old key remains protected until parent DS TTL tracking is complete.')
        else:
            message = (
                'Publish one DS digest for the new key at the registrar. The '
                'old key remains active while propagation is checked.')
    elif rollover.rollover_type == 'zsk':
        message = (
            'The new inactive ZSK is published. DNSKEY TTL and authoritative '
            'visibility must be verified before signer activation changes.')
    else:
        message = (
            'The new algorithm key is active but unpublished. Maximum zone '
            'TTL tracking is required before it can be published safely.')

    return {
        'message': message,
        'newKeyPropagated': new_key_propagated,
        'cancellationAllowed': cancellation_allowed,
        'retirementBlocked': True,
    }


class ZoneTabs:
    """Config data for the zone tabs on the dashboard."""

    TabInfo = namedtuple('TabInfo', ['display_name', 'filter_pattern'])
    """Info about a single tab.

    `display_name` is the name on the tab.
    `filter_pattern` is a SQL LIKE pattern , which is case-insensitively matched against the zone
    name (without the final root-dot).

    If a filter is present, the tab will show zones that match the filter.
    If no filter is present, the tab will show zones that are not matched by any other tab filter.
    """

    tabs = {
        'forward': TabInfo("", None),
        'reverse_ipv4': TabInfo("in-addr.arpa", '%.in-addr.arpa'),
        'reverse_ipv6': TabInfo("ip6.arpa", '%.ip6.arpa'),
    }
    """Dict of unique tab id to a TabInfo."""

    order = ['forward', 'reverse_ipv4', 'reverse_ipv6']
    """List of tab ids in the order they will appear."""


def _bounded_integer(value, default, minimum=None, maximum=None):
    """Return a bounded integer, falling back to a known-safe default."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = int(default)

    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def _request_integer(name, default, minimum=None, maximum=None):
    """Return a bounded integer query argument for a dashboard data request."""
    return _bounded_integer(
        request.args.get(name), default, minimum=minimum, maximum=maximum)


def _dashboard_v2_domains_query():
    """Build a de-duplicated zone query scoped to the signed-in user."""
    if current_user.role.name in ['Administrator', 'Operator']:
        return Domain.query.outerjoin(Account)

    direct_domain_ids = db.session.query(DomainUser.domain_id).filter(
        DomainUser.user_id == current_user.id)
    account_ids = db.session.query(AccountUser.account_id).filter(
        AccountUser.user_id == current_user.id)
    return Domain.query.filter(db.or_(
        Domain.id.in_(direct_domain_ids),
        Domain.account_id.in_(account_ids),
    ))


def _filter_dashboard_v2_tab(domains, tab_id):
    tab = ZoneTabs.tabs[tab_id]
    if tab.filter_pattern:
        return domains.filter(Domain.name.ilike(tab.filter_pattern))

    for tab_info in ZoneTabs.tabs.values():
        if tab_info.filter_pattern:
            domains = domains.filter(
                not_(Domain.name.ilike(tab_info.filter_pattern)))
    return domains


@dashboard_bp.before_request
def before_request():
    # Check if user is anonymous
    g.user = current_user
    login_manager.anonymous_user = Anonymous

    # Check site is in maintenance mode
    maintenance = Setting().get('maintenance')
    if maintenance and current_user.is_authenticated and current_user.role.name not in [
        'Administrator', 'Operator'
    ]:
        return render_template('maintenance.html')

    # Manage session timeout
    session.permanent = True
    current_app.permanent_session_lifetime = datetime.timedelta(
        minutes=int(Setting().get('session_timeout')))
    session.modified = True


@dashboard_bp.route('/domains-custom/<path:tab_id>', methods=['GET'])
@login_required
def domains_custom(tab_id):
    if tab_id not in ZoneTabs.tabs:
        abort(404)

    if current_user.role.name in ['Administrator', 'Operator']:
        domains = Domain.query
    else:
        # Get query for domain to which the user has access permission.
        # This includes direct domain permission AND permission through
        # account membership
        domains = db.session.query(Domain) \
            .outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
            .outerjoin(Account, Domain.account_id == Account.id) \
            .outerjoin(AccountUser, Account.id == AccountUser.account_id) \
            .filter(
            db.or_(
                DomainUser.user_id == current_user.id,
                AccountUser.user_id == current_user.id
            ))

    template = current_app.jinja_env.get_template("dashboard_domain.html")
    render = template.make_module(
        vars={"current_user": current_user, "allow_user_view_history": Setting().get('allow_user_view_history')})

    columns = [
        Domain.name, Domain.dnssec, Domain.type, Domain.serial, Domain.master,
        Domain.account_id
    ]

    order_by = []
    for i in range(len(columns)):
        column_index = request.args.get("order[{0}][column]".format(i))
        sort_direction = request.args.get("order[{0}][dir]".format(i))
        if column_index is None:
            break
        if sort_direction != "asc" and sort_direction != "desc":
            sort_direction = "asc"

        column = columns[int(column_index)]
        order_by.append(getattr(column, sort_direction)())

    if order_by:
        domains = domains.order_by(*order_by)

    if ZoneTabs.tabs[tab_id].filter_pattern:
        # If the tab has a filter, use only that
        domains = domains.filter(Domain.name.ilike(ZoneTabs.tabs[tab_id].filter_pattern))
    else:
        # If the tab has no filter, use all the other filters in negated form
        for tab_info in ZoneTabs.tabs.values():
            if not tab_info.filter_pattern:
                continue
            domains = domains.filter(not_(Domain.name.ilike(tab_info.filter_pattern)))

    total_count = domains.count()

    search = request.args.get("search[value]")
    if search:
        start = "" if search.startswith("^") else "%"
        end = "" if search.endswith("$") else "%"

        if current_user.role.name in ['Administrator', 'Operator']:
            domains = domains.outerjoin(Account).filter(
                Domain.name.ilike(start + search.strip("^$") + end)
                | Account.name.ilike(start + search.strip("^$") + end)
                | Account.description.ilike(start + search.strip("^$") + end))
        else:
            domains = domains.filter(
                Domain.name.ilike(start + search.strip("^$") + end))

    filtered_count = domains.count()

    start = int(request.args.get("start", 0))
    length = min(int(request.args.get("length", 0)), max(100, int(Setting().get('default_domain_table_size'))))

    if length != -1:
        domains = domains[start:start + length]

    data = []
    for domain in domains:
        data.append([
            render.name(domain),
            render.dnssec(domain),
            render.type(domain),
            render.serial(domain),
            render.master(domain),
            render.account(domain),
            render.actions(domain),
        ])

    response_data = {
        "draw": int(request.args.get("draw", 0)),
        "recordsTotal": total_count,
        "recordsFiltered": filtered_count,
        "data": data,
    }
    return jsonify(response_data)


@dashboard_bp.route('/v2/domains/<path:tab_id>', methods=['GET'])
@login_required
def domains_v2(tab_id):
    """Return structured, paginated zone data for the v2 dashboard."""
    if tab_id not in ZoneTabs.tabs:
        abort(404)

    # The classic dashboard performs this update before returning any HTML.
    # V2 defers it to the first data request so the loading state can render.
    if (tab_id == ZoneTabs.order[0]
            and request.args.get('refresh') == '1'
            and not Setting().get('bg_domain_updates')):
        current_app.logger.info(
            'Updating zones in foreground for dashboard v2 data request...')
        Domain().update()

    domains = _filter_dashboard_v2_tab(
        _dashboard_v2_domains_query(), tab_id)
    total_count = domains.count()

    search = request.args.get('search[value]', '').strip()
    if search:
        start_wildcard = '' if search.startswith('^') else '%'
        end_wildcard = '' if search.endswith('$') else '%'
        pattern = start_wildcard + search.strip('^$') + end_wildcard
        if current_user.role.name in ['Administrator', 'Operator']:
            domains = domains.filter(db.or_(
                Domain.name.ilike(pattern),
                Account.name.ilike(pattern),
                Account.description.ilike(pattern),
            ))
        else:
            domains = domains.filter(Domain.name.ilike(pattern))

    filtered_count = domains.count()

    sortable_columns = {
        0: Domain.name,
        1: Domain.dnssec,
        2: Domain.type,
        3: Domain.serial,
        4: Domain.master,
        5: Account.name if current_user.role.name in ['Administrator', 'Operator'] else Domain.account_id,
    }
    order_by = []
    order_index = 0
    while True:
        column_arg = request.args.get(
            'order[{0}][column]'.format(order_index))
        if column_arg is None:
            break
        try:
            column = sortable_columns.get(int(column_arg))
        except (TypeError, ValueError):
            column = None
        if column is not None:
            direction = request.args.get(
                'order[{0}][dir]'.format(order_index), 'asc')
            order_by.append(column.desc() if direction == 'desc' else column.asc())
        order_index += 1

    domains = domains.order_by(*(order_by or [Domain.name.asc()]))
    start = _request_integer('start', 0, minimum=0)
    length = _request_integer(
        'length', Setting().get('default_domain_table_size'),
        minimum=1, maximum=100)
    domains = domains.options(joinedload(Domain.account)).offset(start).limit(length)

    is_operator = current_user.role.name in ['Administrator', 'Operator']
    allow_history = is_operator or Setting().get('allow_user_view_history')
    allow_remove = is_operator or Setting().get('allow_user_remove_domain')
    allow_dnssec = is_operator or not Setting().get('dnssec_admins_only')

    data = []
    for domain in domains.all():
        data.append({
            'id': domain.id,
            'name': domain.name,
            'dnssec': bool(domain.dnssec),
            'type': domain.type,
            'serial': domain.serial,
            'notifiedSerial': domain.notified_serial,
            'primary': domain.master,
            'account': (domain.account.name if is_operator and domain.account
                        else 'None'),
            'permissions': {
                'manageZone': is_operator,
                'viewHistory': allow_history,
                'removeZone': allow_remove,
                'manageDnssec': allow_dnssec,
            },
            'urls': {
                'records': url_for('domain.domain', domain_name=domain.name),
                'settings': url_for('domain.setting', domain_name=domain.name),
                'changelog': url_for('domain.changelog', domain_name=domain.name),
                'remove': url_for('domain.remove'),
                'dnssecEnableV2': url_for(
                    'dashboard.dnssec_enable_v2', domain_name=domain.name),
                'dnssecStatusV2': url_for(
                    'dashboard.dnssec_status_v2', domain_name=domain.name),
            },
        })

    return jsonify({
        'draw': _request_integer('draw', 0, minimum=0),
        'recordsTotal': total_count,
        'recordsFiltered': filtered_count,
        'data': data,
    })


@dashboard_bp.route(
    '/v2/domains/<path:domain_name>/dnssec/enable', methods=['POST'])
@login_required
@can_access_domain
@can_configure_dnssec
def dnssec_enable_v2(domain_name):
    """Enable DNSSEC with explicitly selected key parameters for dashboard v2."""
    parameters, validation_error = _validate_dnssec_key_parameters(
        request.form)
    if validation_error:
        return jsonify({
            'status': 'error',
            'msg': validation_error,
        }), 400

    domain = Domain.query.filter(Domain.name == domain_name).first()
    if domain is None:
        abort(404)

    result = Domain().enable_domain_dnssec(
        domain_name, key_parameters=parameters)
    if result.get('status') != 'ok':
        return jsonify(result), 502

    domain.dnssec = 1
    History(
        msg='DNSSEC was enabled for zone ' + domain_name,
        detail=json.dumps({
            'source': 'dashboard_v2',
            'key': parameters,
        }),
        created_by=current_user.username,
        domain_id=domain.id,
    ).add()

    return jsonify({
        'status': 'ok',
        'msg': 'DNSSEC was enabled successfully.',
        'key': parameters,
    })


@dashboard_bp.route(
    '/v2/domains/<path:domain_name>/dnssec/rollovers', methods=['POST'])
@login_required
@can_access_domain
@can_configure_dnssec
def dnssec_rollover_create_v2(domain_name):
    """Stage one replacement key without changing an existing key."""
    domain = Domain.query.filter(Domain.name == domain_name).with_for_update().first()
    if domain is None:
        abort(404)
    if not domain.dnssec:
        return jsonify({
            'status': 'error',
            'msg': 'Enable DNSSEC before starting a rollover.',
        }), 409
    if _active_dnssec_rollover(domain.id):
        return jsonify({
            'status': 'error',
            'msg': 'This zone already has an active DNSSEC rollover.',
        }), 409

    dnssec = Domain().get_domain_dnssec(domain_name)
    if dnssec.get('status') != 'ok':
        return jsonify(dnssec), 502
    keys = [_serialize_dnssec_key(key) for key in dnssec.get('dnssec', [])]
    rollover_data, validation_error = _validate_dnssec_rollover_parameters(
        request.form, keys)
    if validation_error:
        return jsonify({
            'status': 'error',
            'msg': validation_error,
        }), 400

    parameters = rollover_data['key_parameters']
    keys_by_id = {int(key['id']): key for key in keys if key.get('id') is not None}
    try:
        old_key_identities = [
            dnssec_key_identity(keys_by_id[key_id])
            for key_id in rollover_data['old_key_ids']
        ]
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({
            'status': 'error',
            'msg': (
                'The existing PowerDNS keys do not contain enough public data '
                'to track this rollover safely: {}'.format(error)),
        }), 502

    rollover = DnssecRollover(
        domain_id=domain.id,
        rollover_type=rollover_data['rollover_type'],
        keytype=parameters['keytype'],
        state='planned',
        algorithm=parameters['algorithm'],
        bits=parameters['bits'],
        started_by=current_user.username,
        active=True,
    )
    rollover.old_keys = rollover_data['old_key_ids']
    rollover.new_keys = []
    db.session.add(rollover)
    for identity in old_key_identities:
        DnssecRolloverKey.from_identity(rollover, 'old', identity)
    db.session.commit()

    result = Domain().create_dnssec_key(domain_name, parameters)
    if result.get('status') != 'ok':
        rollover.state = 'failed'
        rollover.active = False
        rollover.error = result.get('msg')
        db.session.commit()
        return jsonify(result), 502

    key = _serialize_dnssec_key(result.get('key') or {})
    try:
        new_key_identity = dnssec_key_identity(key)
    except (KeyError, TypeError, ValueError) as error:
        if key.get('id') is not None:
            Domain().delete_dnssec_key(domain_name, key['id'])
        rollover.state = 'failed'
        rollover.active = False
        rollover.error = (
            'PowerDNS created a key without returning a complete public '
            'identity: {}'.format(error))
        db.session.commit()
        return jsonify({
            'status': 'error',
            'msg': rollover.error,
        }), 502

    DnssecRolloverKey.from_identity(rollover, 'new', new_key_identity)
    rollover.new_keys = [new_key_identity['backendKeyId']]
    rollover.state = (
        'algorithm_key_staged'
        if rollover.rollover_type == 'algorithm'
        else 'new_key_published')
    db.session.commit()

    History(
        msg='DNSSEC rollover was started for zone ' + domain_name,
        detail=json.dumps({
            'source': 'dashboard_v2',
            'rollover_id': rollover.id,
            'rollover_type': rollover.rollover_type,
            'old_key_ids': rollover.old_keys,
            'new_key_ids': rollover.new_keys,
            'key': parameters,
        }),
        created_by=current_user.username,
        domain_id=domain.id,
    ).add()

    return jsonify({
        'status': 'ok',
        'msg': 'The replacement key was staged. No existing key was changed.',
        'rollover': rollover.to_dict(),
    }), 201


@dashboard_bp.route(
    '/v2/domains/<path:domain_name>/dnssec/rollovers/<int:rollover_id>/cancel',
    methods=['POST'])
@login_required
@can_access_domain
@can_configure_dnssec
def dnssec_rollover_cancel_v2(domain_name, rollover_id):
    """Remove a staged replacement only while no parent uses its DS."""
    domain = Domain.query.filter(Domain.name == domain_name).first()
    if domain is None:
        abort(404)
    rollover = DnssecRollover.query.filter(
        DnssecRollover.id == rollover_id,
        DnssecRollover.domain_id == domain.id,
        DnssecRollover.active.is_(True),
    ).first()
    if rollover is None:
        abort(404)

    dnssec = Domain().get_domain_dnssec(domain_name)
    if dnssec.get('status') != 'ok':
        return jsonify(dnssec), 502
    keys = [_serialize_dnssec_key(key) for key in dnssec.get('dnssec', [])]
    reconciliation = _reconcile_dnssec_rollover(rollover, keys)
    if reconciliation.get('changed'):
        db.session.commit()
    if reconciliation.get('state') != 'ok':
        return jsonify({
            'status': 'error',
            'msg': (
                'The rollover key identities could not be reconciled safely. '
                'No keys were changed.'),
            'reconciliation': reconciliation,
        }), 409

    delegation = check_parent_ds(domain_name, keys)
    if (delegation.get('state') != 'undelegated'
            and (delegation.get('state') == 'error'
                 or delegation.get('summary', {}).get(
                     'failedNameservers', 0) > 0)):
        return jsonify({
            'status': 'error',
            'msg': (
                'The parent could not be checked completely, so cancellation '
                'cannot safely determine whether the replacement DS is in use.'),
        }), 409
    replacement_expectations = [
        expectation for expectation in delegation.get('expectedKeys', [])
        if expectation.get('keyId') in rollover.new_keys
    ]
    if any(expectation.get('matchedNameservers', 0) > 0
           for expectation in replacement_expectations):
        return jsonify({
            'status': 'error',
            'msg': (
                'The parent already serves a DS for the replacement key. '
                'Continue forward instead of cancelling the rollover.'),
        }), 409

    domain_model = Domain()
    replacement_key_ids = [
        reference.backend_key_id for reference in rollover.key_references
        if reference.role == 'new'
    ]
    for key_id in replacement_key_ids:
        if not any(key.get('id') == key_id for key in keys):
            continue
        result = domain_model.delete_dnssec_key(domain_name, key_id)
        if result.get('status') != 'ok':
            rollover.error = result.get('msg')
            db.session.commit()
            return jsonify(result), 502

    rollover.state = 'cancelled'
    rollover.active = False
    rollover.completed_at = datetime.datetime.utcnow()
    rollover.error = None
    db.session.commit()

    History(
        msg='DNSSEC rollover was cancelled for zone ' + domain_name,
        detail=json.dumps({
            'source': 'dashboard_v2',
            'rollover_id': rollover.id,
            'removed_key_ids': replacement_key_ids,
        }),
        created_by=current_user.username,
        domain_id=domain.id,
    ).add()
    return jsonify({
        'status': 'ok',
        'msg': 'The staged replacement key was removed.',
    })


@dashboard_bp.route(
    '/v2/domains/<path:domain_name>/dnssec', methods=['GET'])
@login_required
@can_access_domain
def dnssec_status_v2(domain_name):
    """Return public key state and a live parent DS propagation check."""
    domain = Domain.query.filter(Domain.name == domain_name).first()
    if domain is None:
        abort(404)

    dnssec = Domain().get_domain_dnssec(domain_name)
    if dnssec.get('status') != 'ok':
        return jsonify(dnssec), 502

    keys = [_serialize_dnssec_key(key) for key in dnssec.get('dnssec', [])]
    propagation = check_parent_ds(domain_name, keys)
    rollover = _active_dnssec_rollover(domain.id)
    rollover_data = None
    if rollover:
        reconciliation = _reconcile_dnssec_rollover(rollover, keys)
        if reconciliation.get('changed'):
            db.session.commit()
        rollover_data = rollover.to_dict()
        rollover_data['reconciliation'] = reconciliation
        rollover_data['guidance'] = _rollover_guidance(
            rollover, propagation, reconciliation)
        rollover_data['cancelUrl'] = url_for(
            'dashboard.dnssec_rollover_cancel_v2',
            domain_name=domain_name,
            rollover_id=rollover.id)
    return jsonify({
        'status': 'ok',
        'domain': domain_name,
        'enabled': bool(domain.dnssec),
        'keys': keys,
        'delegation': propagation,
        'rollover': rollover_data,
        'urls': {
            'createRollover': url_for(
                'dashboard.dnssec_rollover_create_v2',
                domain_name=domain_name),
        },
    })


@dashboard_bp.route('/v2/', methods=['GET'])
@login_required
def dashboard_v2():
    """Render the non-blocking, client-rendered dashboard preview."""
    if not Setting().get('pdns_api_url') or not Setting().get(
            'pdns_api_key') or not Setting().get('pdns_version'):
        return redirect(url_for('admin.setting_pdns'))

    bg_domain_updates = Setting().get('bg_domain_updates')
    show_bg_domain_button = (
        bg_domain_updates
        and current_user.role.name in ['Administrator', 'Operator'])
    default_page_length = _bounded_integer(
        Setting().get('default_domain_table_size'), 10,
        minimum=1, maximum=100)

    return render_template(
        'dashboard_v2.html',
        zone_tabs=ZoneTabs,
        show_bg_domain_button=show_bg_domain_button,
        refresh_on_first_load=not bg_domain_updates,
        default_page_length=default_page_length,
        dnssec_key_types=DNSSEC_KEY_TYPES,
        dnssec_algorithms=DNSSEC_ALGORITHMS,
        dnssec_rollover_types=DNSSEC_ROLLOVER_TYPES,
        pdns_version=Setting().get('pdns_version'))


@dashboard_bp.route('/', methods=['GET', 'POST'])
@login_required
def dashboard():
    if not Setting().get('pdns_api_url') or not Setting().get(
            'pdns_api_key') or not Setting().get('pdns_version'):
        return redirect(url_for('admin.setting_pdns'))

    BG_DOMAIN_UPDATE = Setting().get('bg_domain_updates')
    if not BG_DOMAIN_UPDATE:
        current_app.logger.info('Updating zones in foreground...')
        Domain().update()
    else:
        current_app.logger.info('Updating zones in background...')

    show_bg_domain_button = BG_DOMAIN_UPDATE
    if BG_DOMAIN_UPDATE and current_user.role.name not in ['Administrator', 'Operator']:
        show_bg_domain_button = False

    # Add custom boxes to render_template
    return render_template('dashboard.html',
                           zone_tabs=ZoneTabs,
                           show_bg_domain_button=show_bg_domain_button,
                           pdns_version=Setting().get('pdns_version'))


@dashboard_bp.route('/domains-updater', methods=['GET', 'POST'])
@login_required
@operator_role_required
def domains_updater():
    current_app.logger.debug('Update zones in background')
    d = Domain().update()

    response_data = {
        "result": d,
    }
    return jsonify(response_data)
