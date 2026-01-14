"""
This is based upon the singleton class from
`tendo <https://github.com/pycontribs/tendo>`_
which is under the Python Software Foundation License version 2
"""

import atexit
import os
import sys
from pathlib import Path

import state

try:
    import fcntl  # @UnresolvedImport
except ImportError:
    pass


class singleinstance(object):
    """
    Implements a single instance application by creating a lock file
    at appdata.
    """

    def __init__(self, flavor_id="", daemon=False):
        self.initialized = False
        self.counter = 0
        self.daemon = daemon
        self.lockPid = None
        self.lockfile = str(Path(state.appdata) / f"singleton{flavor_id}.lock")

        if state.enableGUI and not self.daemon and not state.curses:
            # Tells the already running (if any) application to get focus.
            # We do this SILENTLY via QLocalSocket to avoid bouncing dock icons on macOS.
            try:
                from PyQt6.QtNetwork import QLocalSocket
                socket = QLocalSocket()
                socket.connectToServer(state.singleton_uuid)
                if socket.waitForConnected(500):
                    socket.abort()
                    sys.exit("Another instance of this application is already running")
                socket.abort()
            except ImportError:
                # If PyQt6 is not available, we can't do the silent check.
                # The normal lock file logic below will still catch it.
                pass

        self.lock()

        self.initialized = True
        atexit.register(self.cleanup)

    def lock(self):
        """Obtain single instance lock"""
        from debug import logger
        if self.lockPid is None:
            self.lockPid = os.getpid()
        if sys.platform == "win32":
            try:
                # file already exists, we try to remove
                # (in case previous execution was interrupted)
                lockfile_path = Path(self.lockfile)
                if lockfile_path.exists():
                    lockfile_path.unlink()
                self.fd = os.open(
                    self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_TRUNC
                )
                logger.debug("Windows lock file created: %s", self.lockfile)
            except OSError as e:
                if e.errno == 13:
                    logger.error("Windows lock contention detected for %s", self.lockfile)
                    sys.exit("Another instance of this application is already running")
                raise
            else:
                pidLine = "%i\n" % self.lockPid
                os.write(self.fd, pidLine.encode())
                logger.debug("PID %i written to Windows lockfile.", self.lockPid)
        else:  # non Windows
            self.fp = open(self.lockfile, "a+")
            try:
                if self.daemon and self.lockPid != os.getpid():
                    # wait for parent to finish
                    fcntl.lockf(self.fp, fcntl.LOCK_EX)
                else:
                    fcntl.lockf(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.lockPid = os.getpid()
            except IOError:
                sys.exit("Another instance of this application is already running")
            else:
                pidLine = "%i\n" % self.lockPid
                self.fp.truncate(0)
                self.fp.write(pidLine)
                self.fp.flush()

    def cleanup(self):
        """Release single instance lock"""
        if not self.initialized:
            return
        if self.daemon and self.lockPid == os.getpid():
            # these are the two initial forks while daemonizing
            try:
                if sys.platform == "win32":
                    if hasattr(self, "fd"):
                        os.close(self.fd)
                else:
                    fcntl.lockf(self.fp, fcntl.LOCK_UN)
            except (IOError, OSError):
                pass

            return

        try:
            if sys.platform == "win32":
                if hasattr(self, "fd"):
                    os.close(self.fd)
                    Path(self.lockfile).unlink()
            else:
                fcntl.lockf(self.fp, fcntl.LOCK_UN)
                if Path(self.lockfile).is_file():
                    Path(self.lockfile).unlink()
        except (IOError, OSError):
            pass
