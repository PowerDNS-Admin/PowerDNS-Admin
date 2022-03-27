'''Abstract base classes for fields and schemas.'''


class FieldABC:
    '''Abstract base class for fields.

    Being an instance of :class:`FieldABC` marks a class as a field for
    internal type checks. You can use this class to implement your own type
    checks as well.

    .. note::

        To create new fields, it's a better Idea to subclass
        :class:`lima.fields.Field` directly instead of implementing FieldABC on
        your own.

    '''
    pass


class SchemaABC:
    '''Abstract base class for schemas.

    Being an instance of :class:`SchemaABC` marks a class as a schema for
    internal type checks. You can use this class to implement your own type
    checks as well.

    .. note::

        To create new schemas, it's a *way* better Idea to subclass
        :class:`lima.schema.Schema` directly instead of implementing SchemaABC
        on your own.

    '''
    pass
