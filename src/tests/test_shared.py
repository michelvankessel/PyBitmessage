"""Test cases for shared.py"""

import unittest
from binascii import unhexlify

from pybitmessage.highlevelcrypto import encodeWalletImportFormat
from pybitmessage.shared import (
    config,
    isAddressInMyAddressBook,
    isAddressInMySubscriptionsList,
    checkSensitiveFilePermissions,
    reloadBroadcastSendersForWhichImWatching,
    reloadMyAddressHashes,
    fixSensitiveFilePermissions,
    myAddressesByHash,
    myAddressesByTag,
    myECCryptorObjects,
    MyECSubscriptionCryptorObjects,
    stat,
    os,
)

from .samples import (
    sample_address, sample_privencryptionkey, sample_ripe,
    sample_subscription_addresses, sample_subscription_tag
)

from unittest.mock import patch, PropertyMock

# mock os.stat data for file
PERMISSION_MODE1 = stat.S_IRUSR  # allow Read permission for the file owner.
PERMISSION_MODE2 = (
    stat.S_IRWXO
)  # allow read, write, serach & execute permission for other users
INODE = 753
DEV = 1795
NLINK = 1
UID = 1000
GID = 0
SIZE = 1021
ATIME = 1711587560
MTIME = 1709449249
CTIME = 1709449603


class TestShared(unittest.TestCase):
    """Test class for shared.py"""

    def setUp(self):
        """Clear global state before each test"""
        myAddressesByHash.clear()
        myAddressesByTag.clear()
        myECCryptorObjects.clear()
        MyECSubscriptionCryptorObjects.clear()

    @patch("pybitmessage.shared.sqlQuery")
    def test_isaddress_in_myaddressbook(self, mock_sql_query):
        """Test if address is in MyAddressbook"""
        address = sample_address

        # if address is in MyAddressbook
        mock_sql_query.return_value = [address]
        return_val = isAddressInMyAddressBook(address)
        mock_sql_query.assert_called_once()
        self.assertTrue(return_val)

        # if address is not in MyAddressbook
        mock_sql_query.return_value = []
        return_val = isAddressInMyAddressBook(address)
        self.assertFalse(return_val)
        self.assertEqual(mock_sql_query.call_count, 2)

    @patch("pybitmessage.shared.sqlQuery")
    def test_isaddress_in_mysubscriptionslist(self, mock_sql_query):
        """Test if address is in MySubscriptionsList"""

        address = sample_address

        # if address is in MySubscriptionsList
        mock_sql_query.return_value = [address]
        return_val = isAddressInMySubscriptionsList(address)
        self.assertTrue(return_val)

        # if address is not in MySubscriptionsList
        mock_sql_query.return_value = []
        return_val = isAddressInMySubscriptionsList(address)
        self.assertFalse(return_val)
        self.assertEqual(mock_sql_query.call_count, 2)

    @patch("pybitmessage.shared.sqlQuery")
    def test_reloadBroadcastSendersForWhichImWatching(self, mock_sql_query):
        """Test for reload Broadcast Senders For Which Im Watching"""
        mock_sql_query.return_value = [
            (addr.encode(),) for addr in sample_subscription_addresses + [sample_address]
        ]
        # before reload
        self.assertEqual(len(MyECSubscriptionCryptorObjects), 0)

        reloadBroadcastSendersForWhichImWatching()
        self.assertGreater(len(MyECSubscriptionCryptorObjects), 0)
        self.assertTrue(
            MyECSubscriptionCryptorObjects.get(unhexlify(sample_ripe))
        )
        self.assertTrue(
            MyECSubscriptionCryptorObjects.get(sample_subscription_tag)
        )

    @patch("pybitmessage.shared.config.sections")
    def test_reloadMyAddressHashes(self, mock_sections):
        """Test for reloadMyAddressHashes"""
        # Mock sections to return only our sample address
        mock_sections.return_value = [sample_address]

        self.assertEqual(len(myAddressesByHash), 0)
        self.assertEqual(len(myAddressesByTag), 0)

        # Clean up any existing section from previous runs
        if config.has_section(sample_address):
            config.remove_section(sample_address)
            config.save()

        try:
            config.add_section(sample_address)
            config.set(sample_address, 'enabled', 'false')
            config.set(sample_address, 'privencryptionkey', 'malformed')
            config.save()

            reloadMyAddressHashes()
            self.assertEqual(len(myAddressesByHash), 0)

            config.set(sample_address, 'enabled', 'true')
            config.save()

            reloadMyAddressHashes()
            self.assertEqual(len(myAddressesByHash), 0)

            config.set(
                sample_address, 'privencryptionkey',
                encodeWalletImportFormat(
                    unhexlify(sample_privencryptionkey))
            )  # the key is not for the sample_address, but it doesn't matter
            config.save()

            reloadMyAddressHashes()
            ripe = unhexlify(sample_ripe)
            self.assertEqual(len(myAddressesByTag), 1)
            self.assertTrue(myECCryptorObjects.get(ripe))
            self.assertEqual(myAddressesByHash[ripe], sample_address)
        finally:
            # Clean up the config section
            if config.has_section(sample_address):
                config.remove_section(sample_address)
                config.save()

    @patch("pybitmessage.shared.os.stat")
    @patch(
        "pybitmessage.shared.sys",
        new_callable=PropertyMock,
    )
    def test_check_sensitive_file_permissions(self, mock_sys, mock_os_stat):
        """Test to check file permissions"""
        fake_filename = "path/to/file"

        # test for windows system
        mock_sys.platform = "win32"
        result = checkSensitiveFilePermissions(fake_filename)
        self.assertTrue(result)

        # test for freebsd system
        mock_sys.platform = "freebsd7"
        # returning file permission mode stat.S_IRUSR
        MOCK_OS_STAT_RETURN = os.stat_result((
            PERMISSION_MODE1,  # st_mode
            INODE,             # st_ino
            DEV,               # st_dev
            NLINK,             # st_nlink
            UID,               # st_uid
            GID,               # st_gid
            SIZE,              # st_size
            ATIME,             # st_atime
            MTIME,             # st_mtime
            CTIME,             # st_ctime
        ))
        mock_os_stat.return_value = MOCK_OS_STAT_RETURN
        result = checkSensitiveFilePermissions(fake_filename)
        self.assertTrue(result)

    @patch("pybitmessage.shared.os.chmod")
    @patch("pybitmessage.shared.os.stat")
    def test_fix_sensitive_file_permissions(
        self, mock_os_stat, mock_chmod
    ):
        """Test to fix file permissions"""
        fake_filename = "path/to/file"

        # returning file permission mode stat.S_IRWXO
        MOCK_OS_STAT_RETURN = os.stat_result((
            PERMISSION_MODE2,  # st_mode
            INODE,             # st_ino
            DEV,               # st_dev
            NLINK,             # st_nlink
            UID,               # st_uid
            GID,               # st_gid
            SIZE,              # st_size
            ATIME,             # st_atime
            MTIME,             # st_mtime
            CTIME,             # st_ctime
        ))
        mock_os_stat.return_value = MOCK_OS_STAT_RETURN
        fixSensitiveFilePermissions(fake_filename, False)
        mock_chmod.assert_called_once()
