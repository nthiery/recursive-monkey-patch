# -*- coding: utf-8 -*-
"""
Recursive monkey patching
"""
#*****************************************************************************
#  Copyright (C) 2013-2016 Nicolas M. Thiéry <nthiery at users.sf.net>
#                     2018 Julian Rüth <julian.rueth@fsfe.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

import logging
import importlib
import pkgutil
import sys
from types import ModuleType
# Python 2/3 compatibility: we will want TypeType to match both old and new style classes
try:
    from types import ClassType
    TypeType = (type, ClassType)
except:
    TypeType = type

# Detect whether the SageMath librar is in the path, and if so import
# some classes that require special handling
in_sage=False
try:
    from sage.categories.category_singleton import Category_singleton
    in_sage=True
except:
    pass

def full_name(t):
    if isinstance(t, ModuleType):
        return t.__name__
    else:
        return t.__module__+"."+t.__name__

def monkey_patch(source, target, log_level=logging.WARNING, logger=None):
    """
    Monkey patch recursively ``source`` into ``target``.

    INPUT:

    - ``source``, ``target`` -- modules or classes
    - ``log_level`` -- a :mod:`logging` level (default: logging.warning)
    - ``logger`` -- a :class:`logging.Logger` (default: None): for internal use

    This recurses through the (sub)modules and (nested) classes of
    ``source``; if a (sub)module or (nested) class that does not
    appear at the corresponding location in ``target``, then it is
    copied over. Except for a few special attributes, any function,
    method, or class attribute is copied over, overwriting the
    original content.

    EXAMPLES:

    We start with a small example where we use a patching class
    `AMonkeyPatch` to extend an existing class `A`::

        >>> class A:
        ...     def f(self):
        ...         return "calling A.f"
        ...     def g(self):
        ...         return "calling A.g"
        ...     class Nested:
        ...         pass
        >>> a = A()
        >>> a.f()
        'calling A.f'
        >>> a.g()
        'calling A.g'

        >>> class AMonkeyPatch:
        ...     def f(self):
        ...         return "calling AMonkeyPatch.f"
        ...     class Nested:
        ...         def f(self):
        ...             return "calling AMonkeyPatch.Nested.f"
        ...         x = 1
        ...     class Nested2:
        ...         pass

    We recursively monkey patch the features from `AMonkeyPatch` into `A`::

        >>> from recursive_monkey_patch import monkey_patch
        >>> monkey_patch(AMonkeyPatch, A)

    Now, all the features implemented in `AMonkeyPatch` are available
    for instances of `A` and its nested classes::

        >>> a.f()
        'calling AMonkeyPatch.f'
        >>> a.g()
        'calling A.g'
        >>> a_nested = A.Nested()
        >>> a_nested.f()
        'calling AMonkeyPatch.Nested.f'

        >>> a = A()
        >>> a.f()
        'calling AMonkeyPatch.f'
        >>> a.g()
        'calling A.g'
        >>> a_nested = A.Nested()
        >>> a_nested.f()
        'calling AMonkeyPatch.Nested.f'

        >>> a_nested.x
        1

    .. NOTE::

        The class ``AMonkeyPatch.Nested2`` that did not exist in ``A`` is
        copied over::

            >>> A.Nested2 is AMonkeyPatch.Nested2
            True

        Unlike ``AMonkeyPatch.Nested`` which is just patched::

            >>> A.Nested is AMonkeyPatch.Nested
            False

    .. RUBRIC:: Recursively monkey patching modules and packages

    We now demonstrate a typical use case, where we use a patching
    module to extend the features of an existing module::

        >>> import a_test_module
        >>> dir(a_test_module.submodule)
        ['A', '__builtins__', ...]

        >>> import a_test_module_patch
        >>> dir(a_test_module_patch.submodule)
        ['A', 'B', '__builtins__', ...]

    The following little digression is not needed in normal operation.
    Here we want to log information on standard output for
    demonstration and testing purposes::

        >>> import sys
        >>> import logging
        >>> logger = logging.Logger("monkey_patch.test", level=logging.INFO)
        >>> logger.addHandler(logging.StreamHandler(sys.stdout))

    We now recursively monkey patch the features of
    ``a_test_module_patch`` into ``a_test_module``::

        >>> monkey_patch(a_test_module_patch, a_test_module, logger=logger)
        Monkey patching a_test_module.submodule.A.NestedNew
        Monkey patching a_test_module.submodule.A.__doc__
        Monkey patching a_test_module.submodule.B

        >>> dir(a_test_module.submodule)
        ['A', 'B', '__builtins__', ...]
        >>> dir(a_test_module.submodule_new)
        ['New', '__builtins__', ...]

    .. RUBRIC:: Automatizing the monkey patching

    A typical idiom is to put the :func:`monkey_patch` call in the
    patching module initialization (see the code of
    :mod:`a_test_module2.__init__` for an example). Then the user only
    has to import the patching module::

        >>> import a_test_module_patch2
        >>> dir(a_test_module.submodule)
        ['A', 'B', 'C', '__builtins__', ...]

    .. RUBRIC:: Testing the handling of special attributes

    As for other attributes, documentation is copied over::

        >>> from a_test_module.submodule import A
        >>> A.__doc__
        'A (patched)'

    except for new style classes, in Python 2, because the attribute
    ``__doc__`` is read only for those::

        >>> class B(object):
        ...      "B (original)"
        >>> class B_patch(object):
        ...      "B (patched)"
        >>> monkey_patch(B_patch, B)
        >>> B.__doc__ == ('B (original)' if sys.version_info.major == 2 else 'B (patched)')
        True

    Unpatched documentation is not deleted when no documentation is
    specified in the patch::

        >>> A.Nested.__doc__
        'A.Nested'

    Some special attributes are not copied over. For example, the
    original module name of a class is preserved::

        >>> A.__module__
        'a_test_module.submodule'

    Of course, classes that are copied over as is have their module
    defined appropriately::

        >>> A.NestedNew.__module__
        'a_test_module_patch.submodule'

    .. RUBRIC:: Testing that new modules behave like preexisting modules

    The new modules can be imported (actually they are already imported)::

        >>> import a_test_module.submodule_new
        >>> from a_test_module.submodule_new import New
        >>> New.__module__
        'a_test_module.submodule_new'

    The patch modules can also be imported explicitly::

        >>> import a_test_module_patch.submodule_new
        >>> from a_test_module_patch.submodule_new import New as New_

    Note that types impported from the patch pretend to come from a different
    package::

        >>> New_.__module__
        'a_test_module.submodule_new'
        >>> New_ is New
        True

    """
    if logger is None:
        logger = logging.Logger("monkey_patch."+source.__name__, level=log_level)
        logger.addHandler(logging.StreamHandler(sys.stderr))
    logger.debug("Monkey patching {} into {}".format(source.__name__, target.__name__))

    if isinstance(source, ModuleType):
        if not isinstance(target, ModuleType):
            raise TypeError("target must be a module but %r is a %s"%(target, type(target)))
        if hasattr(source, "__path__"):
            # Force loading all submodules
            for (module_loader, name, ispkg) in pkgutil.iter_modules(path=source.__path__):
                try:
                    importlib.import_module(target.__name__+"."+name)
                except ImportError:
                    # if there is no target.name submodule, then import
                    # source.name as if it was called target.name
                    sys.modules[target.__name__] = source
                    try:
                        subsource = importlib.import_module("."+name, target.__name__)
                        setattr(target, name, subsource)
                        sys.modules[source.__name__+"."+name] = subsource
                    finally:
                        sys.modules[target.__name__] = target
                else:
                    subsource = importlib.import_module(source.__name__ +"."+name)
                setattr(source, name, subsource)

    # The sorting is just to have a reproducible log
    # It could be easily removed if performance would call for it
    for key in sorted(source.__dict__.keys()):
        subsource = source.__dict__[key]
        logger.debug("Considering {}.{}".format(source, key))
        if isinstance(source, ModuleType):
            # If the source is a module, ignore all entries that are not defined in this module
            # Any better test for this?
            # At this point, all constants are ignored because we
            # don't know how to test whether they have been defined or
            # imported in this module
            if isinstance(subsource, ModuleType):
                if not subsource.__name__.startswith(source.__name__):
                    continue
            else:
                if not (hasattr(subsource, '__module__') and subsource.__module__ == source.__name__):
                    continue

        if isinstance(subsource, ModuleType):
            logger.debug("Examining submodule: {}".format(key))
            subtarget = importlib.import_module(target.__name__+"."+key)
            if subtarget is not subsource:
                if not isinstance(subtarget, (type, ModuleType)):
                    raise TypeError("%s.%s must be a module but it is a %s"%(target.__name__, key, type(subtarget)))
                logger.debug("Recursing into preexisting submodule of the target")
                monkey_patch(subsource, subtarget, logger=logger)
            continue

        if isinstance(subsource, (type, TypeType)) and key in target.__dict__:
            # Recurse into a class which already exists in the target
            subtarget = target.__dict__[key]
            if not isinstance(subtarget, (type, TypeType)):
                raise TypeError("expected '%s' to be a type in the target but it is a %s"%(key, type(subtarget)))
            monkey_patch(subsource, subtarget, logger=logger)
            continue

        # Skip unrelevant technical entries
        # In particular, don't override the module name of the target
        if key in ['__module__', '__dict__', '__weakref__']:
            continue
        if key == "__doc__":
            # Don't override existing documentation with undefined documentation,
            if subsource is None:
                continue
            # New style classes in Python 2 don't support __doc__ assignment, so skip those
            if sys.version_info.major == 2 and isinstance(target, type):
                continue
        logger.info("Monkey patching {}.{}".format(full_name(target), key))
        setattr(target, key, subsource)

    ##########################################################################
    # Special handling of categories in Sage
    ##########################################################################
    #
    # Many categories are constructed during Sage's initialization;
    # hence the monkey patching (e.g. triggered by loading a package
    # in the users's startup file) often occurs after the fact.
    #
    # However, upon constructing a category Cs(), the class
    # Cs().parent_class is built by copying over the methods and
    # attributes from Cs.ParentMethods. Hence, if Cs() has already
    # been constructed, the monkey patching needs to explicitly update
    # not only Cs.ParentMethods but also Cs.parent_class.
    #
    # At this stage this is only implemented for singleton categories
    # The same could be implemented for other category classes by
    # looking up in the UniqueRepresentation cache which instances of
    # the class have already been constructed.
    if in_sage and isinstance(target, type) and issubclass(target, Category_singleton):
        category = target.an_instance()
        for cls_key, category_key in (("ParentMethods", "parent_class"),
                                      ("ElementMethods", "element_class"),
                                      ("MorphismMethods", "morphism_class"),
                                      ("SubcategoryMethods", "subcategory_class")):
            if cls_key in source.__dict__:
                monkey_patch(source.__dict__[cls_key], getattr(category, category_key), logger=logger)

    if "_monkey_patch_hook" in target.__dict__:
        target._monkey_patch_hook(source)
