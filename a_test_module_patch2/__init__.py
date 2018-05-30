from __future__ import absolute_import
from . import a_test_module as patch
import a_test_module

from recursive_monkey_patch import monkey_patch
monkey_patch(patch, a_test_module)

