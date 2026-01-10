"""Stubs for cryptography.hazmat.backends"""

from typing import Any

def default_backend() -> Any: ...

class Backend:
    def openssl_version_text(self) -> str: ...
    version: int
    version_info: tuple[int, ...]

# vim: set ft=python:
