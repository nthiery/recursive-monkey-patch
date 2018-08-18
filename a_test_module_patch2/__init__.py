"""
Typical idiom to automatize the monkey patching

Importing this module triggers the monkey patching of its features into a_test_module.
"""

import sys
from recursive_monkey_patch import monkey_patch
import a_test_module
monkey_patch(sys.modules[__name__], a_test_module)
