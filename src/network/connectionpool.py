
"""
`BMConnectionPool` class definition
"""

import errno
import socket
import time
import random
import re
# import threading
import sys
import logging

# import paths
from network import asyncore_pollchoose as asyncore
# from network import receiveDataQueue
from network import knownnodes
import protocol
import state
from bmconfigparser import config
from .connectionchooser import chooseConnection
from .node import Peer
from .proxy import Proxy
from .tcp import (
    bootstrap,
    Socks4aBMConnection,
    Socks5BMConnection,
    TCPConnection,
    TCPServer,
)
from .udp import UDPSocket

logger = logging.getLogger("default")


class BMConnectionPool(object):
    """Pool of all existing connections"""

    trustedPeer = None
    """
    If the trustedpeer option is specified in keys.dat then this will
    contain a Peer which will be connected to instead of using the
    addresses advertised by other peers.

    The expected use case is where the user has a trusted server where
    they run a Bitmessage daemon permanently. If they then run a second
    instance of the client on a local machine periodically when they want
    to check for messages it will sync with the network a lot faster
    without compromising security.
    """

    def __init__(self):
        asyncore.set_rates(
            config.safeGetInt("bitmessagesettings", "maxdownloadrate"),
            config.safeGetInt("bitmessagesettings", "maxuploadrate"),
        )
        self.outboundConnections = {}
        self.inboundConnections = {}
        self.listeningSockets = {}
        self.udpSockets = {}
        self.streams = []
        self._lastSpawned = 0
        self._spawnWait = 2
        self._bootstrapped = False

        trustedPeer = config.safeGet("bitmessagesettings", "trustedpeer")
        try:
            if trustedPeer:
                host, port = trustedPeer.split(":")
                self.trustedPeer = Peer(host, int(port))
        except ValueError:
            sys.exit(
                "Bad trustedpeer config setting! It should be set as"
                " trustedpeer=<hostname>:<portnumber>"
            )

    def __len__(self):
        return len(self.outboundConnections) + len(self.inboundConnections)

    def connections(self):
        """
        Shortcut for combined list of connections from
        `inboundConnections` and `outboundConnections` dicts
        """
        return list(self.inboundConnections.values()) + list(
            self.outboundConnections.values()
        )

    def establishedConnections(self):
        """Shortcut for list of connections having fullyEstablished == True"""
        return [x for x in self.connections() if x.fullyEstablished]

    def connectToStream(self, streamNumber):
        """Connect to a bitmessage stream"""
        self.streams.append(streamNumber)

    def getConnectionByAddr(self, addr):
        """
        Return an (existing) connection object based on a `Peer` object
        (IP and port)
        """
        try:
            return self.inboundConnections[addr]
        except KeyError:
            pass
        try:
            return self.inboundConnections[addr.host]
        except (KeyError, AttributeError):
            pass
        try:
            return self.outboundConnections[addr]
        except KeyError:
            pass
        try:
            return self.udpSockets[addr.host]
        except (KeyError, AttributeError):
            pass
        raise KeyError

    def isAlreadyConnected(self, nodeid):
        """Check if we're already connected to this peer"""
        for i in self.connections():
            try:
                if nodeid == i.nodeid:
                    return True
            except AttributeError:
                pass
        return False

    def addConnection(self, connection):
        """Add a connection object to our internal dict"""
        if isinstance(connection, UDPSocket):
            return
        if connection.isOutbound:
            # print(f">>> ADDING OUTBOUND CONNECTION: {connection.destination} (id={id(connection.destination)})")
            self.outboundConnections[connection.destination] = connection
        else:
            if connection.destination.host in self.inboundConnections:
                self.inboundConnections[connection.destination] = connection
            else:
                self.inboundConnections[connection.destination.host] = connection

    def removeConnection(self, connection):
        """Remove a connection from our internal dict"""
        if isinstance(connection, UDPSocket):
            del self.udpSockets[connection.listening.host]
        elif isinstance(connection, TCPServer):
            del self.listeningSockets[
                Peer(connection.destination.host, connection.destination.port)
            ]
        elif connection.isOutbound:
            try:
                # print(f">>> REMOVING OUTBOUND CONNECTION: {connection.destination} (id={id(connection.destination)})")
                del self.outboundConnections[connection.destination]
            except KeyError:
                # print(f">>> FAILED TO REMOVE OUTBOUND: {connection.destination} - key not found")
                pass
        else:
            try:
                del self.inboundConnections[connection.destination]
            except KeyError:
                try:
                    del self.inboundConnections[connection.destination.host]
                except KeyError:
                    pass
        connection.handle_close()

    @staticmethod
    def getListeningIP():
        """What IP are we supposed to be listening on?"""
        if config.safeGet("bitmessagesettings", "onionhostname", "").endswith(".onion"):
            host = config.safeGet("bitmessagesettings", "onionbindip")
        else:
            host = "127.0.0.1"
        if (
            config.safeGetBoolean("bitmessagesettings", "sockslisten")
            or config.safeGet("bitmessagesettings", "socksproxytype") == "none"
        ):
            # python doesn't like bind + INADDR_ANY?
            # host = socket.INADDR_ANY
            host = config.get("network", "bind")
        return host

    def startListening(self, bind=None):
        """Open a listening socket and start accepting connections on it"""
        if bind is None:
            bind = self.getListeningIP()
        port = config.safeGetInt("bitmessagesettings", "port")
        # correct port even if it changed
        ls = TCPServer(host=bind, port=port)
        self.listeningSockets[ls.destination] = ls

    def startUDPSocket(self, bind=None):
        """
        Open an UDP socket. Depending on settings, it can either only
        accept incoming UDP packets, or also be able to send them.
        """
        if bind is None:
            host = self.getListeningIP()
            udpSocket = UDPSocket(host=host, announcing=True)
        else:
            if bind is False:
                udpSocket = UDPSocket(announcing=False)
            else:
                udpSocket = UDPSocket(host=bind, announcing=True)
        self.udpSockets[udpSocket.listening.host] = udpSocket

    def startBootstrappers(self):
        """Run the process of resolving bootstrap hostnames"""
        proxy_type = config.safeGet("bitmessagesettings", "socksproxytype")
        # A plugins may be added here
        hostname = None
        if not proxy_type or proxy_type == "none":
            connection_base = TCPConnection
        elif proxy_type == "SOCKS5":
            connection_base = Socks5BMConnection
            hostname = random.choice(["quzwelsuziwqgpt2.onion", None])
        elif proxy_type == "SOCKS4a":
            connection_base = Socks4aBMConnection  # FIXME: I cannot test
        else:
            # This should never happen because socksproxytype setting
            # is handled in bitmessagemain before starting the connectionpool
            return

        bootstrapper = bootstrap(connection_base)
        if not hostname:
            port = random.choice([8080, 8444])
            hostname = "bootstrap%s.bitmessage.org" % port
        else:
            port = 8444
        try:
            self.addConnection(bootstrapper(hostname, port))
        except socket.error as e:
            logger.debug("Bootstrap connection failed: %s", e)

    def loop(self):
        """Main Connectionpool's loop"""

        # defaults to empty loop if outbound connections are maxed
        spawnConnections = False
        acceptConnections = True
        if config.safeGetBoolean("bitmessagesettings", "dontconnect"):
            acceptConnections = False
        elif config.safeGetBoolean("bitmessagesettings", "sendoutgoingconnections"):
            spawnConnections = True
        socksproxytype = config.safeGet("bitmessagesettings", "socksproxytype", "")
        onionsocksproxytype = config.safeGet(
            "bitmessagesettings", "onionsocksproxytype", ""
        )
        if (
            socksproxytype[:5] == "SOCKS"
            and not config.safeGetBoolean("bitmessagesettings", "sockslisten")
            and ".onion"
            not in config.safeGet("bitmessagesettings", "onionhostname", "")
        ):
            acceptConnections = False

        if spawnConnections:
            if not knownnodes.knownNodesActual:
                self.startBootstrappers()
                knownnodes.knownNodesActual = True
            if not self._bootstrapped:
                self._bootstrapped = True
                Proxy.proxy = (
                    config.safeGet("bitmessagesettings", "sockshostname"),
                    config.safeGetInt("bitmessagesettings", "socksport"),
                )
                # TODO AUTH
                # TODO reset based on GUI settings changes
                try:
                    if not onionsocksproxytype.startswith("SOCKS"):
                        raise ValueError
                    Proxy.onion_proxy = (
                        config.safeGet("network", "onionsockshostname", None),
                        config.safeGet("network", "onionsocksport", None),
                    )
                except ValueError:
                    Proxy.onion_proxy = None
            established = sum(
                1
                for c in self.outboundConnections.values()
                if (c.connected and c.fullyEstablished)
            )
            pending = len(self.outboundConnections) - established
            if established < config.safeGetInt(
                "bitmessagesettings", "maxoutboundconnections"
            ):
                # Rate limit connection attempts (2s default)
                spawn_delay = 2
                if time.time() - self._lastSpawned < spawn_delay:
                    return

                # Skip connection loop entirely if trustedPeer already connected
                if self.trustedPeer and self.trustedPeer in self.outboundConnections:
                    pass  # Already connected to trustedPeer, skip loop
                else:
                    if self.trustedPeer:
                        pass
                        # Debug why it wasn't found in outboundConnections
                        # print(f">>> TRUSTEDPEER NOT FOUND OUTBOUND: peer={self.trustedPeer} id={id(self.trustedPeer)}")
                        # print(f">>> OUTBOUND KEYS: {[str(k) + ' id=' + str(id(k)) for k in self.outboundConnections.keys()]}")

                    # If trustedPeer is set, still try to connect to others if we have slots
                    loop_range = state.maximumNumberOfHalfOpenConnections - pending
                    for i in range(loop_range):
                        try:
                            chosen = self.trustedPeer or chooseConnection(
                                random.choice(self.streams)
                            )
                        except ValueError:
                            continue

                        # print(f">>> CONNECTION LOOP: trying {chosen.host}:{chosen.port}, "
                        #       f"trustedPeer={self.trustedPeer is not None}, "
                        #       f"outbound={chosen in self.outboundConnections}")
                        if chosen in self.outboundConnections:
                            continue
                        if chosen.host in self.inboundConnections:
                            continue
                        # don't connect to self
                        if chosen in state.ownAddresses:
                            continue
                        # don't connect to the hosts from the same
                        # network group, defense against sibyl attacks
                        host_network_group = protocol.network_group(chosen.host)
                        same_group = False
                        for j in self.outboundConnections.values():
                            if host_network_group == j.network_group:
                                same_group = True
                                if chosen.host == j.destination.host:
                                    knownnodes.decreaseRating(chosen)
                                break
                        if same_group:
                            continue

                        try:
                            logger.info('CONNECTING to %s:%i (trustedPeer=%s)',
                                        chosen.host, chosen.port, self.trustedPeer is not None)
                            if chosen.host.endswith(".onion") and Proxy.onion_proxy:
                                if onionsocksproxytype == "SOCKS5":
                                    self.addConnection(Socks5BMConnection(chosen))
                                elif onionsocksproxytype == "SOCKS4a":
                                    self.addConnection(Socks4aBMConnection(chosen))
                            elif socksproxytype == "SOCKS5":
                                self.addConnection(Socks5BMConnection(chosen))
                            elif socksproxytype == "SOCKS4a":
                                self.addConnection(Socks4aBMConnection(chosen))
                            else:
                                self.addConnection(TCPConnection(chosen))
                            # If trustedPeer, only make one connection attempt
                            if self.trustedPeer:
                                logger.info('trustedPeer connection initiated, breaking loop')
                                self._lastSpawned = time.time()
                                break
                        except socket.error as e:
                            if e.errno == errno.ENETUNREACH:
                                continue

                        self._lastSpawned = time.time()
        else:
            for i in self.outboundConnections.values():
                # FIXME: rating will be increased after next connection
                i.handle_close()

        if acceptConnections:
            if not self.listeningSockets:
                if config.safeGet("network", "bind") == "":
                    self.startListening()
                else:
                    for bind in re.sub(
                        r"[^\w.]+", " ", config.safeGet("network", "bind")
                    ).split():
                        self.startListening(bind)
                logger.info("Listening for incoming connections.")
            if not self.udpSockets:
                if config.safeGet("network", "bind") == "":
                    self.startUDPSocket()
                else:
                    for bind in re.sub(
                        r"[^\w.]+", " ", config.safeGet("network", "bind")
                    ).split():
                        self.startUDPSocket(bind)
                    self.startUDPSocket(False)
                logger.info("Starting UDP socket(s).")
        else:
            if self.listeningSockets:
                for i in self.listeningSockets.values():
                    i.close_reason = "Stopping listening"
                    i.accepting = i.connecting = i.connected = False
                logger.info("Stopped listening for incoming connections.")
            if self.udpSockets:
                for i in self.udpSockets.values():
                    i.close_reason = "Stopping UDP socket"
                    i.accepting = i.connecting = i.connected = False
                logger.info("Stopped udp sockets.")

        # Reference implementation: use _spawnWait as base timeout, 2.0 if enough time has passed
        loopTime = float(self._spawnWait)
        if self._lastSpawned < time.time() - self._spawnWait:
            loopTime = 2.0
        # print(f"DEBUG: ConnectionPool using asyncore map id: {id(asyncore.socket_map)} len: {len(asyncore.socket_map)}")
        try:
            # map_content = {k: type(v).__name__ for k, v in asyncore.socket_map.items()}
            # print(f"DEBUG: ConnectionPool map content: {map_content}")
            # DEBUG: Force select_poller to test if kqueue has issues on macOS
            asyncore.loop(timeout=loopTime, count=1000, poller=asyncore.select_poller)
        except BaseException as e:
            print(f"DEBUG: ASYNCORE LOOP CRASHED: {e}")
            import traceback
            traceback.print_exc()
            raise e

        reaper = []
        for i in self.connections():
            minTx = time.time() - 20
            if i.fullyEstablished:
                minTx -= 300 - 20
            if i.lastTx < minTx:
                if i.fullyEstablished:
                    i.append_write_buf(protocol.CreatePacket(b'ping'))
                else:
                    i.close_reason = "Timeout (%is)" % (time.time() - i.lastTx)
                    i.set_state("close")
        for i in (
            self.connections()
            + list(self.listeningSockets.values())
            + list(self.udpSockets.values())
        ):
            if not (i.accepting or i.connecting or i.connected):
                # print(f"DEBUG: REAPING (no state): {type(i).__name__} accepting={i.accepting} connecting={i.connecting} connected={i.connected}")
                reaper.append(i)
            else:
                try:
                    if i.state == "close":
                        # print(f"DEBUG: REAPING (state=close): {type(i).__name__}")
                        reaper.append(i)
                except AttributeError:
                    pass
        for i in reaper:
            self.removeConnection(i)


pool = BMConnectionPool()
