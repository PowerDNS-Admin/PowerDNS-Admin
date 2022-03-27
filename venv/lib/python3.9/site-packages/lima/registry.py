'''Internal class registry.

.. warning::

    For users of lima there should be no need to use anything within
    :mod:`lima.registry` directly. Name and contents of this module may change
    at any time without deprecation notice or upgrade path.

'''
from collections import defaultdict

from lima import exc


class Registry:
    '''A class registry.'''

    def __init__(self):
        # A mapping of fully module-qualified class names (of the form
        # "modulename.qualname") to these classes.
        self._classes = {}

        # A mapping of non-module-qualified qualnames to sets. Those sets
        # contain the names of modules having the respective classes defined.
        self._defining_modules = defaultdict(set)

    def register(self, cls):
        '''Register a class.

        Args:
            cls: The class to register. Must not have been defined in a local
                namespace.

        Raises:
            RegisterLocalClassError: In case ``cls`` is a class defined in a
                local namespace (see :class:`exc.RegisterLocalClassError`).

        '''
        qualname = cls.__qualname__
        module = cls.__module__
        fullname = '{}.{}'.format(module, qualname)

        # Refuse to register classes that are defined in local namespaces.
        if '<locals>' in qualname:
            raise exc.RegisterLocalClassError(fullname)

        self._classes[fullname] = cls
        self._defining_modules[qualname].add(module)

    def get(self, name):
        '''Get a registered class by its name and return it.

        Args:
            name: The name of the class to look up. Has to be either the
                class's qualified name or the class's fully module-qualified
                name in case two classes with the same qualified name from
                different modules were registered (see the :ref:`entry on class
                names <on_class_names>` for clarification of these concepts).
                Schemas defined within a local namespace can not be referenced
                by name.

        Returns:
            The specified class.

        Raises:
            ClassNotFoundError: If the specified class could not be found (see
                :class:`lima.exc.ClassNotFoundError`).

            AmbiguousClassNameError: If more than one class was found. Usually
                this can be fixed by using a fully module-qualified class name
                (see :class:`lima.exc.AmbiguousClassNameError`).

        '''
        # If a class can be found directly, name must be a fully
        # module-qualified name of the form "modulename.qualname".
        # Just return the class then.
        if name in self._classes:
            return self._classes[name]

        # Or maybe the name is just not module-qualified?
        elif name in self._defining_modules:
            defining_modules = self._defining_modules[name]

            # Fail if more than one class with the same qualname exists in
            # different modules
            if len(defining_modules) > 1:
                raise exc.AmbiguousClassNameError(name)

            module = next(iter(defining_modules))  # get the single set member
            fullname = '{}.{}'.format(module, name)
            return self._classes[fullname]

        # Otherwise: not found.
        raise exc.ClassNotFoundError(name)


global_registry = Registry()
'''A global :class:`Registry` instance.

Used internally by lima to automatically keep track of created Schemas (this is
needed by some field classes).

'''
