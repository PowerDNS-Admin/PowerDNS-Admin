import json
from urllib.parse import urljoin
from flask import Blueprint, g, request, abort, current_app, make_response, jsonify
from flask_login import current_user

from ..models.base import db
from ..models import User,Domain, DomainUser, Account, AccountUser, History, Setting, ApiKey
from ..lib import utils, helper
from ..lib.schema import ApiKeySchema, DomainSchema, ApiPlainKeySchema
from ..lib.errors import DomainNotExists, DomainAlreadyExists, DomainAccessForbidden, RequestIsNotJSON, ApiKeyCreateFail, ApiKeyNotUsable, NotEnoughPrivileges
from ..decorators import api_basic_auth, api_can_create_domain, is_json, apikey_auth, apikey_is_admin, apikey_can_access_domain

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

apikey_schema = ApiKeySchema(many=True)
domain_schema = DomainSchema(many=True)
apikey_plain_schema = ApiPlainKeySchema(many=True)


def get_user_domains():
    domains = db.session.query(Domain) \
        .outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
        .outerjoin(Account, Domain.account_id == Account.id) \
        .outerjoin(AccountUser, Account.id == AccountUser.account_id) \
        .filter(
            db.or_(
                DomainUser.user_id == current_user.id,
                AccountUser.user_id == current_user.id
            )).all()
    return domains


def get_user_apikeys(domain_name=None):
    info = []
    apikey_query = db.session.query(ApiKey) \
        .join(Domain.apikeys) \
        .outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
        .outerjoin(Account, Domain.account_id == Account.id) \
        .outerjoin(AccountUser, Account.id == AccountUser.account_id) \
        .filter(
            db.or_(
                DomainUser.user_id == User.id,
                AccountUser.user_id == User.id
            )
    ) \
        .filter(User.id == current_user.id)

    if domain_name:
        info = apikey_query.filter(Domain.name == domain_name).all()
    else:
        info = apikey_query.all()

    return info


@api_bp.errorhandler(400)
def handle_400(err):
    return json.dumps({"msg": "Bad Request"}), 400


@api_bp.errorhandler(401)
def handle_401(err):
    return json.dumps({"msg": "Unauthorized"}), 401


@api_bp.errorhandler(409)
def handle_409(err):
    return json.dumps({"msg": "Conflict"}), 409


@api_bp.errorhandler(500)
def handle_500(err):
    return json.dumps({"msg": "Internal Server Error"}), 500


@api_bp.errorhandler(DomainNotExists)
def handle_domain_not_exists(err):
    return json.dumps(err.to_dict()), err.status_code


@api_bp.errorhandler(DomainAlreadyExists)
def handle_domain_already_exists(err):
    return json.dumps(err.to_dict()), err.status_code


@api_bp.errorhandler(DomainAccessForbidden)
def handle_domain_access_forbidden(err):
    return json.dumps(err.to_dict()), err.status_code


@api_bp.errorhandler(ApiKeyCreateFail)
def handle_apikey_create_fail(err):
    return json.dumps(err.to_dict()), err.status_code


@api_bp.errorhandler(ApiKeyNotUsable)
def handle_apikey_not_usable(err):
    return json.dumps(err.to_dict()), err.status_code


@api_bp.errorhandler(NotEnoughPrivileges)
def handle_not_enough_privileges(err):
    return json.dumps(err.to_dict()), err.status_code


@api_bp.errorhandler(RequestIsNotJSON)
def handle_request_is_not_json(err):
    return json.dumps(err.to_dict()), err.status_code


@api_bp.before_request
@is_json
def before_request():
    # Check site is in maintenance mode
    maintenance = Setting().get('maintenance')
    if maintenance and current_user.is_authenticated and current_user.role.name not in [
            'Administrator', 'Operator'
    ]:
        return make_response(
            jsonify({
                "status": False,
                "msg": "Site is in maintenance mode"
            }))


