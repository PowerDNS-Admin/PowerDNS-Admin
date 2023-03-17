import json
import secrets
import string
from base64 import b64encode
from urllib.parse import urljoin

from flask import (Blueprint, g, request, abort, current_app, make_response, jsonify)
from flask_login import current_user

from .base import csrf
from ..decorators import (
    api_basic_auth, api_can_create_domain, is_json, apikey_auth,
    apikey_can_create_domain, apikey_can_remove_domain,
    apikey_is_admin, apikey_can_access_domain, apikey_can_configure_dnssec,
    api_role_can, apikey_or_basic_auth,
    callback_if_request_body_contains_key, allowed_record_types, allowed_record_ttl
)
from ..lib import utils, helper
from ..lib.errors import (
    StructuredException,
    DomainNotExists, DomainAlreadyExists, DomainAccessForbidden,
    RequestIsNotJSON, ApiKeyCreateFail, ApiKeyNotUsable, NotEnoughPrivileges,
    AccountCreateFail, AccountUpdateFail, AccountDeleteFail,
    AccountCreateDuplicate, AccountNotExists,
    UserCreateFail, UserCreateDuplicate, UserUpdateFail, UserDeleteFail,
    UserUpdateFailEmail, InvalidAccountNameException
)
from ..lib.schema import (
    ApiKeySchema, DomainSchema, ApiPlainKeySchema, UserSchema, AccountSchema,
    UserDetailedSchema,
)
from ..models import (
    User, Domain, DomainUser, Account, AccountUser, History, Setting, ApiKey,
    Role,
)
from ..models.base import db

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
apilist_bp = Blueprint('apilist', __name__, url_prefix='/')

apikey_schema = ApiKeySchema(many=True)
apikey_single_schema = ApiKeySchema()
domain_schema = DomainSchema(many=True)
apikey_plain_schema = ApiPlainKeySchema()
user_schema = UserSchema(many=True)
user_single_schema = UserSchema()
user_detailed_schema = UserDetailedSchema()
account_schema = AccountSchema(many=True)
account_single_schema = AccountSchema()

def is_custom_header_api():
    custom_header_setting = Setting().get('custom_history_header')
    if custom_header_setting != '' and custom_header_setting in request.headers: 
        return request.headers[custom_header_setting] 
    else: 
        return g.apikey.description 

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


def get_role_id(role_name, role_id=None):
    if role_id:
        if role_name:
            role = Role.query.filter(Role.name == role_name).first()
            if not role or role.id != role_id:
                role_id = None
        else:
            role = Role.query.filter(Role.id == role_id).first()
            if not role:
                role_id = None
    else:
        role = Role.query.filter(Role.name == role_name).first()
        role_id = role.id if role else None
    return role_id


@api_bp.errorhandler(400)
def handle_400(err):
    return jsonify({"msg": "Bad Request"}), 400


@api_bp.errorhandler(401)
def handle_401(err):
    return jsonify({"msg": "Unauthorized"}), 401


@api_bp.errorhandler(409)
def handle_409(err):
    return jsonify({"msg": "Conflict"}), 409


@api_bp.errorhandler(500)
def handle_500(err):
    return jsonify({"msg": "Internal Server Error"}), 500


@api_bp.errorhandler(StructuredException)
def handle_StructuredException(err):
    return jsonify(err.to_dict()), err.status_code


@api_bp.errorhandler(DomainNotExists)
def handle_domain_not_exists(err):
    return jsonify(err.to_dict()), err.status_code


@api_bp.errorhandler(DomainAlreadyExists)
def handle_domain_already_exists(err):
    return jsonify(err.to_dict()), err.status_code


@api_bp.errorhandler(DomainAccessForbidden)
def handle_domain_access_forbidden(err):
    return jsonify(err.to_dict()), err.status_code


@api_bp.errorhandler(ApiKeyCreateFail)
def handle_apikey_create_fail(err):
    return jsonify(err.to_dict()), err.status_code


@api_bp.errorhandler(ApiKeyNotUsable)
def handle_apikey_not_usable(err):
    return jsonify(err.to_dict()), err.status_code


@api_bp.errorhandler(NotEnoughPrivileges)
def handle_not_enough_privileges(err):
    return jsonify(err.to_dict()), err.status_code


@api_bp.errorhandler(RequestIsNotJSON)
def handle_request_is_not_json(err):
    return jsonify(err.to_dict()), err.status_code


