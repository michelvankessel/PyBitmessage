"""
account.py
==========

Account related functions.
"""

import inspect
import re
import sys
import time
from typing import Optional, Dict, Union

from PyQt6 import QtWidgets

import queues
from addresses import decodeAddress
from bmconfigparser import config
from debug import logger
from helper_ackPayload import genAckPayload
from helper_sql import sqlQuery, sqlExecute
from .foldertree import AccountMixin
from .utils import str_broadcast_subscribers

# Define specific types for better type safety
AccountType = Union[
    "BMAccount",
    "BroadcastAccount",
    "SubscriptionAccount",
    "NoAccount",
    "GatewayAccount",
    "MailchuckAccount",
]

# Type for subscription data structure
SubscriptionData = Dict[
    str, Dict[str, Dict[str, Union[str, bool, int]]]
]  # address -> folder -> {label, enabled, count}


def getSortedSubscriptions(
    count: bool = False,
) -> SubscriptionData:
    """
    Actually return a grouped dictionary rather than a sorted list

    :param count: Whether to count messages for each fromaddress in the inbox
    :type count: bool, default False
    :retuns: dict keys are addresses, values are dicts containing settings
    :rtype: dict, default {}
    """
    queryreturn = sqlQuery(
        "SELECT label, address, enabled FROM subscriptions ORDER BY label COLLATE NOCASE ASC"
    )
    ret: SubscriptionData = {}
    for row in queryreturn:
        label, address, enabled = row
        if isinstance(label, bytes):
            label = label.decode("utf-8", "ignore")
        ret[address] = {}
        ret[address]["inbox"] = {}
        ret[address]["inbox"]["label"] = label
        ret[address]["inbox"]["enabled"] = enabled
        ret[address]["inbox"]["count"] = 0
    if count:
        queryreturn = sqlQuery(
            """SELECT fromaddress, folder, count(msgid) as cnt
            FROM inbox, subscriptions ON subscriptions.address = inbox.fromaddress
            WHERE read = 0 AND toaddress = ?
            GROUP BY inbox.fromaddress, folder""",
            str_broadcast_subscribers,
        )
        for row in queryreturn:
            address, folder, cnt = row
            if folder not in ret[address]:
                ret[address][folder] = {
                    "label": ret[address]["inbox"]["label"],
                    "enabled": ret[address]["inbox"]["enabled"],
                }
            ret[address][folder]["count"] = cnt
    return ret


def accountClass(address: Optional[str]) -> Optional[AccountType]:
    """Return a BMAccount for the address"""
    if address is None:
        return None
    if not config.has_section(address):
        # .. todo:: This BROADCAST section makes no sense
        subscription: AccountType
        if address == str_broadcast_subscribers:
            subscription = BroadcastAccount(address)
            if subscription.type_ != AccountMixin.BROADCAST:
                return None
        else:
            subscription = SubscriptionAccount(address)
            if subscription.type_ != AccountMixin.SUBSCRIPTION:
                # e.g. deleted chan
                return NoAccount(address)
        return subscription
    try:
        gateway = config.get(address, "gateway")
        for _, cls in inspect.getmembers(sys.modules[__name__], inspect.isclass):
            if issubclass(cls, GatewayAccount) and cls.gatewayName == gateway:
                return cls(address)
        # general gateway
        return GatewayAccount(address)
    except Exception:
        pass
    # no gateway
    return BMAccount(address)


class AccountColor(AccountMixin):
    """Set the type of account"""

    def __init__(
        self, address: Optional[str] = None, address_type: Optional[int] = None
    ) -> None:
        self.isEnabled = True
        self.address = address
        if address_type is None:
            self.setType()
        else:
            self.type_ = address_type


