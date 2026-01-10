"""Stubs for jsonrpclib"""

from typing import Any

class SimpleJSONRPCServer:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def handle_request(self) -> None: ...
    allow_reuse_address: bool
    content_type: str

# vim: set ft=python:
