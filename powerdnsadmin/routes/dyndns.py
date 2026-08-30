import json
import traceback
import ipaddress
from flask import Blueprint, render_template, request, current_app
from flask_login import current_user

from .base import csrf
from ..lib import utils
from ..decorators import dyndns_login_required
from ..models.base import db
from ..models.account import Account
from ..models.account_user import AccountUser
from ..models.domain import Domain
from ..models.domain_user import DomainUser
from ..models.domain_setting import DomainSetting
from ..models.record import Record
from ..models.history import History

dyndns_bp = Blueprint('dyndns',
                      __name__,
                      template_folder='templates',
                      url_prefix='/')


@dyndns_bp.route('/nic/checkip.html', methods=['GET', 'POST'])
@csrf.exempt
def dyndns_checkip():
    # This route covers the default ddclient 'web' setting for the checkip service
    return render_template('dyndns.html',
                           response=request.environ.get(
                               'HTTP_X_REAL_IP', request.remote_addr))


@dyndns_bp.route('/nic/update', methods=['GET', 'POST'])
@csrf.exempt
@dyndns_login_required
def dyndns_update():
    # dyndns protocol response codes in use are:
    # good: update successful
    # nochg: IP address already set to update address
    # nohost: hostname does not exist for this user account
    # 911: server error
    # have to use 200 HTTP return codes because ddclient does not read the return string if the code is other than 200
    # reference: https://help.dyn.com/remote-access-api/perform-update/
    # reference: https://help.dyn.com/remote-access-api/return-codes/
    hostname = request.args.get('hostname')
    myip = request.args.get('myip')

    if not hostname:
        history = History(msg="DynDNS update: missing hostname parameter",
                          created_by=current_user.username)
        history.add()
        return render_template('dyndns.html', response='nohost'), 200

    try:
        if current_user.role.name in ['Administrator', 'Operator']:
            domains = Domain.query.all()
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
                )).all()
    except Exception as e:
        current_app.logger.error('DynDNS Error: {0}'.format(e))
        current_app.logger.debug(traceback.format_exc())
        return render_template('dyndns.html', response='911'), 200

    domain = None
    domain_segments = hostname.split('.')
    for _index in range(len(domain_segments)):
        full_domain = '.'.join(domain_segments)
        potential_domain = Domain.query.filter(
            Domain.name == full_domain).first()
        if potential_domain in domains:
            domain = potential_domain
            break
        domain_segments.pop(0)

    if not domain:
        history = History(
            msg=
            "DynDNS update: attempted update of {0} but it does not exist for this user"
            .format(hostname),
            created_by=current_user.username)
        history.add()
        return render_template('dyndns.html', response='nohost'), 200

    myip_addr = []
    if myip:
        for address in myip.split(','):
            myip_addr += utils.validate_ipaddress(address)

    remote_addr = utils.validate_ipaddress(
        request.headers.get('X-Forwarded-For',
                            request.remote_addr).split(', ')[0])

    response = 'nochg'
    for ip in myip_addr or remote_addr:
        if isinstance(ip, ipaddress.IPv4Address):
            rtype = 'A'
        else:
            rtype = 'AAAA'

        r = Record(name=hostname, type=rtype)
        # Check if the user requested record exists within this domain
        if r.exists(domain.name) and r.is_allowed_edit():
            if r.data == str(ip):
                # Record content did not change, return 'nochg'
                history = History(
                    msg=
                    "DynDNS update: attempted update of {0} but record already up-to-date"
                    .format(hostname),
                    created_by=current_user.username,
                    domain_id=domain.id)
                history.add()
            else:
                oldip = r.data
                result = r.update(domain.name, str(ip))
                if result['status'] == 'ok':
                    history = History(
                        msg='DynDNS update: updated {} successfully'.format(hostname),
                        detail=json.dumps({
                            'domain': domain.name,
                            'record': hostname,
                            'type': rtype,
                            'old_value': oldip,
                            'new_value': str(ip)
                        }),
                        created_by=current_user.username,
                        domain_id=domain.id)
                    history.add()
                    response = 'good'
                else:
                    response = '911'
                    break
        elif r.is_allowed_edit():
            ondemand_creation = DomainSetting.query.filter(
                DomainSetting.domain == domain).filter(
                DomainSetting.setting == 'create_via_dyndns').first()
            if (ondemand_creation is not None) and utils.parse_boolean(
                    ondemand_creation.value):

                # Build the rrset
                rrset_data = [{
                    "changetype": "REPLACE",
                    "name": hostname + '.',
                    "ttl": 3600,
                    "type": rtype,
                    "records": [{
                        "content": str(ip),
                        "disabled": False
                    }],
                    "comments": []
                }]

                # Format the rrset
                rrset = {"rrsets": rrset_data}
                result = Record().add(domain.name, rrset)
                if result['status'] == 'ok':
                    history = History(
                        msg=
                        'DynDNS update: created record {0} in zone {1} successfully'
                        .format(hostname, domain.name, str(ip)),
                        detail=json.dumps({
                            'domain': domain.name,
                            'record': hostname,
                            'value': str(ip)
                        }),
                        created_by=current_user.username,
                        domain_id=domain.id)
                    history.add()
                    response = 'good'
        else:
            history = History(
                msg=
                'DynDNS update: attempted update of {0} but it does not exist for this user'
                .format(hostname),
                created_by=current_user.username)
            history.add()

    return render_template('dyndns.html', response=response), 200