class BMAccount(AccountMixin):
    """Encapsulate a Bitmessage account"""

    def __init__(self, address: Optional[str] = None) -> None:
        self.address = address
        self.setType()
        self.subject: Union[str, bytes] = ""
        self.message: Union[str, bytes] = ""
        self.toAddress: str = ""
        self.fromAddress: str = ""
        self.fromLabel: str = ""
        self.toLabel: str = ""

    def getLabel(self, address: Optional[str] = None) -> str:
        """Get a label for this bitmessage account"""
        if address is None:
            address = self.address

        # Handle case where address is None
        if address is None:
            return ""

        label = config.safeGet(address, "label", address)
        queryreturn = sqlQuery(
            """select label from addressbook where address=?""", address
        )
        if queryreturn != []:
            for row in queryreturn:
                (label,) = row
                if isinstance(label, bytes):
                    label = label.decode('utf-8', 'replace')
        else:
            queryreturn = sqlQuery(
                """select label from subscriptions where address=?""", address
            )
            if queryreturn != []:
                for row in queryreturn:
                    (label,) = row
                    if isinstance(label, bytes):
                        label = label.decode('utf-8', 'replace')
        return label if label else address

    def parseMessage(
        self,
        toAddress: str,
        fromAddress: str,
        subject: Union[str, bytes],
        message: Union[str, bytes],
    ) -> None:
        """Set metadata and address labels on self"""

        self.toAddress = toAddress
        self.fromAddress = fromAddress
        if isinstance(subject, str):
            self.subject = subject
        else:
            self.subject = subject
        self.message = message
        self.fromLabel = self.getLabel(fromAddress)
        self.toLabel = self.getLabel(toAddress)


class NoAccount(BMAccount):
    """Override the __init__ method on a BMAccount"""

    def __init__(self, address=None):
        self.address = address
        self.type_ = AccountMixin.NORMAL

    def getLabel(self, address: Optional[str] = None) -> str:
        if address is None:
            address = self.address
        return address if address else ""


class SubscriptionAccount(BMAccount):
    """Encapsulate a subscription account"""

    def setType(self) -> None:
        """Set account type"""
        self.type_ = AccountMixin.SUBSCRIPTION


class BroadcastAccount(BMAccount):
    """Encapsulate a broadcast account"""

    def setType(self) -> None:
        """Set account type"""
        self.type_ = AccountMixin.BROADCAST