@api_bp.before_request
@is_json
def before_request():
    # Check site is in maintenance mode
    maintenance = Setting().get('maintenance')
    if (maintenance and current_user.is_authenticated and current_user.role.name not in ['Administrator', 'Operator']):
        return make_response(
            jsonify({
                "status": False,
                "msg": "Site is in maintenance mode"
            }))


@apilist_bp.route('/api', methods=['GET'])
def index():
    return '[{"url": "/api/v1", "version": 1}]', 200


@api_bp.route('/pdnsadmin/zones', methods=['POST'])
@api_basic_auth
@api_can_create_domain
@csrf.exempt
def api_login_create_zone():
    pdns_api_url = Setting().get('pdns_api_url')
    pdns_api_key = Setting().get('pdns_api_key')
    pdns_version = Setting().get('pdns_version')
    api_uri_with_prefix = utils.pdns_api_extended_uri(pdns_version)
    api_full_uri = api_uri_with_prefix + '/servers/localhost/zones'
    headers = {}
    headers['X-API-Key'] = pdns_api_key
    headers['Content-Type'] = 'application/json'

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
        current_app.logger.error("Cannot create zone. Error: {}".format(e))
        abort(500)

    if resp.status_code == 201:
        current_app.logger.debug("Request to powerdns API successful")
        data = request.get_json(force=True)

        domain = Domain()
        domain.update()
        domain_id = domain.get_id_by_name(data['name'].rstrip('.'))

        history = History(msg='Add zone {0}'.format(
            data['name'].rstrip('.')),
            detail=json.dumps(data),
            created_by=current_user.username,
            domain_id=domain_id)
        history.add()

        if current_user.role.name not in ['Administrator', 'Operator']:
            current_app.logger.debug("User is ordinary user, assigning created zone")
            domain = Domain(name=data['name'].rstrip('.'))
            domain.update()
            domain.grant_privileges([current_user.id])

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
    return jsonify(domain_schema.dump(domain_obj_list)), 200


@api_bp.route('/pdnsadmin/zones/<string:domain_name>', methods=['DELETE'])
@api_basic_auth
@api_can_create_domain
@csrf.exempt
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

            domain = Domain()
            domain_id = domain.get_id_by_name(domain_name)
            domain.update()

            history = History(msg='Delete zone {0}'.format(
                utils.pretty_domain_name(domain_name)),
                detail='',
                created_by=current_user.username,
                domain_id=domain_id)
            history.add()

    except Exception as e:
        current_app.logger.error('Error: {0}'.format(e))
        abort(500)

    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/pdnsadmin/apikeys', methods=['POST'])
@api_basic_auth
@csrf.exempt
def api_generate_apikey():
    data = request.get_json()
    description = None
    role_name = None
    apikey = None
    domain_obj_list = []
    account_obj_list = []

    abort(400) if 'role' not in data else None

    if 'domains' not in data:
        domains = []
    elif not isinstance(data['domains'], (list,)):
        abort(400)
    else:
        domains = [d['name'] if isinstance(d, dict) else d for d in data['domains']]

    if 'accounts' not in data:
        accounts = []
    elif not isinstance(data['accounts'], (list,)):
        abort(400)
    else:
        accounts = [a['name'] if isinstance(a, dict) else a for a in data['accounts']]

    description = data['description'] if 'description' in data else None

    if isinstance(data['role'], str):
        role_name = data['role']
    elif isinstance(data['role'], dict) and 'name' in data['role'].keys():
        role_name = data['role']['name']
    else:
        abort(400)

    if role_name == 'User' and len(domains) == 0 and len(accounts) == 0:
        current_app.logger.error("Apikey with User role must have zones or accounts")
        raise ApiKeyNotUsable()

    if role_name == 'User' and len(domains) > 0:
        domain_obj_list = Domain.query.filter(Domain.name.in_(domains)).all()
        if len(domain_obj_list) == 0:
            msg = "One of supplied zones does not exist"
            current_app.logger.error(msg)
            raise DomainNotExists(message=msg)

    if role_name == 'User' and len(accounts) > 0:
        account_obj_list = Account.query.filter(Account.name.in_(accounts)).all()
        if len(account_obj_list) == 0:
            msg = "One of supplied accounts does not exist"
            current_app.logger.error(msg)
            raise AccountNotExists(message=msg)

    if current_user.role.name not in ['Administrator', 'Operator']:
        # domain list of domain api key should be valid for
        # if not any domain error
        # role of api key, user cannot assign role above for api key
        if role_name != 'User':
            msg = "User cannot assign other role than User"
            current_app.logger.error(msg)
            raise NotEnoughPrivileges(message=msg)

        if len(accounts) > 0:
            msg = "User cannot assign accounts"
            current_app.logger.error(msg)
            raise NotEnoughPrivileges(message=msg)

        user_domain_obj_list = get_user_domains()

        domain_list = [item.name for item in domain_obj_list]
        user_domain_list = [item.name for item in user_domain_obj_list]

        current_app.logger.debug("Input zone list: {0}".format(domain_list))
        current_app.logger.debug("User zone list: {0}".format(user_domain_list))

        inter = set(domain_list).intersection(set(user_domain_list))

        if not (len(inter) == len(domain_list)):
            msg = "You don't have access to one of zones"
            current_app.logger.error(msg)
            raise DomainAccessForbidden(message=msg)

    apikey = ApiKey(desc=description,
                    role_name=role_name,
                    domains=domain_obj_list,
                    accounts=account_obj_list)

    try:
        apikey.create()
    except Exception as e:
        current_app.logger.error('Error: {0}'.format(e))
        raise ApiKeyCreateFail(message='Api key create failed')

    apikey.plain_key = b64encode(apikey.plain_key.encode('utf-8')).decode('utf-8')
    return jsonify(apikey_plain_schema.dump(apikey)), 201


