# -*- coding: utf-8 -*-
import unittest
import sys
import os

# Import mocks before importing plugin/utils
import mock_enigma

# Add src to python path to import utils and plugin
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils import decode_html, is_path_safe, remove_wildcard
from plugin import ChannelListUpdateMenu

class TestLogic(unittest.TestCase):
    def test_decode_html(self):
        self.assertEqual(decode_html(b"Hello World"), "Hello World")
        self.assertEqual(decode_html("Hello World"), "Hello World")
        self.assertEqual(decode_html(b"Z\xc3\xb3\xc5\x82\xc4\x87"), "Zółć")

    def test_is_path_safe_relative_to_root(self):
        # Base path is root '/'
        self.assertTrue(is_path_safe("/etc/enigma2/userbouquet.tv", "/"))
        self.assertTrue(is_path_safe("/usr/share/enigma2/picon/1_0_1_1.png", "/"))
        self.assertTrue(is_path_safe("/picon/1_0_1_1.png", "/"))
        self.assertTrue(is_path_safe("/media/usb/picon/1.png", "/"))

        # Unsafe paths
        self.assertFalse(is_path_safe("/var/volatile/tmp/evil.sh", "/"))
        self.assertFalse(is_path_safe("/tmp/evil.sh", "/"))
        self.assertFalse(is_path_safe("/bin/sh", "/"))

    def test_is_path_safe_relative_to_base(self):
        # Base path is '/tmp/chList'
        self.assertTrue(is_path_safe("/tmp/chList/list_by_djcrash-e2_1x1/lamedb", "/tmp/chList"))
        self.assertFalse(is_path_safe("/tmp/chList/../../etc/enigma2/lamedb", "/tmp/chList"))
        self.assertFalse(is_path_safe("/etc/enigma2/lamedb", "/tmp/chList"))

    def test_process_version_info(self):
        session = mock_enigma.MagicMock()
        menu = ChannelListUpdateMenu(session)

        manifest_data = (
            '[plugin]\n'
            'Version = 20240522\n'
            'File = "rango_channel_list_updater20240522.tar.gz"\n'
            'Url = "https://raw.githubusercontent.com/fullkiller/Rango_channel_list/"\n'
            'MD5 = "e271d0c9154c4ba78d6e7c0f080cc737"\n'
        )
        menu.processVersionInfo(manifest_data)

        self.assertEqual(menu.newVersion, "20240522")
        self.assertEqual(menu.newFile, "rango_channel_list_updater20240522.tar.gz")
        self.assertEqual(menu.fileUrl, "https://raw.githubusercontent.com/fullkiller/Rango_channel_list/")
        self.assertEqual(menu.MD5, "e271d0c9154c4ba78d6e7c0f080cc737")
        self.assertEqual(menu.updateurl, "https://raw.githubusercontent.com/fullkiller/Rango_channel_list//rango_channel_list_updater20240522.tar.gz")

if __name__ == '__main__':
    unittest.main()