class GatewayAccount(BMAccount):
    """Encapsulate a gateway account"""

    gatewayName: Optional[str] = None
    ALL_OK = 0
    REGISTRATION_DENIED = 1

    def __init__(self, address):
        super(GatewayAccount, self).__init__(address)

    def send(self):
        """Override the send method for gateway accounts"""

        result = decodeAddress(self.toAddress)
        if not result or len(result) != 4:
            logger.error("Failed to decode address. Result: %s", result)
            return  # or raise an exception
        status, version, stream, ripe = result

        stealthLevel = config.safeGetInt("bitmessagesettings", "ackstealthlevel")
        ackdata = genAckPayload(stream, stealthLevel)
        sqlExecute(
            """INSERT INTO sent VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            "",
            self.toAddress,
            ripe,
            self.fromAddress,
            self.subject,
            self.message,
            ackdata,
            int(time.time()),  # sentTime (this will never change)
            int(time.time()),  # lastActionTime
            0,  # sleepTill time. This will get set when the POW gets done.
            "msgqueued",
            0,  # retryNumber
            "sent",  # folder
            2,  # encodingtype
            # not necessary to have a TTL higher than 2 days
            min(config.getint("bitmessagesettings", "ttl"), 86400 * 2),
        )

        queues.workerQueue.put(("sendmessage", self.toAddress))

    def register(self, email):
        """Register with gateway - base implementation"""
        pass

    def unregister(self):
        """Unregister from gateway - base implementation"""
        pass

    def status(self):
        """Get gateway status - base implementation"""
        pass


class MailchuckAccount(GatewayAccount):
    """Encapsulate a particular kind of gateway account"""

    # set "gateway" in keys.dat to this
    gatewayName = "mailchuck"
    registrationAddress = "BM-2cVYYrhaY5Gbi3KqrX9Eae2NRNrkfrhCSA"
    unregistrationAddress = "BM-2cVMAHTRjZHCTPMue75XBK5Tco175DtJ9J"
    relayAddress = "BM-2cWim8aZwUNqxzjMxstnUMtVEUQJeezstf"
    regExpIncoming = re.compile(r"(.*)MAILCHUCK-FROM::(\S+) \| (.*)")
    regExpOutgoing = re.compile(r"(\S+) (.*)")

    def __init__(self, address):
        super(MailchuckAccount, self).__init__(address)
        self.feedback = self.ALL_OK

    def createMessage(
        self,
        toAddress: str,
        fromAddress: str,
        subject: Union[str, bytes],
        message: Union[str, bytes],
    ) -> None:
        """createMessage specific to a MailchuckAccount"""
        # Ensure subject is string for concatenation
        subject_str = subject.decode() if isinstance(subject, bytes) else subject

        # Type narrowing: guarantee subject is a string for concatenation
        if isinstance(subject_str, str):
            subject_final = subject_str
        elif isinstance(subject_str, (bytearray, memoryview)):
            subject_final = str(subject_str)
        else:
            # Fallback for any other type
            subject_final = str(subject_str)

        # Type assertion for Pylance guarantee
        assert isinstance(subject_final, str), (
            f"subject_final must be str, got {type(subject_final)}"
        )

        self.subject = toAddress + " " + subject_final
        self.toAddress = self.relayAddress
        self.fromAddress = fromAddress
        self.message = message

    def register(self, email):
        """register specific to a MailchuckAccount"""
        self.toAddress = self.registrationAddress
        self.subject = email
        self.message = ""
        self.fromAddress = self.address
        self.send()

    def unregister(self):
        """unregister specific to a MailchuckAccount"""
        self.toAddress = self.unregistrationAddress
        self.subject = ""
        self.message = ""
        self.fromAddress = self.address
        self.send()

    def status(self):
        """status specific to a MailchuckAccount"""
        self.toAddress = self.registrationAddress
        self.subject = "status"
        self.message = ""
        self.fromAddress = self.address
        self.send()

    def settings(self):
        """settings specific to a MailchuckAccount"""

        self.toAddress = self.registrationAddress
        self.subject = "config"
        self.message = QtWidgets.QApplication.translate(
            "Mailchuck",
            """# You can use this to configure your email gateway account
# Uncomment the setting you want to use
# Here are the options:
#
# pgp: server
# The email gateway will create and maintain PGP keys for you and sign, verify,
# encrypt and decrypt on your behalf. When you want to use PGP but are lazy,
# use this. Requires subscription.
#
# pgp: local
# The email gateway will not conduct PGP operations on your behalf. You can
# either not use PGP at all, or use it locally.
#
# attachments: yes
# Incoming attachments in the email will be uploaded to MEGA.nz, and you can
# download them from there by following the link. Requires a subscription.
#
# attachments: no
# Attachments will be ignored.
#
# archive: yes
# Your incoming emails will be archived on the server. Use this if you need
# help with debugging problems or you need a third party proof of emails. This
# however means that the operator of the service will be able to read your
# emails even after they have been delivered to you.
#
# archive: no
# Incoming emails will be deleted from the server as soon as they are relayed
# to you.
#
# masterpubkey_btc: BIP44 xpub key or electrum v1 public seed
# offset_btc: integer (defaults to 0)
# feeamount: number with up to 8 decimal places
# feecurrency: BTC, XBT, USD, EUR or GBP
# Use these if you want to charge people who send you emails. If this is on and
# an unknown person sends you an email, they will be requested to pay the fee
# specified. As this scheme uses deterministic public keys, you will receive
# the money directly. To turn it off again, set "feeamount" to 0. Requires
# subscription.
""",
        )
        self.fromAddress = self.address

    def parseMessage(
        self,
        toAddress: str,
        fromAddress: str,
        subject: Union[str, bytes],
        message: Union[str, bytes],
    ) -> None:
        """parseMessage specific to a MailchuckAccount"""

        super(MailchuckAccount, self).parseMessage(
            toAddress, fromAddress, subject, message
        )

        # Ensure subject is string for regex operations
        subject_str = subject.decode() if isinstance(subject, bytes) else subject

        # Type narrowing: guarantee subject is a string for regex operations
        if isinstance(subject_str, str):
            subject_final = subject_str
        elif isinstance(subject_str, (bytearray, memoryview)):
            subject_final = str(subject_str)
        else:
            # Fallback for any other type
            subject_final = str(subject_str)

        # Type assertion for Pylance guarantee
        assert isinstance(subject_final, str), (
            f"subject_final must be str, got {type(subject_final)}"
        )

        if fromAddress == self.relayAddress:
            matches = self.regExpIncoming.search(subject_final)
            if matches is not None:
                self.subject = ""
                if not matches.group(1) is None:
                    self.subject += matches.group(1)
                if not matches.group(3) is None:
                    self.subject += matches.group(3)
                if not matches.group(2) is not None:
                    self.fromLabel = matches.group(2)
                    self.fromAddress = matches.group(2)

        if toAddress == self.relayAddress:
            matches = self.regExpOutgoing.search(subject_final)
            if matches is not None:
                if not matches.group(2) is None:
                    self.subject = matches.group(2)
                if not matches.group(1) is None:
                    self.toLabel = matches.group(1)
                    self.toAddress = matches.group(1)
        self.feedback = self.ALL_OK
        if (
            fromAddress == self.registrationAddress
            and self.subject == "Registration Request Denied"
        ):
            self.feedback = self.REGISTRATION_DENIED
        # Return None to match parent class signature
        return None