@api_bp.route('/pdnsadmin/zones', methods=['POST'])
@api_basic_auth
@api_can_create_domain
def api_login_create_zone():
    pdns_api_url = Setting().get('pdns_api_url')
    pdns_api_key = Setting().get('pdns_api_key')
    pdns_version = Setting().get('pdns_version')
    api_uri_with_prefix = utils.pdns_api_extended_uri(pdns_version)
    api_full_uri = api_uri_with_prefix + '/servers/localhost/zones'
    headers = {}
    headers['X-API-Key'] = pdns_api_key

    msg_str = "Sending request to powerdns API {0}"
    msg = msg_str.format(request.get_json(force=True))
    current_app.logger.debug(msg)

    try:
        resp = utils.fetch_remote(urljoin(pdns_api_url, api_full_uri),
                                  method='POST',
                                  data=request.get_json(force=True),
                                  headers=headers,
                                  accept='application/json; q=1',
                                  verify=Setting().get('verify_ssl_connections'))
    except Exception as e:
        current_app.logger.error("Cannot create domain. Error: {}".format(e))
        abort(500)

    if resp.status_code == 201:
        current_app.logger.debug("Request to powerdns API successful")
        data = request.get_json(force=True)

        history = History(msg='Add domain {0}'.format(
            data['name'].rstrip('.')),
                          detail=json.dumps(data),
                          created_by=current_user.username)
        history.add()

        if current_user.role.name not in ['Administrator', 'Operator']:
            current_app.logger.debug(
                "User is ordinary user, assigning created domain")
            domain = Domain(name=data['name'].rstrip('.'))
            domain.update()
            domain.grant_privileges([current_user.id])

        domain = Domain()
        domain.update()

    if resp.status_code == 409:
        raise (DomainAlreadyExists)

    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/pdnsadmin/zones', methods=['GET'])
@api_basic_auth
def api_login_list_zones():
    if current_user.role.name not in ['Administrator', 'Operator']:
        domain_obj_list = get_user_domains()
    else:
        domain_obj_list = Domain.query.all()

    domain_obj_list = [] if domain_obj_list is None else domain_obj_list
    return json.dumps(domain_schema.dump(domain_obj_list)), 200


@api_bp.route('/pdnsadmin/zones/<string:domain_name>', methods=['DELETE'])
@api_basic_auth
@api_can_create_domain
def api_login_delete_zone(domain_name):
    pdns_api_url = Setting().get('pdns_api_url')
    pdns_api_key = Setting().get('pdns_api_key')
    pdns_version = Setting().get('pdns_version')
    api_uri_with_prefix = utils.pdns_api_extended_uri(pdns_version)
    api_full_uri = api_uri_with_prefix + '/servers/localhost/zones'
    api_full_uri += '/' + domain_name
    headers = {}
    headers['X-API-Key'] = pdns_api_key

    domain = Domain.query.filter(Domain.name == domain_name)

    if not domain:
        abort(404)

    if current_user.role.name not in ['Administrator', 'Operator']:
        user_domains_obj_list = get_user_domains()
        user_domains_list = [item.name for item in user_domains_obj_list]

        if domain_name not in user_domains_list:
            raise DomainAccessForbidden()

    msg_str = "Sending request to powerdns API {0}"
    current_app.logger.debug(msg_str.format(domain_name))

    try:
        resp = utils.fetch_remote(urljoin(pdns_api_url, api_full_uri),
                                  method='DELETE',
                                  headers=headers,
                                  accept='application/json; q=1',
                                  verify=Setting().get('verify_ssl_connections'))

        if resp.status_code == 204:
            current_app.logger.debug("Request to powerdns API successful")

            history = History(msg='Delete domain {0}'.format(domain_name),
                              detail='',
                              created_by=current_user.username)
            history.add()

            domain = Domain()
            domain.update()
    except Exception as e:
        current_app.logger.error('Error: {0}'.format(e))
        abort(500)

    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/pdnsadmin/apikeys', methods=['POST'])
@api_basic_auth
def api_generate_apikey():
    data = request.get_json()
    description = None
    role_name = None
    apikey = None
    domain_obj_list = []

    abort(400) if 'domains' not in data else None
    abort(400) if not isinstance(data['domains'], (list, )) else None
    abort(400) if 'role' not in data else None

    description = data['description'] if 'description' in data else None
    role_name = data['role']
    domains = data['domains']

    if role_name == 'User' and len(domains) == 0:
        current_app.logger.error("Apikey with User role must have domains")
        raise ApiKeyNotUsable()
    elif role_name == 'User':
        domain_obj_list = Domain.query.filter(Domain.name.in_(domains)).all()
        if len(domain_obj_list) == 0:
            msg = "One of supplied domains does not exist"
            current_app.logger.error(msg)
            raise DomainNotExists(message=msg)

    if current_user.role.name not in ['Administrator', 'Operator']:
        # domain list of domain api key should be valid for
        # if not any domain error
        # role of api key, user cannot assign role above for api key
        if role_name != 'User':
            msg = "User cannot assign other role than User"
            current_app.logger.error(msg)
            raise NotEnoughPrivileges(message=msg)

        user_domain_obj_list = get_user_domains()

        domain_list = [item.name for item in domain_obj_list]
        user_domain_list = [item.name for item in user_domain_obj_list]

        current_app.logger.debug("Input domain list: {0}".format(domain_list))
        current_app.logger.debug(
            "User domain list: {0}".format(user_domain_list))

        inter = set(domain_list).intersection(set(user_domain_list))

        if not (len(inter) == len(domain_list)):
            msg = "You don't have access to one of domains"
            current_app.logger.error(msg)
            raise DomainAccessForbidden(message=msg)

    apikey = ApiKey(desc=description,
                    role_name=role_name,
                    domains=domain_obj_list)

    try:
        apikey.create()
    except Exception as e:
        current_app.logger.error('Error: {0}'.format(e))
        raise ApiKeyCreateFail(message='Api key create failed')

    return json.dumps(apikey_plain_schema.dump([apikey])), 201


