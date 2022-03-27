'''Field classes and related code.'''

import datetime
import decimal

from lima import abc
from lima import registry
from lima import util


class Field(abc.FieldABC):
    '''Base class for fields.

    Args:
        attr: The optional name of the corresponding attribute.

        key: The optional name of the corresponding key.

        get: An optional getter function accepting an object as its only
            parameter and returning the field value.

        val: An optional constant value for the field.

    .. versionadded:: 0.3
        The ``val`` parameter.

    :attr:`attr`, :attr:`key`, :attr:`get` and :attr:`val` are mutually
    exclusive.

    When a :class:`Field` object ends up with two or more of the attributes
    :attr:`attr`, :attr:`key`, :attr:`get` and :attr:`val` regardless (because
    one or more of them are implemented at the class level for example),
    :meth:`lima.schema.Schema.dump` tries to get the field's value in the
    following order: :attr:`val` :attr:`get` :attr:`key` and finally
    :attr:`attr`.

    If a :class:`Field` object ends up with none of these attributes (not at
    the instance and not at the class level), :meth:`lima.schema.Schema.dump`
    tries to get the field's value by looking for an attribute of the same name
    as the field has within the corresponding :class:`lima.schema.Schema`
    instance.

    '''
    def __init__(self, *, attr=None, key=None, get=None, val=None):
        if sum(v is not None for v in (attr, key, get, val)) > 1:
            raise ValueError('attr, key, get and val are mutually exclusive.')

        if attr is not None:
            if not isinstance(attr, str) or not str.isidentifier(attr):
                msg = 'attr is not a valid Python identifier: {}'.format(attr)
                raise ValueError(msg)
            self.attr = attr
        elif key is not None:
            self.key = key
        elif get is not None:
            if not callable(get):
                raise ValueError('get is not callable.')
            self.get = get
        elif val is not None:
            self.val = val


class Boolean(Field):
    '''A boolean field.

    currently this class has no additional functionality compared to
    :class:`Field`. Nevertheless it should be used over :class:`Field` when
    referencing boolean values as an indicator for a field's type and to keep
    code future-proof.

    '''
    pass


class Decimal(Field):
    '''A decimal field.

    Decimal values get serialized as strings, this way, no precision is lost.

    '''
    @staticmethod
    def pack(val):
        return str(val) if val is not None else None


class Float(Field):
    '''A float field.

    currently this class has no additional functionality compared to
    :class:`Field`. Nevertheless it should be used over :class:`Field` when
    referencing float values as an indicator for a field's type and to keep
    code future-proof.

    '''
    pass


class Integer(Field):
    '''An integer field.

    currently this class has no additional functionality compared to
    :class:`Field`. Nevertheless it should be used over :class:`Field` when
    referencing integer values as an indicator for a field's type and to keep
    code future-proof.

    '''
    pass


class String(Field):
    '''A string field.

    currently this class has no additional functionality compared to
    :class:`Field`. Nevertheless it should be used over :class:`Field` when
    referencing string values as an indicator for a field's type and to keep
    code future-proof.

    '''
    pass


class Date(Field):
    '''A date field.

    '''
    @staticmethod
    def pack(val):
        '''Return a string representation of ``val``.

        Args:
            val: The :class:`datetime.date` object to convert.

        Returns:
            The ISO 8601-representation of ``val`` (``YYYY-MM-DD``).
        '''
        return val.isoformat() if val is not None else None


class DateTime(Field):
    '''A DateTime field.

    '''
    @staticmethod
    def pack(val):
        '''Return a string representation of ``val``.

        Args:
            val: The :class:`datetime.datetime` object to convert.

        Returns:
            The ISO 8601-representation of ``val``
            (``YYYY-MM-DD%HH:MM:SS.mmmmmm+HH:MM`` for
            :class:`datetime.datetime` objects with Timezone
            information and microsecond precision).

        '''
        return val.isoformat() if val is not None else None


class _LinkedObjectField(Field):
    '''A base class for fields that represent linked objects.

    This is to be considered an abstract class. Concrete implementations will
    have to define their own :meth:`pack` methods, utilizing the associated
    schema of the linked object.

    Args:
        schema: The schema of the linked object. This can be specified via a
            schema *object,* a schema *class* or the qualified *name* of a
            schema class (for when the named schema has not been defined at the
            time of instantiation. If two or more schema classes with the same
            name exist in different modules, the schema class name has to be
            fully module-qualified (see the :ref:`entry on class names
            <on_class_names>` for clarification of these concepts). Schemas
            defined within a local namespace can not be referenced by name.

        attr: See :class:`Field`.

        get: See :class:`Field`.

        key: See :class:`Field`.

        val: See :class:`Field`.

        kwargs: Optional keyword arguments to pass to the :class:`Schema`'s
            constructor when the time has come to instance it. Must be empty if
            ``schema`` is a :class:`lima.schema.Schema` object.

    The schema of the linked object associated with a field of this type will
    be lazily evaluated the first time it is needed. This means that incorrect
    arguments might produce errors at a time after the field's instantiation.

    '''
    def __init__(self,
                 *,
                 schema,
                 attr=None,
                 key=None,
                 get=None,
                 val=None,
                 **kwargs):
        super().__init__(attr=attr, key=key, get=get, val=val)

        # those will be evaluated later on (in _schema_inst)
        self._schema_arg = schema
        self._schema_kwargs = kwargs

    @util.reify
    def _schema_inst(self):
        '''Determine and return the associated Schema instance (reified).

        If no associated Schema instance exists at call time (because only a
        Schema class name was supplied to the constructor), find the Schema
        class in the global registry and instantiate it.

        Returns:
            A schema instance for the linked object.

        Raises:
            ValueError: If ``kwargs`` were specified to the field constructor
                even if a :class:`lima.schema.Schema` *instance* was provided
                as the ``schema`` arg.

            TypeError: If the ``schema`` arg provided to the field constructor
                has the wrong type.

        '''
        with util.exception_context('Lazy evaluation of schema instance'):

            # those were supplied to field constructor
            schema = self._schema_arg
            kwargs = self._schema_kwargs

            # in case schema is a Schema object
            if isinstance(schema, abc.SchemaABC):
                if kwargs:
                    msg = ('No additional keyword args must be '
                           'supplied to field constructor if '
                           'schema already is a Schema object.')
                    raise ValueError(msg)
                return schema

            # in case schema is a schema class
            elif (isinstance(schema, type) and
                  issubclass(schema, abc.SchemaABC)):
                return schema(**kwargs)

            # in case schema is a string
            elif isinstance(schema, str):
                cls = registry.global_registry.get(schema)
                return cls(**kwargs)

            # otherwise fail
            msg = 'schema arg supplied to constructor has illegal type ({})'
            raise TypeError(msg.format(type(schema)))

    def pack(self, val):
        raise NotImplementedError


