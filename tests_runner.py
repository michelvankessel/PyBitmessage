#!/usr/bin/env python3
"""Custom tests runner script for tox and python3"""
import random
import sys
import unittest


def unittest_discover():
    """Explicit test suite creation"""
    if sys.hexversion >= 0x3000000:
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            import pathmagic
        else:
            from pybitmessage import pathmagic
        pathmagic.setup()
    loader = unittest.defaultTestLoader
    # randomize the order of tests in test cases
    loader.sortTestMethodsUsing = lambda a, b: random.randint(-1, 1)
    # pybitmessage symlink disappears on Windows!
    testsuite = loader.discover('pybitmessage.tests')
    testsuite.addTests([loader.discover('pybitmessage.pyelliptic')])

    return testsuite


if __name__ == "__main__":
    success = unittest.TextTestRunner(verbosity=2).run(
        unittest_discover()).wasSuccessful()
    try:
        from pybitmessage.tests import common
    except ImportError:
        checkup = False
    else:
        checkup = common.checkup()

    if checkup and not success:
        print(checkup)

    sys.exit(not success or checkup)
