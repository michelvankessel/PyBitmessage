"""
SQL-related functions defined here are really pass the queries (or other SQL
commands) to :class:`.threads.sqlThread` through `sqlSubmitQueue` queue and check
or return the result got from `sqlReturnQueue`.

This is done that way because :mod:`sqlite3` is so thread-unsafe that they
won't even let you call it from different threads using your own locks.
SQLite objects can only be used from one thread.

.. note:: This actually only applies for certain deployments, and/or
   really old version of sqlite. I haven't actually seen it anywhere.
   Current versions do have support for threading and multiprocessing.
   I don't see an urgent reason to refactor this, but it should be noted
   in the comment that the problem is mostly not valid. Sadly, last time
   I checked, there is no reliable way to check whether the library is
   or isn't thread-safe.
"""

import threading

import queue


sqlSubmitQueue: queue.Queue = queue.Queue()
"""the queue for SQL"""
sqlReturnQueue: queue.Queue = queue.Queue()
"""the queue for results"""
sql_lock = threading.Lock()
""" lock to prevent queueing a new request until the previous response
    is available """
sql_available = False
"""set to True by `.threads.sqlThread` immediately upon start"""
sql_ready = threading.Event()
"""set by `.threads.sqlThread` when ready for processing (after
   initialization is done)"""
sql_timeout = 60
"""timeout for waiting for sql_ready in seconds"""


def _sql_get():
    while sql_available or not sqlReturnQueue.empty():
        try:
            return sqlReturnQueue.get(timeout=0.1)
        except queue.Empty:
            continue
    raise RuntimeError("SQL thread exited")


def sqlQuery(sql_statement, *args):
    """
    Query sqlite and return results

    :param str sql_statement: SQL statement string
    :param list args: SQL query parameters
    :rtype: list
    """
    if not sql_available:
        return []
    sql_lock.acquire()
    sqlSubmitQueue.put(sql_statement)

    if args == ():
        sqlSubmitQueue.put("")
    elif isinstance(args[0], (list, tuple)):
        sqlSubmitQueue.put(args[0])
    else:
        sqlSubmitQueue.put(args)
    try:
        queryreturn, _ = _sql_get()
    except RuntimeError:
        queryreturn = []
    sql_lock.release()

    return queryreturn


def sqlExecuteChunked(sql_statement, idCount, *args):
    """Execute chunked SQL statement to avoid argument limit"""
    # SQLITE_MAX_VARIABLE_NUMBER,
    # unfortunately getting/setting isn't exposed to python
    if not sql_available:
        return 0
    sqlExecuteChunked.chunkSize = 999

    if idCount == 0 or idCount > len(args):
        return 0

    total_row_count = 0
    with sql_lock:
        for i in range(
            len(args) - idCount,
            len(args),
            sqlExecuteChunked.chunkSize - (len(args) - idCount),
        ):
            chunk_slice = args[
                i:i + sqlExecuteChunked.chunkSize - (len(args) - idCount)
            ]
            sqlSubmitQueue.put(f"{sql_statement},{','.join('?' * len(chunk_slice))}")
            # first static args, and then iterative chunk
            sqlSubmitQueue.put(args[0:len(args) - idCount] + chunk_slice)
            try:
                ret_val = _sql_get()
            except RuntimeError:
                break
            total_row_count += ret_val[1]
        sqlSubmitQueue.put("commit")
    return total_row_count


def sqlExecute(sql_statement, *args):
    """Execute SQL statement (optionally with arguments)"""
    if not sql_available:
        return 0
    sql_lock.acquire()
    sqlSubmitQueue.put(sql_statement)

    if args == ():
        sqlSubmitQueue.put("")
    else:
        sqlSubmitQueue.put(args)
    try:
        _, rowcount = _sql_get()
    except RuntimeError:
        rowcount = 0
    sqlSubmitQueue.put("commit")
    sql_lock.release()
    return rowcount


def sqlExecuteScript(sql_statement):
    """Execute SQL script statement"""

    statements = sql_statement.split(";")
    with SqlBulkExecute() as sql:
        for q in statements:
            sql.execute(f"{q}")


def sqlStoredProcedure(procName):
    """Schedule procName to be run"""
    if not sql_available:
        return
    sql_lock.acquire()
    sqlSubmitQueue.put(procName)
    if procName == "exit":
        sqlSubmitQueue.task_done()
        sqlSubmitQueue.put("terminate")
    sql_lock.release()


class SqlBulkExecute(object):
    """This is used when you have to execute the same statement in a cycle."""

    def __enter__(self):
        sql_lock.acquire()
        return self

    def __exit__(self, exc_type, value, traceback):
        sqlSubmitQueue.put("commit")
        sql_lock.release()

    @staticmethod
    def execute(sql_statement, *args):
        """Used for statements that do not return results."""
        if not sql_available:
            return
        sqlSubmitQueue.put(sql_statement)

        if args == ():
            sqlSubmitQueue.put("")
        else:
            sqlSubmitQueue.put(args)
        try:
            _sql_get()
        except RuntimeError:
            pass
