Recursive monkey patching for Python
====================================

Motivating use case
-------------------

Let ``foo`` be a Python package, built on top of another Python
package ``bar``. Sometimes ``foo`` may wish to extend the ``bar``
package by adding features (e.g. methods) to existing classes or
modules. Sometimes the whole package is meant as a temporary location
where experimental features can mature and be distributed early until
they get merged into the ``bar`` package.

In such cases, it's desirable to write the source code of those
features as closely as if they were in the ``bar`` package.

``recursive-monkey-patch`` enables this by providing a tool to
recursively monkey patch the ``bar`` package. Let's assume for example
that we are writing a package ``bar-foo`` that requires the addition
of a method ``f`` to the class ``bar.x.y.z.Z``.

To achieve this, one writes a module ``sage_foo.x.y.z.Z`` containing a
dummy ``Z`` class:

    class Z:
        def f(self):
            return "f"

And then, upon initializing the package, one runs:

    import bar
    import foo
    from recursive_monkey_patch import monkey_patch
    monkey_patch(foo, bar)

which will recursively crawl through ``foo``, and insert methods like
``f`` at the corresponding location in ``bar``. If a class or module
in ``foo`` does not exist in ``bar``, then the module is inserted at
the corresponding location in ``bar``

Relation with SageMath
----------------------

This package is primarily meant for writing (experimental) packages on
top of `SageMath <http://sagemath.org>`_, an open source software for
mathematics that includes a large Python library. However, the
dependency upon the ``SageMath`` package is actually light:

- Running the doctests requires ``sage``;
- When the SageMath package is present, the monkey patching involves a
  few additional Sage specific hacks.

ToDo
----

- Support for lazy imports
- Where is the natural place for running ``monkey_patch` in a package?
