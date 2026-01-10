# PyBitmessage Network Agent Guidelines

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10

## Overview

PyBitmessage P2P networking - connection management, protocol handshake, address distribution, inventory synchronization. Handles peer discovery, connection lifecycle, and Bitmessage protocol message encoding/decoding.

## Structure

```
./src/network/
├── connectionpool.py     # Connection management, peer selection, pool lifecycle
├── bmproto.py           # Protocol message encoding/decoding, handshake logic
├── addrthread.py        # Address discovery/gossip, peer broadcasting
├── knownnodes.py        # Peer database management, node persistence
├── connectionchooser.py # Peer selection strategy, connection decisions
├── node.py              # Peer/Node named tuples, network identity
├── tcp.py               # TCP connections, SOCKS proxy support
├── udp.py               # UDP socket handling
├── tls.py               # TLS encryption for connections
├── proxy.py             # Proxy abstraction layer
├── socks4a.py           # SOCKS4a proxy implementation
├── socks5.py            # SOCKS5 proxy implementation
├── objectracker.py      # Inventory tracking, object requests
├── invthread.py         # Inventory broadcasting
├── downloadthread.py    # Object download management
├── uploadthread.py      # Object upload management
├── announcethread.py    # Self-announcement broadcasting
├── dandelion.py         # Dandelion++ privacy protocol
├── asyncore_pollchoose.py # Async networking core
├── advanceddispatcher.py # Enhanced asyncore dispatcher
├── networkthread.py     # Main network thread coordination
├── threads.py           # Thread base classes
├── multiqueue.py        # Queue management utilities
├── stats.py             # Network statistics
├── http*.py             # HTTP server components
└── __init__.py          # Network module exports
```

## Commands

```bash
# Test network components
PYTHONPATH=src python3.13 -m unittest pybitmessage.tests.test_protocol
PYTHONPATH=src python3.13 -m unittest pybitmessage.tests.test_network

# Monitor network activity
tail -f debug.log | grep -i network
```

## Conventions

- **Connection State**: `unconnected` → `connected` → `established` → `active`
- **Peer Rating**: -1.0 to 1.0, auto-decay over time
- **Stream Numbers**: 1-3 for main network, higher for custom streams
- **Protocol Version**: Handshake negotiation, backward compatibility
- **Proxy Support**: SOCKS4a, SOCKS5, HTTP CONNECT

## Anti-Patterns (This Module)

- **FIXME**: cannot test Socks4a (connectionpool.py:220) - needs test infrastructure
- **FIXME**: init with queue (addrthread.py:10) - circular import issue
- **FIXME**: check against complete list (bmproto.py:542) - incomplete validation
- **FIXME**: maybe 28 days? (knownnodes.py:112) - arbitrary timeout value
- **type: ignore** on Peer assignment (knownnodes.py:19) - mypy workaround
- **TODO**: AUTH implementation (connectionpool.py:269) - authentication missing
- **TODO**: reset GUI settings (connectionpool.py:270) - dynamic config updates

## Connection Lifecycle

1. **Discovery**: chooseConnection() selects peer from knownnodes or discovered
2. **Handshake**: bmproto.py handles version exchange, capabilities
3. **Address Exchange**: addrthread.py broadcasts peer addresses
4. **Inventory Sync**: invthread.py exchanges object inventories
5. **Object Transfer**: downloadthread.py/uploadthread.py handle data
6. **Maintenance**: Connection pool manages disconnections, retries

## Where to Look

| Task | Location |
|------|----------|
| Connection management | `connectionpool.py` - BMConnectionPool class |
| Protocol messages | `bmproto.py` - BMProto class, message handlers |
| Peer discovery | `addrthread.py` - AddrThread, address gossip |
| Peer database | `knownnodes.py` - node persistence, ratings |
| Connection selection | `connectionchooser.py` - chooseConnection() |
| Network identity | `node.py` - Peer/Node named tuples |
| Proxy support | `tcp.py`, `socks*.py` - proxy implementations |
| Inventory tracking | `objectracker.py` - ObjectTracker class |
| Privacy features | `dandelion.py` - Dandelion++ implementation |

## Known Issues

- SOCKS4a testing blocked by infrastructure limitations
- Address queue initialization has circular dependency
- Peer rating system needs refinement (arbitrary timeouts)
- Authentication mechanism not implemented
- GUI configuration changes don't reset network state