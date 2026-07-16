import unittest
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock environment
import mock_enigma

from utils import decode_html, is_path_safe
from plugin import ChannelListUpdateMenu

class TestLogic(unittest.TestCase):
    def test_decode_html(self):
        self.assertEqual(decode_html(b"test"), "test")
        self.assertEqual(decode_html("test"), "test")
        self.assertEqual(decode_html(b"\xc3\xb3"), "ó")

    def test_is_path_safe(self):
        # Test with base /
        self.assertTrue(is_path_safe("/", "/etc/enigma2/test.tv"))
        self.assertTrue(is_path_safe("/", "/usr/share/enigma2/test.png"))
        self.assertFalse(is_path_safe("/", "/etc/passwd"))
        self.assertFalse(is_path_safe("/", "/tmp/test"))

        # Test with other base
        self.assertTrue(is_path_safe("/tmp", "/tmp/test"))
        self.assertFalse(is_path_safe("/tmp", "/etc/enigma2"))
        self.assertFalse(is_path_safe("/tmp", "/tmp/../etc/passwd"))

    def test_process_version_info(self):
        # Create a mock session
        session = mock_enigma.MagicMock()
        screen = ChannelListUpdateMenu(session)

        data = b"Version = 20240101\nFile = test.tar.gz\nUrl = http://example.com\nMD5 = 12345"
        screen.processVersionInfo(data)

        self.assertEqual(screen.newVersion, "20240101")
        self.assertEqual(screen.newFile, "test.tar.gz")
        self.assertEqual(screen.fileUrl, "http://example.com")
        self.assertEqual(screen.MD5, "12345")
        self.assertEqual(screen.updateurl, "http://example.com/test.tar.gz")

if __name__ == '__main__':
    unittest.main()