class Embed(_LinkedObjectField):
    '''A Field to embed linked objects.

    Args:
        schema: The schema of the linked object. This can be specified via a
            schema *object,* a schema *class* or the qualified *name* of a
            schema class (for when the named schema has not been defined at the
            time of instantiation. If two or more schema classes with the same
            name exist in different modules, the schema class name has to be
            fully module-qualified (see the :ref:`entry on class names
            <on_class_names>` for clarification of these concepts). Schemas
            defined within a local namespace can not be referenced by name.

        attr: See :class:`Field`.

        key: See :class:`Field`.

        get: See :class:`Field`.

        val: See :class:`Field`.

        kwargs: Optional keyword arguments to pass to the :class:`Schema`'s
            constructor when the time has come to instance it. Must be empty if
            ``schema`` is a :class:`lima.schema.Schema` object.

    Examples: ::

        # refer to PersonSchema class
        author = Embed(schema=PersonSchema)

        # refer to PersonSchema class with additional params
        artists = Embed(schema=PersonSchema, exclude='email', many=True)

        # refer to PersonSchema object
        author = Embed(schema=PersonSchema())

        # refer to PersonSchema object with additional params
        # (note that Embed() itself gets no kwargs)
        artists = Embed(schema=PersonSchema(exclude='email', many=true))

        # refer to PersonSchema per name
        author = Embed(schema='PersonSchema')

        # refer to PersonSchema per name with additional params
        author = Embed(schema='PersonSchema', exclude='email', many=True)

        # refer to PersonSchema per module-qualified name
        # (in case of ambiguity)
        author = Embed(schema='project.persons.PersonSchema')

        # specify attr name as well
        user = Embed(attr='login_user', schema=PersonSchema)

    '''
    @util.reify
    def _pack_func(self):
        '''Return the associated schema's dump fields *function* (reified).'''
        return self._schema_inst._dump_fields

    def pack(self, val):
        '''Return the marshalled representation of val.

        Args:
            val: The linked object to embed.

        Returns:
            The marshalled representation of ``val`` (or ``None`` if ``val`` is
            ``None``).

        Note that the return value is determined using an (internal) dump
        fields *function* of the associated schema object. This means that
        overriding the associated schema's :meth:`~lima.schema.Schema.dump`
        *method* has no effect on the result of this method.

        '''
        return self._pack_func(val) if val is not None else None


class Reference(_LinkedObjectField):
    '''A Field to reference linked objects.

    Args:

        schema: A schema for the linked object (see :class:`Embed` for details
            on how to specify this schema). One field of this schema will act
            as reference to the linked object.

        field: The name of the field to act as reference to the linked object.

        attr: see :class:`Field`.

        key: see :class:`Field`.

        get: see :class:`Field`.

        val: see :class:`Field`.

        kwargs: see :class:`Embed`.


    '''
    def __init__(self,
                 *,
                 schema,
                 field,
                 attr=None,
                 key=None,
                 get=None,
                 val=None,
                 **kwargs):
        super().__init__(schema=schema,
                         attr=attr, key=key, get=get, val=val, **kwargs)
        self._field = field

    @util.reify
    def _pack_func(self):
        '''Return the associated schema's dump field *function* (reified).'''
        return self._schema_inst._dump_field_func(self._field)

    def pack(self, val):
        '''Return value of reference field of marshalled representation of val.

        Args:
            val: The nested object to get the reference to.

        Returns:
            The value of the reference-field of the marshalled representation
            of val (see ``field`` argument of constructor) or ``None`` if
            ``val`` is ``None``.

        Note that the return value is determined using an (internal) dump field
        *function* of the associated schema object. This means that overriding
        the associated schema's :meth:`~lima.schema.Schema.dump` *method* has
        no effect on the result of this method.

        '''
        return self._pack_func(val) if val is not None else None


TYPE_MAPPING = {
    bool: Boolean,
    float: Float,
    int: Integer,
    str: String,
    datetime.date: Date,
    datetime.datetime: DateTime,
    decimal.Decimal: Decimal,
}
'''A mapping of native Python types to :class:`Field` classes.

This can be used to automatically create fields for objects you know the
attribute's types of.'''
