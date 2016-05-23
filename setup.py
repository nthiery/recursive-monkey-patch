## -*- encoding: utf-8 -*-
"""Recursive Monkey Patching
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='recursive-monkey-patch',
    version='0.1.1',
    description='Recursive Monkey Patching',
    long_description=long_description,
    url='https://github.com/nthiery/recursive-monkey-patch',
    author='Nicolas M. Thiéry',
    author_email='nthiery@users.sf.net',
    license='GPLv2+',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    keywords='packaging development',
    py_modules=["recursive_monkey_patch"],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