@api_bp.route('/pdnsadmin/apikeys', defaults={'domain_name': None})
@api_bp.route('/pdnsadmin/apikeys/<string:domain_name>')
@api_basic_auth
def api_get_apikeys(domain_name):
    apikeys = []
    current_app.logger.debug("Getting apikeys")

    if current_user.role.name not in ['Administrator', 'Operator']:
        if domain_name:
            msg = "Check if zone {0} exists and is allowed for user.".format(
                domain_name)
            current_app.logger.debug(msg)
            apikeys = get_user_apikeys(domain_name)

            if not apikeys:
                raise DomainAccessForbidden(name=domain_name)

            current_app.logger.debug(apikey_schema.dump(apikeys))
        else:
            msg_str = "Getting all allowed zones for user {0}"
            msg = msg_str.format(current_user.username)
            current_app.logger.debug(msg)

            try:
                apikeys = get_user_apikeys()
                current_app.logger.debug(apikey_schema.dump(apikeys))
            except Exception as e:
                current_app.logger.error('Error: {0}'.format(e))
                abort(500)
    else:
        current_app.logger.debug("Getting all zones for administrative user")
        try:
            apikeys = ApiKey.query.all()
            current_app.logger.debug(apikey_schema.dump(apikeys))
        except Exception as e:
            current_app.logger.error('Error: {0}'.format(e))
            abort(500)

    return jsonify(apikey_schema.dump(apikeys)), 200


@api_bp.route('/pdnsadmin/apikeys/<int:apikey_id>', methods=['GET'])
@api_basic_auth
def api_get_apikey(apikey_id):
    apikey = ApiKey.query.get(apikey_id)

    if not apikey:
        abort(404)

    current_app.logger.debug(current_user.role.name)

    if current_user.role.name not in ['Administrator', 'Operator']:
        if apikey_id not in [a.id for a in get_user_apikeys()]:
            raise DomainAccessForbidden()

    return jsonify(apikey_single_schema.dump(apikey)), 200


