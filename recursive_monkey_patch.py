# -*- coding: utf-8 -*-
"""
Recursive monkey patching
"""
#*****************************************************************************
#  Copyright (C) 2013-2016 Nicolas M. Thiéry <nthiery at users.sf.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from __future__ import print_function
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

def monkey_patch(source, target, verbose=False):
    """
    Monkey patch recursively ``source`` into ``target``.

    INPUT:

    - ``source``, ``target`` -- modules or classes
    - ``verbose`` -- a boolean (default: False)

    This recurses through the (sub)modules and (nested) classes of
    ``source``; if a module or class that does not appear at the
    corresponding location in ``target``, then it is copied other. Any
    function, method or class/module attribute is copied over.

    EXAMPLES::

        >>> from recursive_monkey_patch import monkey_patch

        >>> class A:
        ...     "The class A"
        ...     def f(self):
        ...         return "calling A.f"
        ...     def g(self):
        ...         return "calling A.g"
        ...     class Nested:
        ...         "The class A.Nested"
        ...     class Nested2(object):
        ...         "The class A.Nested2"

        >>> a = A()
        >>> a.f()
        'calling A.f'
        >>> a.g()
        'calling A.g'

        >>> class AMonkeyPatch:
        ...     "The class AMonkeyPatch"
        ...     def f(self):
        ...         return "calling AMonkeyPatch.f"
        ...     class Nested:
        ...         def f(self):
        ...             return "calling AMonkeyPatch.Nested.f"
        ...         x = 1
        ...     class Nested2:
        ...         "The class AMonkeyPatch.Nested2"
        ...         pass
        ...     class Nested3:
        ...         pass

        >>> monkey_patch(AMonkeyPatch, A)

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

    The class ``AMonkeyPatch.Nested3`` that did not exist in ``A`` is
    copied over::

        >>> A.Nested3 is AMonkeyPatch.Nested3
        True

    Unlike  ``AMonkeyPatch.Nested2``::

        >>> A.Nested2 is AMonkeyPatch.Nested2
        False

    Special cases: some special attributes are not copied over.

    For example, the original module name of a class is preserved::

        >>> class source(object):
        ...    __module__ = 'source_module'
        >>> class target(object):
        ...    __module__ = 'target_module'
        >>> target
        <class 'target_module.target'>
        >>> monkey_patch(source, target)
        >>> target
        <class 'target_module.target'>

    Existing documentation is copied over::

        >>> A.__doc__
        'The class AMonkeyPatch'
        >>> A.Nested.__doc__
        'The class A.Nested'

    except for new style classes, in Python 2::

        >>> import sys
        >>> A.Nested2.__doc__ == ('The class A.Nested2' if sys.version_info.major == 2 else 'The class AMonkeyPatch.Nested2')
        True

    This is because the attribute ``__doc__`` is read only for those.
    """
    if verbose:
        print("Monkey patching %s into %s"%(source.__name__, target.__name__), file=stderr)
    if isinstance(source, ModuleType):
        assert isinstance(target, ModuleType)
        if hasattr(source, "__path__"):
            # Recurse into package
            for (module_loader, name, ispkg) in pkgutil.iter_modules(path=source.__path__, prefix=source.__name__+"."):
                subsource = module_loader.find_module(name).load_module(name)
                short_name = name.split('.')[-1]
                if short_name in target.__dict__:
                    subtarget = target.__dict__[short_name]
                    assert isinstance(subtarget, (type, ModuleType))
                    monkey_patch(subsource, subtarget, verbose=verbose)

    for (key, subsource) in source.__dict__.items():
        if isinstance(source, ModuleType) and \
           not (hasattr(subsource, "__module__") and subsource.__module__ == source.__name__):
            continue
        if isinstance(subsource, (type, TypeType)) and key in target.__dict__:
            # Recurse into class
            subtarget = target.__dict__[key]
            assert isinstance(subtarget, (type, TypeType))
            monkey_patch(subsource, subtarget, verbose=verbose)
            continue

        if verbose:
            print("Handling attribute %s"%(key), file=stderr)

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
                monkey_patch(source.__dict__[cls_key], getattr(category, category_key), verbose=verbose)