@api_bp.route('/pdnsadmin/apikeys', defaults={'domain_name': None})
@api_bp.route('/pdnsadmin/apikeys/<string:domain_name>')
@api_basic_auth
def api_get_apikeys(domain_name):
    apikeys = []
    current_app.logger.debug("Getting apikeys")

    if current_user.role.name not in ['Administrator', 'Operator']:
        if domain_name:
            msg = "Check if domain {0} exists and is allowed for user.".format(
                domain_name)
            current_app.logger.debug(msg)
            apikeys = get_user_apikeys(domain_name)

            if not apikeys:
                raise DomainAccessForbidden(name=domain_name)

            current_app.logger.debug(apikey_schema.dump(apikeys))
        else:
            msg_str = "Getting all allowed domains for user {0}"
            msg = msg_str.format(current_user.username)
            current_app.logger.debug(msg)

            try:
                apikeys = get_user_apikeys()
                current_app.logger.debug(apikey_schema.dump(apikeys))
            except Exception as e:
                current_app.logger.error('Error: {0}'.format(e))
                abort(500)
    else:
        current_app.logger.debug("Getting all domains for administrative user")
        try:
            apikeys = ApiKey.query.all()
            current_app.logger.debug(apikey_schema.dump(apikeys))
        except Exception as e:
            current_app.logger.error('Error: {0}'.format(e))
            abort(500)

    return json.dumps(apikey_schema.dump(apikeys)), 200


@api_bp.route('/pdnsadmin/apikeys/<int:apikey_id>', methods=['DELETE'])
@api_basic_auth
def api_delete_apikey(apikey_id):
    apikey = ApiKey.query.get(apikey_id)

    if not apikey:
        abort(404)

    current_app.logger.debug(current_user.role.name)

    if current_user.role.name not in ['Administrator', 'Operator']:
        apikeys = get_user_apikeys()
        user_domains_obj_list = current_user.get_domain().all()
        apikey_domains_obj_list = apikey.domains
        user_domains_list = [item.name for item in user_domains_obj_list]
        apikey_domains_list = [item.name for item in apikey_domains_obj_list]
        apikeys_ids = [apikey_item.id for apikey_item in apikeys]

        inter = set(apikey_domains_list).intersection(set(user_domains_list))

        if not (len(inter) == len(apikey_domains_list)):
            msg = "You don't have access to some domains apikey belongs to"
            current_app.logger.error(msg)
            raise DomainAccessForbidden(message=msg)

        if apikey_id not in apikeys_ids:
            raise DomainAccessForbidden()

    try:
        apikey.delete()
    except Exception as e:
        current_app.logger.error('Error: {0}'.format(e))
        abort(500)

    return '', 204