@api_bp.route('/pdnsadmin/apikeys/<int:apikey_id>', methods=['DELETE'])
@api_basic_auth
@csrf.exempt
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
            msg = "You don't have access to some zones apikey belongs to"
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
@csrf.exempt
def api_update_apikey(apikey_id):
    # if role different and user is allowed to change it, update
    # if apikey domains are different and user is allowed to handle
    # that domains update domains
    domain_obj_list = None
    account_obj_list = None

    apikey = ApiKey.query.get(apikey_id)

    if not apikey:
        abort(404)

    data = request.get_json()
    description = data['description'] if 'description' in data else None

    if 'role' in data:
        if isinstance(data['role'], str):
            role_name = data['role']
        elif isinstance(data['role'], dict) and 'name' in data['role'].keys():
            role_name = data['role']['name']
        else:
            abort(400)

        target_role = role_name
    else:
        role_name = None
        target_role = apikey.role.name

    if 'domains' not in data:
        domains = None
    elif not isinstance(data['domains'], (list,)):
        abort(400)
    else:
        domains = [d['name'] if isinstance(d, dict) else d for d in data['domains']]

    if 'accounts' not in data:
        accounts = None
    elif not isinstance(data['accounts'], (list,)):
        abort(400)
    else:
        accounts = [a['name'] if isinstance(a, dict) else a for a in data['accounts']]

    current_app.logger.debug('Updating apikey with id {0}'.format(apikey_id))

    if target_role == 'User':
        current_domains = [item.name for item in apikey.domains]
        current_accounts = [item.name for item in apikey.accounts]

        if domains is not None:
            domain_obj_list = Domain.query.filter(Domain.name.in_(domains)).all()
            if len(domain_obj_list) != len(domains):
                msg = "One of supplied zones does not exist"
                current_app.logger.error(msg)
                raise DomainNotExists(message=msg)

            target_domains = domains
        else:
            target_domains = current_domains

        if accounts is not None:
            account_obj_list = Account.query.filter(Account.name.in_(accounts)).all()
            if len(account_obj_list) != len(accounts):
                msg = "One of supplied accounts does not exist"
                current_app.logger.error(msg)
                raise AccountNotExists(message=msg)

            target_accounts = accounts
        else:
            target_accounts = current_accounts

        if len(target_domains) == 0 and len(target_accounts) == 0:
            current_app.logger.error("Apikey with User role must have zones or accounts")
            raise ApiKeyNotUsable()

        if domains is not None and set(domains) == set(current_domains):
            current_app.logger.debug(
                "Zones are the same, apikey zones won't be updated")
            domains = None

        if accounts is not None and set(accounts) == set(current_accounts):
            current_app.logger.debug(
                "Accounts are the same, apikey accounts won't be updated")
            accounts = None

    if current_user.role.name not in ['Administrator', 'Operator']:
        if role_name != 'User':
            msg = "User cannot assign other role than User"
            current_app.logger.error(msg)
            raise NotEnoughPrivileges(message=msg)

        if len(accounts) > 0:
            msg = "User cannot assign accounts"
            current_app.logger.error(msg)
            raise NotEnoughPrivileges(message=msg)

        apikeys = get_user_apikeys()
        apikeys_ids = [apikey_item.id for apikey_item in apikeys]

        user_domain_obj_list = current_user.get_domain().all()

        domain_list = [item.name for item in domain_obj_list]
        user_domain_list = [item.name for item in user_domain_obj_list]

        current_app.logger.debug("Input zone list: {0}".format(domain_list))
        current_app.logger.debug(
            "User zone list: {0}".format(user_domain_list))

        inter = set(domain_list).intersection(set(user_domain_list))

        if not (len(inter) == len(domain_list)):
            msg = "You don't have access to one of zones"
            current_app.logger.error(msg)
            raise DomainAccessForbidden(message=msg)

        if apikey_id not in apikeys_ids:
            msg = 'Apikey does not belong to zone to which user has access'
            current_app.logger.error(msg)
            raise DomainAccessForbidden()

    if role_name == apikey.role.name:
        current_app.logger.debug("Role is same, apikey role won't be updated")
        role_name = None

    if description == apikey.description:
        msg = "Description is same, apikey description won't be updated"
        current_app.logger.debug(msg)
        description = None

    if target_role != "User":
        domains, accounts = [], []

    try:
        apikey.update(role_name=role_name,
                      domains=domains,
                      accounts=accounts,
                      description=description)
    except Exception as e:
        current_app.logger.error('Error: {0}'.format(e))
        abort(500)

    return '', 204


@api_bp.route('/pdnsadmin/users', defaults={'username': None})
@api_bp.route('/pdnsadmin/users/<string:username>')
@api_basic_auth
@api_role_can('list users', allow_self=True)
def api_list_users(username=None):
    if username is None:
        user_list = [] or User.query.all()
        return jsonify(user_schema.dump(user_list)), 200
    else:
        user = User.query.filter(User.username == username).first()
        if user is None:
            abort(404)
        return jsonify(user_detailed_schema.dump(user)), 200


