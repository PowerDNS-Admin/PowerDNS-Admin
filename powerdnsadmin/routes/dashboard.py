import datetime
from collections import namedtuple
from flask import Blueprint, render_template, url_for, current_app, request, jsonify, redirect, g, session, abort
from flask_login import login_required, current_user, login_manager
from sqlalchemy import not_

from ..decorators import operator_role_required
from ..models.user import User, Anonymous
from ..models.account import Account
from ..models.account_user import AccountUser
from ..models.domain import Domain
from ..models.domain_user import DomainUser
from ..models.setting import Setting
from ..models.history import History
from ..models.server import Server
from ..models.base import db

dashboard_bp = Blueprint('dashboard',
                         __name__,
                         template_folder='templates',
                         url_prefix='/dashboard')


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
