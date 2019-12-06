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
