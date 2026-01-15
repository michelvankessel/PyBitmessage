"""jsonrpclib stub package for type checking"""
from typing import Any, Optional


class SimpleJSONRPCServer:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def handle_request(self) -> None: ...
    allow_reuse_address: bool
    content_type: str


class ServerProxy:
    def __init__(self, uri: str, transport: Any = None, encoding: Optional[str] = None, verbose: bool = False, allow_none: bool = False, use_datetime: bool = False) -> None: ...
    def __getattr__(self, name: str) -> Any: ...


jsonrpc: Any