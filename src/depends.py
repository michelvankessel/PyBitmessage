"""
Utility functions to check the availability of dependencies
and suggest how it may be installed
"""

import sys
from pathlib import Path
from typing import Optional

# Only really old versions of Python don't have sys.hexversion. We don't
# support them. The logging module was introduced in Python 2.3
if not hasattr(sys, "hexversion") or sys.hexversion < 0x30D00F0:
    sys.exit(
        "Python version: %s\nPyBitmessage requires Python 3.13 or greater" % sys.version
    )

import logging
import subprocess
from importlib import import_module

# We can now use logging so set up a simple configuration
formatter = logging.Formatter("%(levelname)s: %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger = logging.getLogger("both")
logger.addHandler(handler)
logger.setLevel(logging.ERROR)


OS_RELEASE = {
    "Debian GNU/Linux".lower(): "Debian",
    "fedora": "Fedora",
    "opensuse": "openSUSE",
    "ubuntu": "Ubuntu",
    "gentoo": "Gentoo",
    "calculate": "Gentoo",
}

PACKAGE_MANAGER = {
    "OpenBSD": "pkg_add",
    "FreeBSD": "pkg install",
    "Debian": "apt-get install",
    "Ubuntu": "apt-get install",
    "Ubuntu 12": "apt-get install",
    "Ubuntu 20": "apt-get install",
    "openSUSE": "zypper install",
    "Fedora": "dnf install",
    "Guix": "guix package -i",
    "Gentoo": "emerge",
}

PACKAGES = {
    "PyQt6": {
        "OpenBSD": "py3-qt6",
        "FreeBSD": "py39-qt6",
        "Debian": "python3-pyqt6",
        "Ubuntu": "python3-pyqt6",
        "Ubuntu 22": "python3-pyqt6",
        "openSUSE": "python3-qt6",
        "Fedora": "python3-pyqt6",
        "Guix": "python-pyqt@6",
        "Gentoo": "dev-python/PyQt6",
        "optional": True,
        "description": "You only need PyQt if you want to use the GUI."
        " When only running as a daemon, this can be skipped.",
    },
    "msgpack": {
        "OpenBSD": "py3-msgpack",
        "FreeBSD": "py39-msgpack",
        "Debian": "python3-msgpack",
        "Ubuntu": "python3-msgpack",
        "Ubuntu 12": "python3-msgpack",
        "Ubuntu 20": "",
        "openSUSE": "python3-msgpack",
        "Fedora": "python3-msgpack",
        "Guix": "python-msgpack",
        "Gentoo": "dev-python/msgpack",
        "optional": True,
        "description": "python-msgpack is recommended for improved performance of"
        " message encoding/decoding",
    },
    "pyopencl": {
        "FreeBSD": "py39-pyopencl",
        "Debian": "python3-pyopencl",
        "Ubuntu": "python3-pyopencl",
        "Ubuntu 12": "python3-pyopencl",
        "Ubuntu 20": "",
        "Fedora": "python3-pyopencl",
        "openSUSE": "",
        "OpenBSD": "",
        "Guix": "",
        "Gentoo": "dev-python/pyopencl",
        "optional": True,
        "description": "If you install pyopencl, you will be able to use"
        " GPU acceleration for proof of work.\n"
        "You also need a compatible GPU and drivers.",
    },
    "setuptools": {
        "OpenBSD": "py3-setuptools",
        "FreeBSD": "py39-setuptools",
        "Debian": "python3-setuptools",
        "Ubuntu": "python3-setuptools",
        "Ubuntu 12": "python3-setuptools",
        "Ubuntu 20": "python3-setuptools",
        "Fedora": "python3-setuptools",
        "openSUSE": "python3-setuptools",
        "Guix": "python-setuptools",
        "Gentoo": "dev-python/setuptools",
        "optional": False,
    },
    "cryptography": {
        "OpenBSD": "py3-cryptography",
        "FreeBSD": "py39-cryptography",
        "Debian": "python3-cryptography",
        "Ubuntu": "python3-cryptography",
        "openSUSE": "python3-cryptography",
        "Fedora": "python3-cryptography",
        "Gentoo": "dev-python/cryptography",
        "optional": False,
        "description": "cryptography is required for secure cryptographic operations.",
    },
}


_os_result: Optional[str] = None


def detectOS():
    """Finding out what Operating System is running"""
    global _os_result
    if _os_result is not None:
        return _os_result
    if sys.platform.startswith("openbsd"):
        _os_result = "OpenBSD"
    elif sys.platform.startswith("freebsd"):
        _os_result = "FreeBSD"
    elif sys.platform.startswith("win"):
        _os_result = "Windows"
    elif Path("/etc/os-release").is_file():
        detectOSRelease()
    elif Path("/etc/config.scm").is_file():
        _os_result = "Guix"
    return _os_result


def detectOSRelease():
    """Detecting the release of OS"""
    global _os_result
    with open("/etc/os-release", "r") as osRelease:
        version = None
        for line in osRelease:
            if line.startswith("NAME="):
                _os_result = OS_RELEASE.get(
                    line.replace('"', "").split("=")[-1].strip().lower()
                )
            elif line.startswith("VERSION_ID="):
                try:
                    version = float(line.split("=")[1].replace('"', ""))
                except ValueError:
                    pass
        if _os_result == "Ubuntu" and version < 14:
            _os_result = "Ubuntu 12"
        elif _os_result == "Ubuntu" and version >= 20:
            _os_result = "Ubuntu 20"


def try_import(module, log_extra=False):
    """Try to import the non imported packages"""
    try:
        return import_module(module)
    except ImportError:
        module = module.split(".")[0]
        logger.error("The %s module is not available.", module)
        if log_extra:
            logger.error(log_extra)
            dist = detectOS()
            logger.error(
                'On %s, try running "%s %s" as root.',
                dist,
                PACKAGE_MANAGER[dist],
                PACKAGES[module][dist],
            )
        return False


def check_cryptography():
    """Check availability of the cryptography library"""
    try:
        from cryptography.hazmat.backends import default_backend

        return default_backend() is not None
    except ImportError:
        return False


def check_ripemd160():
    """Check availability of the RIPEMD160 hash function"""
    try:
        from Crypto.Hash import RIPEMD160 as RIPEMD160Hash
    except ImportError:
        return False
    return RIPEMD160Hash is not None


def check_sqlite():
    """Do sqlite check.

    Simply check sqlite3 module if exist or not with hexversion
    support in python version for specifieed platform.
    """
    sqlite3 = try_import("sqlite3")
    if not sqlite3:
        return False

    logger.info("sqlite3 Module Version: %s", sqlite3.version)
    logger.info("SQLite Library Version: %s", sqlite3.sqlite_version)
    # sqlite_version_number formula: https://sqlite.org/c3ref/c_source_id.html
    sqlite_version_number = (
        sqlite3.sqlite_version_info[0] * 1000000
        + sqlite3.sqlite_version_info[1] * 1000
        + sqlite3.sqlite_version_info[2]
    )

    conn = None
    try:
        try:
            conn = sqlite3.connect(":memory:")
            if sqlite_version_number >= 3006018:
                sqlite_source_id = conn.execute(
                    "SELECT sqlite_source_id();"
                ).fetchone()[0]
                logger.info("SQLite Library Source ID: %s", sqlite_source_id)
            if sqlite_version_number >= 3006023:
                compile_options = ", ".join(
                    [row[0] for row in conn.execute("PRAGMA compile_options;")]
                )
                logger.info("SQLite Library Compile Options: %s", compile_options)
            # There is no specific version requirement as yet, so we just
            # use the first version that was included with Python.
            if sqlite_version_number < 3000008:
                logger.error(
                    "This version of SQLite is too old."
                    " PyBitmessage requires SQLite 3.0.8 or later"
                )
                return False
            return True
        except sqlite3.Error:
            logger.exception("An exception occured while checking sqlite.")
            return False
    finally:
        if conn:
            conn.close()


def check_openssl():
    """Do openssl dependency check.

    Now that we use the cryptography library, we primarily rely on its
    internal OpenSSL management.
    """
    try:
        from cryptography.hazmat.backends.openssl.backend import backend

        logger.info(
            "OpenSSL Version (via cryptography): %s", backend.openssl_version_text()
        )
        return True
    except ImportError:
        # If cryptography is missing, check_cryptography will catch it
        return True
    except Exception:
        logger.exception(
            "An exception occurred while checking OpenSSL via cryptography."
        )
        return False


# ..todo:: The minimum versions of pythondialog and dialog need to be determined
def check_curses():
    """Do curses dependency check.

    Here we are checking for curses if available or not with check as interface
    requires the `pythondialog <https://pypi.org/project/pythondialog>`_ package
    and the dialog utility.
    """
    curses = try_import("curses")
    if not curses:
        logger.error("The curses interface can not be used.")
        return False

    logger.info("curses Module Version: %s", curses.version)

    dialog = try_import("dialog")
    if not dialog:
        logger.error("The curses interface can not be used.")
        return False

    try:
        subprocess.check_call(["which", "dialog"])
    except subprocess.CalledProcessError:
        logger.error(
            "Curses requires the `dialog` command to be installed as well as"
            " the python library."
        )
        return False

    logger.info("pythondialog Package Version: %s", dialog.__version__)
    dialog_util_version = dialog.Dialog().cached_backend_version
    # The pythondialog author does not like Python2 str, so we have to use
    # unicode for just the version otherwise we get the repr form which
    # includes the module and class names along with the actual version.
    logger.info("dialog Utility Version %s", dialog_util_version.decode("utf-8"))
    return True


def check_pyqt():
    """Do pyqt dependency check.

    Here we are checking for PyQt6 with its version, as for it require
    PyQt 6.0 or later.
    """
    QtCore = try_import(
        "PyQt6.QtCore", "PyBitmessage requires PyQt 6.0 or later and Qt 6.0 or later."
    )

    if not QtCore:
        return False

    logger.info("PyQt Version: %s", QtCore.PYQT_VERSION_STR)
    logger.info("Qt Version: %s", QtCore.QT_VERSION_STR)
    passed = True
    if QtCore.PYQT_VERSION < 0x60000:
        logger.error(
            "This version of PyQt is too old. PyBitmessage requries PyQt 6.0 or later."
        )
        passed = False
    if QtCore.QT_VERSION < 0x60000:
        logger.error(
            "This version of Qt is too old. PyBitmessage requries Qt 6.0 or later."
        )
        passed = False
    return passed


def check_msgpack():
    """Do sgpack module check.

    simply checking if msgpack package with all its dependency
    is available or not as recommended for messages coding.
    """
    return (
        try_import("msgpack", "It is highly recommended for messages coding.")
        is not False
    )


def check_dependencies(verbose=False, optional=False):
    """Do dependency check.

    It identifies project dependencies and checks if there are
    any known, publicly disclosed, vulnerabilities.basically
    scan applications (and their dependent libraries) so that
    easily identify any known vulnerable components.
    """
    if verbose:
        logger.setLevel(logging.INFO)

    has_all_dependencies = True

    logger.info("Python version: %s", sys.version)
    if sys.hexversion < 0x30D00F0:
        logger.error("PyBitmessage requires Python 3.13 or greater")
        has_all_dependencies = False
    check_functions = [check_cryptography, check_ripemd160, check_sqlite, check_openssl]
    if optional:
        check_functions.extend([check_msgpack, check_pyqt, check_curses])
    # Unexpected exceptions are handled here
    for check in check_functions:
        try:
            has_all_dependencies &= check()
        except Exception:
            logger.exception("%s failed unexpectedly.", check.__name__)
            has_all_dependencies = False

    if not has_all_dependencies:
        sys.exit("PyBitmessage cannot start. One or more dependencies are unavailable.")


logger.setLevel(0)