@api_bp.route('/pdnsadmin/users', methods=['POST'])
@api_basic_auth
@api_role_can('create users', allow_self=True)
@csrf.exempt
def api_create_user():
    """
    Create new user
    """
    data = request.get_json()
    username = data['username'] if 'username' in data else None
    password = data['password'] if 'password' in data else None
    plain_text_password = (
        data['plain_text_password']
        if 'plain_text_password' in data
        else None
    )
    firstname = data['firstname'] if 'firstname' in data else None
    lastname = data['lastname'] if 'lastname' in data else None
    email = data['email'] if 'email' in data else None
    otp_secret = data['otp_secret'] if 'otp_secret' in data else None
    confirmed = data['confirmed'] if 'confirmed' in data else None
    role_name = data['role_name'] if 'role_name' in data else None
    role_id = data['role_id'] if 'role_id' in data else None

    # Create user
    if not username:
        current_app.logger.debug('Invalid username {}'.format(username))
        abort(400)
    if not confirmed:
        confirmed = False
    elif confirmed is not True:
        current_app.logger.debug('Invalid confirmed {}'.format(confirmed))
        abort(400)

    if not plain_text_password and not password:
        plain_text_password = ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(15))
    if not role_name and not role_id:
        role_name = 'User'
    role_id = get_role_id(role_name, role_id)
    if not role_id:
        current_app.logger.debug(
            'Invalid role {}/{}'.format(role_name, role_id))
        abort(400)

    user = User(
        username=username,
        password=password,
        plain_text_password=plain_text_password,
        firstname=firstname,
        lastname=lastname,
        role_id=role_id,
        email=email,
        otp_secret=otp_secret,
        confirmed=confirmed,
    )
    try:
        result = user.create_local_user()
    except Exception as e:
        current_app.logger.error('Create user ({}, {}) error: {}'.format(
            username, email, e))
        raise UserCreateFail(message='User create failed')
    if not result['status']:
        current_app.logger.warning('Create user ({}, {}) error: {}'.format(
            username, email, result['msg']))
        raise UserCreateDuplicate(message=result['msg'])

    history = History(msg='Created user {0}'.format(user.username),
                      created_by=current_user.username)
    history.add()
    return jsonify(user_single_schema.dump(user)), 201


@api_bp.route('/pdnsadmin/users/<int:user_id>', methods=['PUT'])
@api_basic_auth
@api_role_can('update users', allow_self=True)
@csrf.exempt
def api_update_user(user_id):
    """
    Update existing user
    """
    data = request.get_json()
    username = data['username'] if 'username' in data else None
    password = data['password'] if 'password' in data else None
    plain_text_password = (
        data['plain_text_password']
        if 'plain_text_password' in data
        else None
    )
    firstname = data['firstname'] if 'firstname' in data else None
    lastname = data['lastname'] if 'lastname' in data else None
    email = data['email'] if 'email' in data else None
    otp_secret = data['otp_secret'] if 'otp_secret' in data else None
    confirmed = data['confirmed'] if 'confirmed' in data else None
    role_name = data['role_name'] if 'role_name' in data else None
    role_id = data['role_id'] if 'role_id' in data else None

    user = User.query.get(user_id)
    if not user:
        current_app.logger.debug("User not found for id {}".format(user_id))
        abort(404)
    if username:
        if username != user.username:
            current_app.logger.error(
                'Cannot change username for {}'.format(user.username)
            )
            abort(400)
    if password is not None:
        user.password = password
    user.plain_text_password = plain_text_password or ''
    if firstname is not None:
        user.firstname = firstname
    if lastname is not None:
        user.lastname = lastname
    if email is not None:
        user.email = email
    if otp_secret is not None:
        user.otp_secret = otp_secret
    if confirmed is not None:
        user.confirmed = confirmed
    if role_name is not None:
        user.role_id = get_role_id(role_name, role_id)
    elif role_id is not None:
        user.role_id = role_id
    current_app.logger.debug(
        "Updating user {} ({})".format(user_id, user.username))
    try:
        result = user.update_local_user()
    except Exception as e:
        current_app.logger.error('Create user ({}, {}) error: {}'.format(
            username, email, e))
        raise UserUpdateFail(message='User update failed')
    if not result['status']:
        current_app.logger.warning('Update user ({}, {}) error: {}'.format(
            username, email, result['msg']))
        if result['msg'].startswith('New email'):
            raise UserUpdateFailEmail(message=result['msg'])
        else:
            raise UserCreateFail(message=result['msg'])

    history = History(msg='Updated user {0}'.format(user.username),
                      created_by=current_user.username)
    history.add()
    return '', 204


@api_bp.route('/pdnsadmin/users/<int:user_id>', methods=['DELETE'])
@api_basic_auth
@api_role_can('delete users')
@csrf.exempt
def api_delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        current_app.logger.debug("User not found for id {}".format(user_id))
        abort(404)
    if user.id == current_user.id:
        current_app.logger.debug("Cannot delete self (id {})".format(user_id))
        msg = "Cannot delete self"
        raise UserDeleteFail(message=msg)

    # Remove account associations first
    user_accounts = Account.query.join(AccountUser).join(
        User).filter(AccountUser.user_id == user.id,
                     AccountUser.account_id == Account.id).all()
    for uc in user_accounts:
        uc.revoke_privileges_by_id(user.id)

    # Then delete the user
    result = user.delete()
    if not result:
        raise UserDeleteFail("Failed to delete user {}".format(
            user.username))

    history = History(msg='Delete user {0}'.format(user.username),
                      created_by=current_user.username)
    history.add()
    return '', 204


