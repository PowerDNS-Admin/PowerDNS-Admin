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

    def __init__(self, name=None, message="Domain does not exist"):
        StructuredException.__init__(self)
        self.message = message
        self.name = name


class DomainAccessForbidden(StructuredException):
    status_code = 403

    def __init__(self, name=None, message="Domain access not allowed"):
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

    def __init__(self, name=None, message="Api key must have domains or have \
    administrative role"):
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
