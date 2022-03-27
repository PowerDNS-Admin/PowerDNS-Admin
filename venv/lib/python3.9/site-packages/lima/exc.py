'''The lima exception hierarchy.

.. note::

    Currently this module only holds Exceptions related to
    :mod:`lima.registry`, but this might change in the future.

'''


class RegistryError(Exception):
    '''The base class for all registry-related exceptions.'''
    pass


class RegisterLocalClassError(RegistryError, ValueError):
    '''Raised when trying to register a class defined in a local namespace.'''
    pass


class AmbiguousClassNameError(RegistryError, ValueError):
    '''Raised when asking for a class with an ambiguous name.

    Usually this is the case if two or more classes of the same name were
    registered from within different modules, and afterwards a registry is
    asked for one of those classes without specifying the module in the class
    name.

    '''
    pass


class ClassNotFoundError(RegistryError):
    '''Raised when a class was not found by a registry.'''
    pass
