import datetime
from flask import Blueprint, render_template, url_for, current_app, request, jsonify, redirect, g, session
from flask_login import login_required, current_user, login_manager
from sqlalchemy import not_

from ..lib.utils import customBoxes
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


@dashboard_bp.route('/domains-custom/<path:boxId>', methods=['GET'])
@login_required
def domains_custom(boxId):
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
    render = template.make_module(vars={"current_user": current_user})

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

    if boxId == "reverse":
        for boxId in customBoxes.order:
            if boxId == "reverse": continue
            domains = domains.filter(
                not_(Domain.name.ilike(customBoxes.boxes[boxId][1])))
    else:
        domains = domains.filter(Domain.name.ilike(
            customBoxes.boxes[boxId][1]))

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
    length = min(int(request.args.get("length", 0)), 100)

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
        current_app.logger.info('Updating domains in foreground...')
        Domain().update()
    else:
        current_app.logger.info('Updating domains in background...')

    # Stats for dashboard
    domain_count = Domain.query.count()
    user_num = User.query.count()
    history_number = History.query.count()
    history = History.query.order_by(History.created_on.desc()).limit(4)
    server = Server(server_id='localhost')
    statistics = server.get_statistic()
    if statistics:
        uptime = list([
            uptime for uptime in statistics if uptime['name'] == 'uptime'
        ])[0]['value']
    else:
        uptime = 0

    # Add custom boxes to render_template
    return render_template('dashboard.html',
                           custom_boxes=customBoxes,
                           domain_count=domain_count,
                           user_num=user_num,
                           history_number=history_number,
                           uptime=uptime,
                           histories=history,
                           show_bg_domain_button=BG_DOMAIN_UPDATE,
                           pdns_version=Setting().get('pdns_version'))


@dashboard_bp.route('/domains-updater', methods=['GET', 'POST'])
@login_required
def domains_updater():
    current_app.logger.debug('Update domains in background')
    d = Domain().update()

    response_data = {
        "result": d,
    }
    return jsonify(response_data)
