import unittest
import os
import sys

# Add src and tests to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Mock enigma before importing anything from src
import mock_enigma

from utils import decode_html, is_path_safe
from plugin import ChannelListUpdateMenu

class TestLogic(unittest.TestCase):
    def test_decode_html(self):
        self.assertEqual(decode_html(b"test"), "test")
        self.assertEqual(decode_html("test"), "test")
        self.assertEqual(decode_html(b"test\xff"), "test\ufffd")

    def test_is_path_safe(self):
        # Base is /etc/enigma2/
        self.assertTrue(is_path_safe('/etc/enigma2/', 'userbouquet.tv'))
        self.assertFalse(is_path_safe('/etc/enigma2/', '../passwd'))

        # Base is / (root extraction)
        self.assertTrue(is_path_safe('/', 'etc/enigma2/userbouquet.tv'))
        self.assertTrue(is_path_safe('/', 'usr/share/enigma2/skin.xml'))
        self.assertFalse(is_path_safe('/', 'etc/passwd'))
        self.assertFalse(is_path_safe('/', '../etc/passwd'))

    def test_process_version_info(self):
        # Mocking session for ChannelListUpdateMenu
        session = mock_enigma.MagicMock()
        menu = ChannelListUpdateMenu(session)

        data = b'Version = 20240522\nFile = test.tar.gz\nUrl = http://example.com\nMD5 = abc'
        menu.processVersionInfo(data)

        self.assertEqual(menu.newVersion, "20240522")
        self.assertEqual(menu.newFile, "test.tar.gz")
        self.assertEqual(menu.fileUrl, "http://example.com")
        self.assertEqual(menu.MD5, "abc")
        self.assertEqual(menu.updateurl, "http://example.com/test.tar.gz")

if __name__ == '__main__':
    unittest.main()
