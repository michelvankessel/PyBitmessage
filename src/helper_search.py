"""
Additional SQL helper for searching messages.
Used by :mod:`.bitmessageqt`.
"""

from helper_sql import sqlQuery
from bmconfigparser import config
from tr import _translate


def search_sql(
    xAddress='toaddress', account=None, folder='inbox', where=None,
    what=None, unreadOnly=False
):
    """
    Search for messages from given account and folder having search term
    in one of it's fields.

    :param str xAddress: address field checked
      ('fromaddress', 'toaddress' or 'both')
    :param account: the account which is checked
    :type account: :class:`.bitmessageqt.account.BMAccount`
      instance
    :param str folder: the folder which is checked
    :param str where: message field which is checked ('toaddress',
      'fromaddress', 'subject' or 'message'), by default check any field
    :param str what: the search term
    :param bool unreadOnly: if True, search only for unread messages
    :return: all messages where <where> field contains <what>
    :rtype: list[list]
    """
    if what and what == "[Broadcast subscribers]":
        sqlStatementParts = []
        sqlArguments = []
        if account is not None:
            # Handle special case for 'xAddress' to ensure we capture the right sender
            # In inbox: fromAddress is sender. In sent: fromAddress is sender.
            sqlStatementParts.append('fromaddress = ? ')
            sqlArguments.append(account)
        else:
            # Prevent leaking all messages if account is missing
            sqlStatementParts.append("1=0")
        if unreadOnly:
            sqlStatementParts.append('read = 0')
        if not unreadOnly and folder == 'inbox':
            sqlStatementParts.append("folder='inbox'")

        sqlStatementBaseInbox = 'SELECT toaddress, fromaddress, subject, folder, msgid, received, read FROM inbox '
        if sqlStatementParts:
            sqlStatementBaseInbox += 'WHERE ' + ' AND '.join(sqlStatementParts)

        # Now for SENT table
        # We want to find messages SENT by us (fromaddress = account) that were sent TO [Broadcast subscribers]
        sqlStatementPartsSent = []
        sqlArgumentsSent = []
        if account is not None:
            sqlStatementPartsSent.append('fromaddress = ?')
            sqlArgumentsSent.append(account)
        else:
            sqlStatementPartsSent.append("1=0")

        sqlStatementPartsSent.append("toaddress = ?")
        sqlArgumentsSent.append(what)

        if not unreadOnly:  # Sent messages are technically "read"
            # We map SENT columns to match INBOX structure but use 'msgid' instead of 'ackdata'
            # to allow deduping.
            sqlStatementBaseSent = "SELECT toaddress, fromaddress, subject, 'sent' as folder, msgid, lastactiontime as received, 1 as read FROM sent "
            if sqlStatementPartsSent:
                sqlStatementBaseSent += 'WHERE ' + ' AND '.join(sqlStatementPartsSent)

            # Combine with GROUP BY to dedup self-sent broadcasts that are also in inbox.
            # We use MIN(read) to respect 'unread' status if present in inbox.
            # We use MIN(folder) so 'inbox' takes precedence over 'sent'.
            finalQuery = f"""
                SELECT toaddress, fromaddress, subject, MIN(folder), msgid, MAX(received) as received, MIN(read) as read
                FROM ({sqlStatementBaseInbox} UNION ALL {sqlStatementBaseSent})
                GROUP BY msgid
                ORDER BY received DESC
            """
            sqlArguments.extend(sqlArgumentsSent)
            return sqlQuery(finalQuery, sqlArguments)

    where_map = {
        _translate("MainWindow", "To"): "toaddress",
        _translate("MainWindow", "From"): "fromaddress",
        _translate("MainWindow", "Subject"): "subject",
        _translate("MainWindow", "Message"): "message",
        _translate("MainWindow", "All"): "all",
    }
    where = where_map.get(where, where)

    if what and not what.startswith("%") and not what.endswith("%"):
        what = f"%{what}%"

    # Find addresses matching the search term in the address book
    matching_addresses = []
    if where == "all" or where == "toaddress" or where == "fromaddress":
        query = "SELECT address FROM addressbook WHERE label LIKE ?"
        try:
            for row in sqlQuery(query, [what]):
                addr = row[0]
                if isinstance(addr, bytes):
                    addr = addr.decode("utf-8", "replace")
                matching_addresses.append(addr)
        except Exception as e:
            print(f"DEBUG_SEARCH: Error querying addressbook: {e}")

    # Also check local identities (Your Identities)
    if where == "all" or where == "toaddress" or where == "fromaddress":
        try:
            # Strip wildcards for Python-side string matching
            search_term = what.strip('%').lower()
            if search_term:
                for address in config.addresses():
                    label = config.get(address, 'label')
                    if label and search_term in label.lower():
                        matching_addresses.append(address)
        except Exception as e:
            print(f"DEBUG_SEARCH: Error querying identities: {e}")

    if folder == 'trash':
        # Union query for trash to handle both inbox and sent items
        # and dedup self-sent broadcasts.
        sqlStatementPartsInbox = []
        sqlArgumentsInbox = []
        if account is not None:
            if xAddress == 'both':
                sqlStatementPartsInbox.append('(fromaddress = ? OR toaddress = ?)')
                sqlArgumentsInbox.extend([account, account])
            else:
                sqlStatementPartsInbox.append(xAddress + ' = ? ')
                sqlArgumentsInbox.append(account)
        else:
            sqlStatementPartsInbox.append("1=0")

        sqlStatementPartsInbox.append("folder = 'trash'")

        if what:
            if where == "all":
                sqlStatementPartsInbox.append(
                    "(subject LIKE ? OR toaddress LIKE ? OR fromaddress LIKE ? OR message LIKE ?)"
                )
                sqlArgumentsInbox.extend([what] * 4)
            else:
                sqlStatementPartsInbox.append('%s LIKE ?' % (where))
                sqlArgumentsInbox.append(what)
        if unreadOnly:
            sqlStatementPartsInbox.append('read = 0')

        sqlStatementBaseInbox = 'SELECT toaddress, fromaddress, subject, folder, msgid, received, read FROM inbox '
        if sqlStatementPartsInbox:
            sqlStatementBaseInbox += 'WHERE ' + ' AND '.join(sqlStatementPartsInbox)

        # Sent trash
        sqlStatementPartsSent = []
        sqlArgumentsSent = []
        if account is not None:
            # For sent messages, ownership is determined by fromaddress
            sqlStatementPartsSent.append('fromaddress = ? ')
            sqlArgumentsSent.append(account)
        else:
            sqlStatementPartsSent.append("1=0")

        sqlStatementPartsSent.append("folder = 'trash'")

        if what:
            if where == "all":
                sqlStatementPartsSent.append(
                    "(subject LIKE ? OR toaddress LIKE ? OR fromaddress LIKE ? OR message LIKE ?)"
                )
                sqlArgumentsSent.extend([what] * 4)
            else:
                sqlStatementPartsSent.append('%s LIKE ?' % (where))
                sqlArgumentsSent.append(what)

        sqlStatementBaseSent = "SELECT toaddress, fromaddress, subject, 'trash' as folder, msgid, lastactiontime as received, 1 as read FROM sent "
        if sqlStatementPartsSent:
            sqlStatementBaseSent += 'WHERE ' + ' AND '.join(sqlStatementPartsSent)

        finalQuery = f"""
            SELECT toaddress, fromaddress, subject, folder, msgid, MAX(received) as received, MIN(read) as read
            FROM ({sqlStatementBaseInbox} UNION ALL {sqlStatementBaseSent})
            GROUP BY msgid
            ORDER BY received DESC
        """
        return sqlQuery(finalQuery, sqlArgumentsInbox + sqlArgumentsSent)

    print(f"DEBUG: search_sql called with what='{what}', folder='{folder}', account='{account}'")

    sqlStatementBase = 'SELECT toaddress, fromaddress, subject, ' + (
        'status, ackdata, lastactiontime FROM sent ' if folder == 'sent'
        else 'folder, msgid, received, read FROM inbox '
    )

    sqlStatementParts = []
    sqlArguments = []
    if account is not None:
        if xAddress == 'both':
            sqlStatementParts.append('(fromaddress = ? OR toaddress = ?)')
            sqlArguments.append(account)
            sqlArguments.append(account)
        else:
            sqlStatementParts.append(xAddress + ' = ? ')
            sqlArguments.append(account)
    if folder is not None and folder != 'sent':
        if folder == 'new':
            folder = 'inbox'
            unreadOnly = True
        sqlStatementParts.append('folder = ? ')
        sqlArguments.append(folder)
    else:
        sqlStatementParts.append('folder != ?')
        sqlArguments.append('trash')
    if what:
        if where == "all":
            sqlStatementParts.append(
                "(subject LIKE ? OR toaddress LIKE ? OR fromaddress LIKE ? OR message LIKE ?)"
            )
            sqlArguments.extend([what] * 4)

            # Add matching addresses from address book
            if matching_addresses:
                address_placeholders = ','.join(['?'] * len(matching_addresses))
                sqlStatementParts[-1] = sqlStatementParts[-1][:-1] + f" OR toaddress IN ({address_placeholders}) OR fromaddress IN ({address_placeholders}))"
                sqlArguments.extend(matching_addresses * 2)
        else:
            sqlStatementParts.append('%s LIKE ?' % (where))
            sqlArguments.append(what)
    if unreadOnly:
        sqlStatementParts.append('read = 0')
    if sqlStatementParts:
        sqlStatementBase += 'WHERE ' + ' AND '.join(sqlStatementParts)
    if folder == 'sent':
        sqlStatementBase += ' ORDER BY lastactiontime'
    return sqlQuery(sqlStatementBase, sqlArguments)


def check_match(
        toAddress, fromAddress, subject, message, where=None, what=None):
    """
    Check if a single message matches a filter (used when new messages
    are added to messagelists)
    """
    if not what:
        return True

    if where in (
        _translate("MainWindow", "To"), _translate("MainWindow", "All")
    ):
        if what.lower() not in toAddress.lower():
            return False
    elif where in (
        _translate("MainWindow", "From"), _translate("MainWindow", "All")
    ):
        if what.lower() not in fromAddress.lower():
            return False
    elif where in (
        _translate("MainWindow", "Subject"),
        _translate("MainWindow", "All")
    ):
        if what.lower() not in subject.lower():
            return False
    elif where in (
        _translate("MainWindow", "Message"),
        _translate("MainWindow", "All")
    ):
        if what.lower() not in message.lower():
            return False
    return True
