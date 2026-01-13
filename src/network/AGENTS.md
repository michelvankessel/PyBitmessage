# NETWORK LAYER KNOWLEDGE BASE

**Generated:** 2026-01-13
**Status:** Phase 5B Pending (Thread Safety Audit)

## OVERVIEW
P2P protocol implementation managing peer connections, message routing, and privacy features through Dandelion++ anonymous routing.

## STRUCTURE
```
src/network/
├── bmproto.py           # Core protocol: message encoding/decoding, handshake state machine
├── connectionpool.py    # Connection lifecycle: BMConnectionPool manages inbound/outbound pools
├── addrthread.py        # Peer discovery: address gossip protocol for network propagation
├── invthread.py         # Inventory sync: Dandelion++ routing for privacy-preserving broadcasts
├── dandelion.py         # Privacy protocol: stem/fluff phases prevent timing analysis
├── objectracker.py      # Inventory tracking: manages object requests and availability
├── advanceddispatcher.py # Thread-safe asyncore with connection buffering
├── tcp.py               # Transport layer: SOCKS4a/5 proxy support, TLS integration
├── knownnodes.py        # Peer database: node persistence with rating system
└── *thread.py           # Specialized workers: download, upload, announce, receive
```

## WHERE TO LOOK
| P2P Task | Critical File | Key Classes/Methods |
|----------|---------------|---------------------|
| **Connection Handshake** | `bmproto.py` | `BMProto._command_version()`, `_command_verack()` |
| **Peer Selection** | `connectionpool.py` | `BMConnectionPool.chooseConnection()` |
| **Message Broadcasting** | `invthread.py` | `InvThread.run()` with Dandelion++ routing |
| **Privacy Routing** | `dandelion.py` | `DandelionStemManager`, `DandelionFluffMapping` |
| **Inventory Tracking** | `objectracker.py` | `ObjectTracker.hasObject()`, `ObjectTracker.returns()` |
| **Async Event Loop** | `advanceddispatcher.py` | `AdvancedDispatcher.handle_write()` |
| **Proxy Connections** | `tcp.py` | `TCPConnection.connectThroughProxy()` |

## CONVENTIONS
- **Connection States**: `unconnected` → `connected` → `established` → `active` → `shutdown`
- **Thread Safety**: Use `threading.local()` for per-thread state, module locks for shared data
- **Message Validation**: Validate all incoming protocol messages before processing
- **Stream Handling**: Default stream=1, but NEVER hardcode - always use config
- **Proxy Chain**: Support SOCKS4a → SOCKS5 → HTTP CONNECT cascading

## ANTI-PATTERNS (NETWORK LAYER)
- **FIXME**: cannot test Socks4a (connectionpool.py:220) - infrastructure gap
- **FIXME**: init with queue (addrthread.py:10) - circular import on startup
- **FIXME**: check against complete list (bmproto.py:542) - incomplete message validation
- **FIXME**: maybe 28 days? (knownnodes.py:112) - arbitrary peer timeout
- **TODO**: AUTH implementation (connectionpool.py:269) - missing peer authentication
- **CRITICAL**: Thread-unsafe inventory access in `ObjectTracker` - needs Phase 5B audit

## THREAD SAFETY (Phase 5B Priority)
```python
# Pattern: Thread-local inventory tracking
import threading
local = threading.local()

def get_thread_inventory():
    if not hasattr(local, 'inventory'):
        local.inventory = set()
    return local.inventory

# Pattern: Connection pool locking
with self.connectionPoolLock:
    # Critical section: modify connection pools
    self.inboundConnections.pop(peer, None)
```

## P2P CONNECTION LIFECYCLE
1. **Discovery**: `chooseConnection()` selects from `knownnodes` or bootstrap
2. **TCP Handshake**: `TCPConnection` establishes with optional proxy chain
3. **Protocol Handshake**: `BMProto` exchanges version, services, nonce
4. **Address Exchange**: `AddrThread` broadcasts peer addresses via gossip
5. **Inventory Sync**: `InvThread` announces available objects with Dandelion++
6. **Object Transfer**: `DownloadThread`/`UploadThread` handle data exchange
7. **Maintenance**: Connection pool enforces limits, handles disconnections

## DANDELION++ PRIVACY
- **Stem Phase**: Route through single relay for anonymity
- **Fluff Phase**: Broadcast after random delay
- **Mapping**: `DandelionFluffMapping` tracks stem sources
- **Failover**: Automatic fluff on stem failure

## NETWORK COMMANDS
```bash
# Test P2P protocol
uv run pytest src/tests/test_protocol.py -v

# Monitor connections
tail -f debug.log | grep -E "(connection|peer|network)"

# Check network stats
grep "connection count" debug.log | tail -20
```