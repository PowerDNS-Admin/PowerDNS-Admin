'''Internal utilities.

.. warning::

    For users of lima there should be no need to use anything within
    :mod:`lima.util` directly. Name and contents of this module may change at
    any time without deprecation notice or upgrade path.

'''
from collections import abc
from contextlib import contextmanager


@contextmanager
def exception_context(context_info):
    '''Context manager adding info to msg of exceptions raised within.'''
    try:
        yield
    except Exception as e:
        # adapted from http://stackoverflow.com/a/17677938
        msg = '{}: {}'.format(context_info, e) if e.args else context_info
        e.args = (msg, ) + e.args[1:]
        raise


# The code for this class is taken from pyramid.decorator (with negligible
# alterations), licensed under the Repoze Public License (see
# http://www.pylonsproject.org/about/license)
class reify:
    '''Like property, but saves the underlying method's result for later use.

    Use as a class method decorator. It operates almost exactly like the Python
    ``@property`` decorator, but it puts the result of the method it decorates
    into the instance dict after the first call, effectively replacing the
    function it decorates with an instance variable. It is, in Python parlance,
    a non-data descriptor. An example:

    .. code-block:: python

       class Foo(object):
           @reify
           def jammy(self):
               print('jammy called')
               return 1

    And usage of Foo:

    >>> f = Foo()
    >>> v = f.jammy
    'jammy called'
    >>> print(v)
    1
    >>> f.jammy
    1
    >>> # jammy func not called the second time; it replaced itself with 1

    Taken from pyramid.decorator (see source for license info).

    '''
    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.__doc__ = wrapped.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        val = self.wrapped(instance)
        setattr(instance, self.wrapped.__name__, val)
        return val


# The code for this class is taken directly from the Python 3.4 standard
# library (to support Python 3.3), licensed under the PSF License (see
# https://docs.python.org/3/license.html)
class suppress:
    '''Context manager to suppress specified exceptions

    After the exception is suppressed, execution proceeds with the next
    statement following the with statement.

         with suppress(FileNotFoundError):
             os.remove(somefile)
         # Execution still resumes here if the file was already removed

    Backported for Python 3.3 from Python 3.4 (see source for license info).

    '''
    def __init__(self, *exceptions):
        self._exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exctype, excinst, exctb):
        # Unlike isinstance and issubclass, CPython exception handling
        # currently only looks at the concrete type hierarchy (ignoring
        # the instance and subclass checking hooks). While Guido considers
        # that a bug rather than a feature, it's a fairly hard one to fix
        # due to various internal implementation details. suppress provides
        # the simpler issubclass based semantics, rather than trying to
        # exactly reproduce the limitations of the CPython interpreter.
        #
        # See http://bugs.python.org/issue12029 for more details
        return exctype is not None and issubclass(exctype, self._exceptions)


def vector_context(obj):
    '''Return obj if obj is a vector, or [obj] in case obj is a scalar.

    For this function, a *vector* is an iterable that's no string. Everything
    else counts as a *scalar*.

    Inspired by Perl's list context (this has nothing to do with Python context
    managers). Useful to provide scalar values to operations that expect
    vectors (so there's no need to put brackets around single elements).

    Args:
        obj: Any object

    Returns:
        ``obj`` if obj is a vector, otherwise ``[obj]``.

    '''
    if isinstance(obj, abc.Iterable) and not isinstance(obj, str):
        return obj
    return [obj]


def ensure_iterable(obj):
    '''Raise TypeError if obj is not iterable.'''
    if not isinstance(obj, abc.Iterable):
        raise TypeError('{!r} is not iterable.'.format(obj))


def ensure_mapping(obj):
    '''Raise TypeError if obj is no mapping.'''
    if not isinstance(obj, abc.Mapping):
        raise TypeError('{!r} is not a mapping.'.format(obj))


def ensure_only_one_of(collection, elements):
    '''Raise ValueError if collection contains more than one of elements.

    Only distinct elements are considered. For mappings, the keys are
    considered.

    Args:
        collection: An iterable container.

        elements: A set of elements that must not appear together.

    Raises:
        ValueError: If *collection* contains more than one (distinct) element
            of *elements*.

    '''
    found = set(collection) & set(elements)
    if len(found) > 1:
        raise ValueError('Mutually exclusive: {!r}'.format(found))


def ensure_subset_of(collection, superset):
    '''Raise ValueError if collection is no subset of superset

    Only distinct elements are considered. For mappings, only the keys are
    considered.

    Args:
        collection: An iterable container.

        superset: A set of allowed elements.

    Raises:
        ValueError: If *collection* contains more than one (distinct) element
            of *elements*.

    '''
    excess = set(collection) - set(superset)
    if excess:
        raise ValueError('Excess element(s): {!r}'.format(excess))


def ensure_only_instances_of(collection, cls):
    '''Raise TypeError, if collection contains elements not of type cls.'''
    found = [obj for obj in collection if not isinstance(obj, cls)]
    if found:
        raise TypeError('No instances of {}: {!r}'.format(cls, found))
