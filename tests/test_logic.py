import unittest
import os
import sys

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock enigma before importing utils or plugin
import mock_enigma

from utils import is_path_safe, decode_html
from plugin import ChannelListUpdateMenu

class TestLogic(unittest.TestCase):
    def test_is_path_safe(self):
        # Test basic directory containment
        self.assertTrue(is_path_safe('/tmp', '/tmp/file.txt'))
        self.assertTrue(is_path_safe('/tmp/', '/tmp/file.txt'))
        self.assertFalse(is_path_safe('/tmp', '/etc/passwd'))

        # Test path traversal attempts
        self.assertFalse(is_path_safe('/tmp', '/tmp/../etc/passwd'))

        # Test root special cases (from allowed_paths in utils.py)
        self.assertTrue(is_path_safe('/', '/etc/enigma2/bouquets.tv'))
        self.assertTrue(is_path_safe('/', '/etc/enigma2'))
        self.assertTrue(is_path_safe('/', '/etc'))
        self.assertTrue(is_path_safe('/', '/picon/picon.png'))
        self.assertTrue(is_path_safe('/', '/picon'))
        self.assertFalse(is_path_safe('/', '/bin/bash'))
        self.assertFalse(is_path_safe('/', '/root/.ssh/authorized_keys'))

    def test_decode_html(self):
        # Test bytes to string
        self.assertEqual(decode_html(b'test'), 'test')
        # Test utf-8 handling
        self.assertEqual(decode_html('zażółć gęślą jaźń'.encode('utf-8')), 'zażółć gęślą jaźń')
        # Test invalid bytes (should use 'replace')
        self.assertIn('\ufffd', decode_html(b'\xff\xfe\xfd'))

    def test_process_version_info(self):
        menu = ChannelListUpdateMenu.__new__(ChannelListUpdateMenu)
        version_data = (
            "Version = 20221219\n"
            'File = "rango_channel_list_updater20221219.tar.gz"\n'
            'Url = "https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/"\n'
            'MD5 = "d41d8cd98f00b204e9800998ecf8427e"\n'
        )
        menu.processVersionInfo(version_data)
        self.assertEqual(menu.newVersion, "20221219")
        self.assertEqual(menu.newFile, "rango_channel_list_updater20221219.tar.gz")
        self.assertEqual(menu.fileUrl, "https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/")
        self.assertEqual(menu.MD5, "d41d8cd98f00b204e9800998ecf8427e")
        self.assertEqual(
            menu.updateurl,
            "https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/rango_channel_list_updater20221219.tar.gz"
        )

if __name__ == '__main__':
    unittest.main()