@api_bp.route('/pdnsadmin/accounts', defaults={'account_name': None})
@api_bp.route('/pdnsadmin/accounts/<string:account_name>')
@api_basic_auth
@api_role_can('list accounts')
def api_list_accounts(account_name):
    if current_user.role.name not in ['Administrator', 'Operator']:
        msg = "{} role cannot list accounts".format(current_user.role.name)
        raise NotEnoughPrivileges(message=msg)
    else:
        if account_name is None:
            account_list = [] or Account.query.all()
            return jsonify(account_schema.dump(account_list)), 200
        else:
            account = Account.query.filter(
                Account.name == account_name).first()
            if account is None:
                abort(404)
            return jsonify(account_single_schema.dump(account)), 200


@api_bp.route('/pdnsadmin/accounts', methods=['POST'])
@api_basic_auth
@csrf.exempt
def api_create_account():
    if current_user.role.name not in ['Administrator', 'Operator']:
        msg = "{} role cannot create accounts".format(current_user.role.name)
        raise NotEnoughPrivileges(message=msg)
    data = request.get_json()
    name = data['name'] if 'name' in data else None
    description = data['description'] if 'description' in data else None
    contact = data['contact'] if 'contact' in data else None
    mail = data['mail'] if 'mail' in data else None
    if not name:
        current_app.logger.debug("Account creation failed: name missing")
        raise InvalidAccountNameException(message="Account name missing")

    sanitized_name = Account.sanitize_name(name)
    account_exists = Account.query.filter(Account.name == sanitized_name).all()

    if len(account_exists) > 0:
        msg = ("Requested Account {} would be translated to {}"
               " which already exists").format(name, sanitized_name)
        current_app.logger.debug(msg)
        raise AccountCreateDuplicate(message=msg)

    account = Account(name=name,
                      description=description,
                      contact=contact,
                      mail=mail)

    try:
        result = account.create_account()
    except Exception as e:
        current_app.logger.error('Error: {0}'.format(e))
        raise AccountCreateFail(message='Account create failed')
    if not result['status']:
        raise AccountCreateFail(message=result['msg'])

    history = History(msg='Create account {0}'.format(account.name),
                      created_by=current_user.username)
    history.add()
    return jsonify(account_single_schema.dump(account)), 201


@api_bp.route('/pdnsadmin/accounts/<int:account_id>', methods=['PUT'])
@api_basic_auth
@api_role_can('update accounts')
@csrf.exempt
def api_update_account(account_id):
    data = request.get_json()
    name = data['name'] if 'name' in data else None
    description = data['description'] if 'description' in data else None
    contact = data['contact'] if 'contact' in data else None
    mail = data['mail'] if 'mail' in data else None

    account = Account.query.get(account_id)

    if not account:
        abort(404)

    if name and Account.sanitize_name(name) != account.name:
        msg = "Account name is immutable"
        raise AccountUpdateFail(message=msg)

    if current_user.role.name not in ['Administrator', 'Operator']:
        msg = "User role update accounts"
        raise NotEnoughPrivileges(message=msg)

    if description is not None:
        account.description = description
    if contact is not None:
        account.contact = contact
    if mail is not None:
        account.mail = mail

    current_app.logger.debug(
        "Updating account {} ({})".format(account_id, account.name))
    result = account.update_account()
    if not result['status']:
        raise AccountUpdateFail(message=result['msg'])
    history = History(msg='Update account {0}'.format(account.name),
                      created_by=current_user.username)
    history.add()
    return '', 204


@api_bp.route('/pdnsadmin/accounts/<int:account_id>', methods=['DELETE'])
@api_basic_auth
@api_role_can('delete accounts')
@csrf.exempt
def api_delete_account(account_id):
    account_list = [] or Account.query.filter(Account.id == account_id).all()
    if len(account_list) == 1:
        account = account_list[0]
    else:
        abort(404)
    current_app.logger.debug(f'Deleting Account {account.name}')

    # Remove account association from domains first
    if len(account.domains) > 0:
        for domain in account.domains:
            current_app.logger.info(f"Disassociating zone {domain.name} with {account.name}")
            Domain(name=domain.name).assoc_account(None, update=False)
        current_app.logger.info("Syncing all zones")
        Domain().update()

    current_app.logger.debug(
        "Deleting account {} ({})".format(account_id, account.name))
    result = account.delete_account()
    if not result:
        raise AccountDeleteFail(message=result['msg'])

    history = History(msg='Delete account {0}'.format(account.name),
                      created_by=current_user.username)
    history.add()
    return '', 204


