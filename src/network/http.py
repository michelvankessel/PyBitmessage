import socket

from .advanceddispatcher import AdvancedDispatcher
from . import asyncore_pollchoose as asyncore
from .proxy import ProxyError
from .socks5 import Socks5Connection, Socks5Resolver
from .socks4a import Socks4aConnection, Socks4aResolver


class HttpError(ProxyError):
    pass


class HttpConnection(AdvancedDispatcher):
    def __init__(self, host, path="/", connect=True):
        AdvancedDispatcher.__init__(self)
        self.path = path
        self.destination = (host, 80)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        if connect:
            self.connect(self.destination)
        print("connecting in background to %s:%i" % self.destination)

    def state_init(self):
        self.append_write_buf(
            "GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n"
            % (self.path, self.destination[0])
        )
        print("Sending %ib" % len(self.write_buf))
        self.set_state("http_request_sent", 0)
        return False

    def state_http_request_sent(self):
        if self.read_buf:
            print("Received %ib" % len(self.read_buf))
            self.read_buf = b""
        if not self.connected:
            self.set_state("close", 0)
        return False


class Socks5HttpConnection(Socks5Connection, HttpConnection):
    def __init__(self, host, path="/"):
        self.path = path
        Socks5Connection.__init__(self, address=(host, 80))

    def state_socks_handshake_done(self):
        HttpConnection.state_init(self)
        return False


class Socks4aHttpConnection(Socks4aConnection, HttpConnection):
    def __init__(self, host, path="/"):
        Socks4aConnection.__init__(self, address=(host, 80))
        self.path = path

    def state_socks_handshake_done(self):
        HttpConnection.state_init(self)
        return False


if __name__ == "__main__":
    # initial fill
    for host in ("bootstrap8080.bitmessage.org", "bootstrap8444.bitmessage.org"):
        proxy5r = Socks5Resolver(host=host)
        while asyncore.socket_map:
            print("loop %s, len %i" % (proxy5r.state, len(asyncore.socket_map)))
            asyncore.loop(timeout=1, count=1)
        proxy5r.resolved()

        proxy4r = Socks4aResolver(host=host)
        while asyncore.socket_map:
            print("loop %s, len %i" % (proxy4r.state, len(asyncore.socket_map)))
            asyncore.loop(timeout=1, count=1)
        proxy4r.resolved()

    for host in ("bitmessage.org",):
        direct = HttpConnection(host)
        while asyncore.socket_map:
            asyncore.loop(timeout=1, count=1)

        proxy5 = Socks5HttpConnection(host)
        while asyncore.socket_map:
            asyncore.loop(timeout=1, count=1)

        proxy4 = Socks4aHttpConnection(host)
        while asyncore.socket_map:
            asyncore.loop(timeout=1, count=1)
