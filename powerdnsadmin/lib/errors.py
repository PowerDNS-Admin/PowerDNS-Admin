class StructuredException(Exception):
    status_code = 0

    def __init__(self, name=None, message="You want override this error!"):
        Exception.__init__(self)
        self.message = message
        self.name = name

    def to_dict(self):
        rv = dict()
        msg = ''
        if self.name:
            msg = '{0} {1}'.format(self.message, self.name)
        else:
            msg = self.message

        rv['msg'] = msg
        return rv


class DomainNotExists(StructuredException):
    status_code = 404

    def __init__(self, name=None, message="Zone does not exist"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class DomainAlreadyExists(StructuredException):
    status_code = 409

    def __init__(self, name=None, message="Zone already exists"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class DomainAccessForbidden(StructuredException):
    status_code = 403

    def __init__(self, name=None, message="Zone access not allowed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name

class DomainOverrideForbidden(StructuredException):
    status_code = 409

    def __init__(self, name=None, message="Zone override of record not allowed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name

class ApiKeyCreateFail(StructuredException):
    status_code = 500

    def __init__(self, name=None, message="Creation of api key failed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class ApiKeyNotUsable(StructuredException):
    status_code = 400

    def __init__(
        self,
        name=None,
        message=("Api key must have zones or accounts"
                 " or an administrative role")):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class NotEnoughPrivileges(StructuredException):
    status_code = 401

    def __init__(self, name=None, message="Not enough privileges"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class RequestIsNotJSON(StructuredException):
    status_code = 400

    def __init__(self, name=None, message="Request is not json"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class AccountCreateFail(StructuredException):
    status_code = 500

    def __init__(self, name=None, message="Creation of account failed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class AccountCreateDuplicate(StructuredException):
    status_code = 409

    def __init__(self, name=None, message="Creation of account failed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class AccountUpdateFail(StructuredException):
    status_code = 500

    def __init__(self, name=None, message="Update of account failed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class AccountDeleteFail(StructuredException):
    status_code = 500

    def __init__(self, name=None, message="Delete of account failed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class AccountNotExists(StructuredException):
    status_code = 404

    def __init__(self, name=None, message="Account does not exist"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name

class InvalidAccountNameException(StructuredException):
    status_code = 400

    def __init__(self, name=None, message="The account name is invalid"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name

class UserCreateFail(StructuredException):
    status_code = 500

    def __init__(self, name=None, message="Creation of user failed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name

class UserCreateDuplicate(StructuredException):
    status_code = 409

    def __init__(self, name=None, message="Creation of user failed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name

class UserUpdateFail(StructuredException):
    status_code = 500

    def __init__(self, name=None, message="Update of user failed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name

class UserUpdateFailEmail(StructuredException):
    status_code = 409

    def __init__(self, name=None, message="Update of user failed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name

class UserDeleteFail(StructuredException):
    status_code = 500

    def __init__(self, name=None, message="Delete of user failed"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name

class RecordTypeNotAllowed(StructuredException):
    status_code = 400

    def __init__(self, name=None, message="Record type not allowed or does not present"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name

class RecordTTLNotAllowed(StructuredException):
    status_code = 400

    def __init__(self, name=None, message="Record TTL not allowed or does not present"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name
