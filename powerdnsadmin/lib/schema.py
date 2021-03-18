from lima import fields, Schema


class DomainSchema(Schema):
    id = fields.Integer()
    name = fields.String()


class RoleSchema(Schema):
    id = fields.Integer()
    name = fields.String()


class ApiKeySchema(Schema):
    id = fields.Integer()
    role = fields.Embed(schema=RoleSchema)
    domains = fields.Embed(schema=DomainSchema, many=True)
    description = fields.String()
    key = fields.String()


class ApiPlainKeySchema(Schema):
    id = fields.Integer()
    role = fields.Embed(schema=RoleSchema)
    domains = fields.Embed(schema=DomainSchema, many=True)
    description = fields.String()
    plain_key = fields.String()


class AccountSummarySchema(Schema):
    id = fields.Integer()
    name = fields.String()


class UserSchema(Schema):
    id = fields.Integer()
    username = fields.String()
    firstname = fields.String()
    lastname = fields.String()
    email = fields.String()
    role = fields.Embed(schema=RoleSchema)

class UserDetailedSchema(Schema):
    id = fields.Integer()
    username = fields.String()
    firstname = fields.String()
    lastname = fields.String()
    email = fields.String()
    role = fields.Embed(schema=RoleSchema)
    accounts = fields.Embed(schema=AccountSummarySchema)

class AccountSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    description = fields.String()
    contact = fields.String()
    mail = fields.String()
    domains = fields.Embed(schema=DomainSchema, many=True)