@api_bp.route('/pdnsadmin/accounts/users/<int:account_id>', methods=['GET'])
@api_bp.route('/pdnsadmin/accounts/<int:account_id>/users', methods=['GET'])
@api_basic_auth
@api_role_can('list account users')
def api_list_account_users(account_id):
    account = Account.query.get(account_id)
    if not account:
        abort(404)
    user_list = User.query.join(AccountUser).filter(
        AccountUser.account_id == account_id).all()
    return jsonify(user_schema.dump(user_list)), 200


@api_bp.route(
    '/pdnsadmin/accounts/users/<int:account_id>/<int:user_id>',
    methods=['PUT'])
@api_bp.route(
    '/pdnsadmin/accounts/<int:account_id>/users/<int:user_id>',
    methods=['PUT'])
@api_basic_auth
@api_role_can('add user to account')
@csrf.exempt
def api_add_account_user(account_id, user_id):
    account = Account.query.get(account_id)
    if not account:
        abort(404)
    user = User.query.get(user_id)
    if not user:
        abort(404)
    if not account.add_user(user):
        raise AccountUpdateFail("Cannot add user {} to {}".format(
            user.username, account.name))

    history = History(
        msg='Add {} user privileges on {}'.format(
            user.username, account.name),
        created_by=current_user.username)
    history.add()
    return '', 204


@api_bp.route(
    '/pdnsadmin/accounts/users/<int:account_id>/<int:user_id>',
    methods=['DELETE'])
@api_bp.route(
    '/pdnsadmin/accounts/<int:account_id>/users/<int:user_id>',
    methods=['DELETE'])
@api_basic_auth
@api_role_can('remove user from account')
@csrf.exempt
def api_remove_account_user(account_id, user_id):
    account = Account.query.get(account_id)
    if not account:
        abort(404)
    user = User.query.get(user_id)
    if not user:
        abort(404)
    user_list = User.query.join(AccountUser).filter(
        AccountUser.account_id == account_id,
        AccountUser.user_id == user_id,
    ).all()
    if not user_list:
        abort(404)
    if not account.remove_user(user):
        raise AccountUpdateFail("Cannot remove user {} from {}".format(
            user.username, account.name))

    history = History(
        msg='Revoke {} user privileges on {}'.format(
            user.username, account.name),
        created_by=current_user.username)
    history.add()
    return '', 204


@api_bp.route(
    '/servers/<string:server_id>/zones/<string:zone_id>/cryptokeys',
    methods=['GET', 'POST'])
@apikey_auth
@apikey_can_access_domain
@apikey_can_configure_dnssec(http_methods=['POST'])
@csrf.exempt
def api_zone_cryptokeys(server_id, zone_id):
    resp = helper.forward_request()
    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route(
    '/servers/<string:server_id>/zones/<string:zone_id>/cryptokeys/<string:cryptokey_id>',
    methods=['GET', 'PUT', 'DELETE'])
@apikey_auth
@apikey_can_access_domain
@apikey_can_configure_dnssec()
@csrf.exempt
def api_zone_cryptokey(server_id, zone_id, cryptokey_id):
    resp = helper.forward_request()
    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route(
    '/servers/<string:server_id>/zones/<string:zone_id>/<path:subpath>',
    methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@apikey_auth
@apikey_can_access_domain
@csrf.exempt
def api_zone_subpath_forward(server_id, zone_id, subpath):
    resp = helper.forward_request()
    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers/<string:server_id>/zones/<string:zone_id>',
              methods=['GET', 'PUT', 'PATCH', 'DELETE'])
@apikey_auth
@allowed_record_types
@allowed_record_ttl
@apikey_can_access_domain
@apikey_can_remove_domain(http_methods=['DELETE'])
@callback_if_request_body_contains_key(apikey_can_configure_dnssec()(),
                                       http_methods=['PUT'],
                                       keys=['dnssec', 'nsec3param'])