@api_bp.route('/pdnsadmin/apikeys/<int:apikey_id>', methods=['PUT'])
@api_basic_auth
def api_update_apikey(apikey_id):
    # if role different and user is allowed to change it, update
    # if apikey domains are different and user is allowed to handle
    # that domains update domains
    data = request.get_json()
    description = data['description'] if 'description' in data else None
    role_name = data['role'] if 'role' in data else None
    domains = data['domains'] if 'domains' in data else None
    domain_obj_list = None

    apikey = ApiKey.query.get(apikey_id)

    if not apikey:
        abort(404)

    current_app.logger.debug('Updating apikey with id {0}'.format(apikey_id))

    if role_name == 'User' and len(domains) == 0:
        current_app.logger.error("Apikey with User role must have domains")
        raise ApiKeyNotUsable()
    elif role_name == 'User':
        domain_obj_list = Domain.query.filter(Domain.name.in_(domains)).all()
        if len(domain_obj_list) == 0:
            msg = "One of supplied domains does not exist"
            current_app.logger.error(msg)
            raise DomainNotExists(message=msg)

    if current_user.role.name not in ['Administrator', 'Operator']:
        if role_name != 'User':
            msg = "User cannot assign other role than User"
            current_app.logger.error(msg)
            raise NotEnoughPrivileges(message=msg)

        apikeys = get_user_apikeys()
        apikey_domains = [item.name for item in apikey.domains]
        apikeys_ids = [apikey_item.id for apikey_item in apikeys]

        user_domain_obj_list = current_user.get_domain().all()

        domain_list = [item.name for item in domain_obj_list]
        user_domain_list = [item.name for item in user_domain_obj_list]

        current_app.logger.debug("Input domain list: {0}".format(domain_list))
        current_app.logger.debug(
            "User domain list: {0}".format(user_domain_list))

        inter = set(domain_list).intersection(set(user_domain_list))

        if not (len(inter) == len(domain_list)):
            msg = "You don't have access to one of domains"
            current_app.logger.error(msg)
            raise DomainAccessForbidden(message=msg)

        if apikey_id not in apikeys_ids:
            msg = 'Apikey does not belong to domain to which user has access'
            current_app.logger.error(msg)
            raise DomainAccessForbidden()

        if set(domains) == set(apikey_domains):
            current_app.logger.debug(
                "Domains are same, apikey domains won't be updated")
            domains = None

    if role_name == apikey.role:
        current_app.logger.debug("Role is same, apikey role won't be updated")
        role_name = None

    if description == apikey.description:
        msg = "Description is same, apikey description won't be updated"
        current_app.logger.debug(msg)
        description = None

    try:
        apikey = ApiKey.query.get(apikey_id)
        apikey.update(role_name=role_name,
                      domains=domains,
                      description=description)
    except Exception as e:
        current_app.logger.error('Error: {0}'.format(e))
        abort(500)

    return '', 204


@api_bp.route(
    '/servers/<string:server_id>/zones/<string:zone_id>/<path:subpath>',
    methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@apikey_auth
@apikey_can_access_domain
def api_zone_subpath_forward(server_id, zone_id, subpath):
    resp = helper.forward_request()
    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers/<string:server_id>/zones/<string:zone_id>',
              methods=['GET', 'PUT', 'PATCH', 'DELETE'])
@apikey_auth
@apikey_can_access_domain
def api_zone_forward(server_id, zone_id):
    resp = helper.forward_request()
    domain = Domain()
    domain.update()
    status = resp.status_code
    if 200 <= status < 300:
        current_app.logger.debug("Request to powerdns API successful")
        if request.method != 'GET' and request.method != 'DELETE':
            data = request.get_json(force=True)
            for rrset_data in data['rrsets']:
                history = History(msg='{0} zone {1} record of {2}'.format(
                    rrset_data['changetype'].lower(), rrset_data['type'],
                    rrset_data['name'].rstrip('.')),
                                  detail=json.dumps(data),
                                  created_by=g.apikey.description)
                history.add()
        elif request.method == 'DELETE':
            history = History(msg='Deleted zone {0}'.format(domain.name),
                              detail='',
                              created_by=g.apikey.description)
            history.add()
    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers', methods=['GET'])
@apikey_auth
@apikey_is_admin
def api_server_forward():
    resp = helper.forward_request()
    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers/<path:subpath>', methods=['GET', 'PUT'])
@apikey_auth
@apikey_is_admin
def api_server_sub_forward(subpath):
    resp = helper.forward_request()
    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers/<string:server_id>/zones', methods=['POST'])
@apikey_auth
def api_create_zone(server_id):
    resp = helper.forward_request()

    if resp.status_code == 201:
        current_app.logger.debug("Request to powerdns API successful")
        data = request.get_json(force=True)

        history = History(msg='Add domain {0}'.format(
            data['name'].rstrip('.')),
                          detail=json.dumps(data),
                          created_by=g.apikey.description)
        history.add()

        if g.apikey.role.name not in ['Administrator', 'Operator']:
            current_app.logger.debug(
                "Apikey is user key, assigning created domain")
            domain = Domain(name=data['name'].rstrip('.'))
            g.apikey.domains.append(domain)

        domain = Domain()
        domain.update()

    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers/<string:server_id>/zones', methods=['GET'])
@apikey_auth
def api_get_zones(server_id):
    if server_id == 'pdnsadmin':
        if g.apikey.role.name not in ['Administrator', 'Operator']:
            domain_obj_list = g.apikey.domains
        else:
            domain_obj_list = Domain.query.all()
        return json.dumps(domain_schema.dump(domain_obj_list)), 200
    else:
        resp = helper.forward_request()
        return resp.content, resp.status_code, resp.headers.items()


# The endpoint to snychronize Domains in background
@api_bp.route('/sync_domains', methods=['GET'])
@apikey_auth
def sync_domains():
    domain = Domain()
    domain.update()
    return 'Finished synchronization in background', 200
