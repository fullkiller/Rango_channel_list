import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater')))

# Mock enigma2 environment before imports
import tests.mock_enigma

from utils import decode_html, is_path_safe, CommonChannelListScreen
from plugin import ChannelListUpdateMenu

class TestLogic(unittest.TestCase):
    def test_decode_html(self):
        self.assertEqual(decode_html(b"test"), "test")
        self.assertEqual(decode_html("test"), "test")
        self.assertEqual(decode_html(b"\xfftest"), "test") # ignore error

    def test_is_path_safe(self):
        # Base is /
        self.assertTrue(is_path_safe("/", "/etc/enigma2/userbouquet.tv"))
        self.assertTrue(is_path_safe("/", "/media/hdd/picon"))
        self.assertTrue(is_path_safe("/", "/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater/plugin.py"))
        self.assertTrue(is_path_safe("/", "/picon/test.png"))
        self.assertFalse(is_path_safe("/", "/usr/bin/bash"))
        self.assertFalse(is_path_safe("/", "/etc/shadow"))

        # Base is specific dir
        self.assertTrue(is_path_safe("/tmp/chList", "/tmp/chList/file"))
        self.assertFalse(is_path_safe("/tmp/chList", "/tmp/other"))
        self.assertFalse(is_path_safe("/tmp/chList", "/tmp/chList/../other"))

        # Test startswith bypass
        self.assertFalse(is_path_safe("/tmp/a", "/tmp/ab/file"))

    def test_processVersionInfo(self):
        session = MagicMock()
        with patch('plugin.getPage'), patch('plugin.LoadPixmap'):
            menu = ChannelListUpdateMenu(session)
            data = b"Version = 20240522\nFile = test.tar.gz\nUrl = http://test.com/\nMD5 = abc"
            menu.processVersionInfo(data)
            self.assertEqual(menu.newVersion, "20240522")
            self.assertEqual(menu.newFile, "test.tar.gz")
            self.assertEqual(menu.fileUrl, "http://test.com/")
            self.assertEqual(menu.updateurl, "http://test.com/test.tar.gz")

if __name__ == '__main__':
    unittest.main()
EOF
