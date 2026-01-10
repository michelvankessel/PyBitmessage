"""
Testing the logger configuration
"""

import tempfile
from pathlib import Path

from .test_process import TestProcessProto


class TestLogger(TestProcessProto):
    """A test case for logger configuration"""

    pattern = r" <===> "
    conf_template = """
[loggers]
keys=root

[handlers]
keys=default

[formatters]
keys=default

[formatter_default]
format=%(asctime)s {1} %(message)s

[handler_default]
class=FileHandler
level=NOTSET
formatter=default
args=({0!r}, 'w')

[logger_root]
level=DEBUG
handlers=default
"""

    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp()
        cls._files = cls._files[2:] + ("logging.dat",)
        cls.log_file = str(Path(cls.home) / "debug.log")

        with open(Path(cls.home) / "logging.dat", "wb") as dst:
            dst.write(cls.conf_template.format(cls.log_file, cls.pattern))

        super(TestLogger, cls).setUpClass()

    def test_fileConfig(self):
        """Check that our logging.dat was used"""

        self._stop_process()
        data = open(self.log_file).read()
        self.assertRegex(data, self.pattern)
        self.assertRegex(data, "Loaded logger configuration")
