import os
import tempfile
import sys

# Safety guard: Ensure BITMESSAGE_HOME is set to a temp dir if not already provided
# This protects production data from being overwritten by tests.
if "BITMESSAGE_HOME" not in os.environ:
    _temp_home = tempfile.mkdtemp(prefix="pybitmessage_test_")
    os.environ["BITMESSAGE_HOME"] = _temp_home
    print(f"NOTE: BITMESSAGE_HOME not set. Using temporary directory for tests: {_temp_home}", file=sys.stderr)


if getattr(sys, 'frozen', None):
    from .test_addresses import TestAddresses
    from .test_crypto import TestHighlevelcrypto
    from .test_l10n import TestL10n
    from .test_packets import TestSerialize
    from .test_protocol import TestProtocol

    __all__ = [
        "TestAddresses", "TestHighlevelcrypto", "TestL10n",
        "TestProtocol", "TestSerialize"
    ]