@csrf.exempt
def api_zone_forward(server_id, zone_id):
    resp = helper.forward_request()
    if not Setting().get('bg_domain_updates'):
        domain = Domain()
        domain.update()
    status = resp.status_code
    created_by_value=is_custom_header_api()
    if 200 <= status < 300:
        current_app.logger.debug("Request to powerdns API successful")
        if Setting().get('enable_api_rr_history'):
            if request.method in ['POST', 'PATCH']:
                data = request.get_json(force=True)
                history = History(
                    msg='Apply record changes to zone {0}'.format(zone_id.rstrip('.')),
                    detail = json.dumps({
                        'domain': zone_id.rstrip('.'),
                        'add_rrsets': list(filter(lambda r: r['changetype'] == "REPLACE", data['rrsets'])),
                        'del_rrsets': list(filter(lambda r: r['changetype'] == "DELETE", data['rrsets']))
                    }),
                    created_by=created_by_value,
                    domain_id=Domain().get_id_by_name(zone_id.rstrip('.')))
                history.add()
            elif request.method == 'DELETE':
                history = History(msg='Deleted zone {0}'.format(zone_id.rstrip('.')),
                                  detail='',
                                  created_by=created_by_value,
                                  domain_id=Domain().get_id_by_name(zone_id.rstrip('.')))
                history.add()
            elif request.method != 'GET':
                history = History(msg='Updated zone {0}'.format(zone_id.rstrip('.')),
                                  detail='',
                                  created_by=created_by_value,
                                  domain_id=Domain().get_id_by_name(zone_id.rstrip('.')))
                history.add()
    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers/<path:subpath>', methods=['GET', 'PUT'])
@apikey_auth
@apikey_is_admin
@csrf.exempt
def api_server_sub_forward(subpath):
    resp = helper.forward_request()
    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers/<string:server_id>/zones', methods=['POST'])
@apikey_auth
@apikey_can_create_domain
@csrf.exempt
def api_create_zone(server_id):
    resp = helper.forward_request()

    if resp.status_code == 201:
        current_app.logger.debug("Request to powerdns API successful")
        created_by_value=is_custom_header_api()
        data = request.get_json(force=True)

        if g.apikey.role.name not in ['Administrator', 'Operator']:
            current_app.logger.debug(
                "Apikey is user key, assigning created zone")
            domain = Domain(name=data['name'].rstrip('.'))
            g.apikey.domains.append(domain)

        domain = Domain()
        domain.update()

        history = History(msg='Add zone {0}'.format(
            data['name'].rstrip('.')),
            detail=json.dumps(data),
            created_by=created_by_value,
            domain_id=domain.get_id_by_name(data['name'].rstrip('.')))
        history.add()

    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers/<string:server_id>/zones', methods=['GET'])
@apikey_auth
def api_get_zones(server_id):
    if server_id == 'pdnsadmin':
        if g.apikey.role.name not in ['Administrator', 'Operator']:
            domain_obj_list = g.apikey.domains
        else:
            domain_obj_list = Domain.query.all()
        return jsonify(domain_schema.dump(domain_obj_list)), 200
    else:
        resp = helper.forward_request()
        if (g.apikey.role.name not in ['Administrator', 'Operator'] and resp.status_code == 200):
            domain_list = [d['name']
                           for d in domain_schema.dump(g.apikey.domains)]

            accounts_domains = [d.name for a in g.apikey.accounts for d in a.domains]
            allowed_domains = set(domain_list + accounts_domains)
            current_app.logger.debug("Account zones: {}".format('/'.join(accounts_domains)))
            content = json.dumps([i for i in json.loads(resp.content)
                                  if i['name'].rstrip('.') in allowed_domains])
            return content, resp.status_code, resp.headers.items()
        else:
            return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers', methods=['GET'])
@apikey_auth
def api_server_forward():
    resp = helper.forward_request()
    return resp.content, resp.status_code, resp.headers.items()


@api_bp.route('/servers/<string:server_id>', methods=['GET'])
@apikey_auth
def api_server_config_forward(server_id):
    resp = helper.forward_request()
    return resp.content, resp.status_code, resp.headers.items()


# The endpoint to synchronize Domains in background
@api_bp.route('/sync_domains', methods=['GET'])
@apikey_or_basic_auth
def sync_domains():
    domain = Domain()
    domain.update()
    return 'Finished synchronization in background', 200


@api_bp.route('/health', methods=['GET'])
@apikey_auth
def health():
    domain = Domain()
    domain_to_query = domain.query.first()

    if not domain_to_query:
        current_app.logger.error("No zone found to query a health check")
        return make_response("Unknown", 503)

    try:
        domain.get_domain_info(domain_to_query.name)
    except Exception as e:
        current_app.logger.error(
            "Health Check - Failed to query authoritative server for zone {}".format(domain_to_query.name))
        return make_response("Down", 503)

    return make_response("Up", 200)
