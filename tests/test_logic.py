import unittest
import os
import sys

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock enigma before importing utils & plugin
import mock_enigma

from utils import is_path_safe, decode_html, CommonChannelListScreen
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
        self.assertTrue(is_path_safe('/', '/picon/picon.png'))
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
        menu = ChannelListUpdateMenu(session=None)
        version_data = 'Version = 20221219\nFile = test.tar.gz\nUrl = https://example.com/dir/\nMD5 = 12345678901234567890123456789012'
        menu.processVersionInfo(version_data)
        self.assertEqual(menu.newVersion, '20221219')
        self.assertEqual(menu.newFile, 'test.tar.gz')
        self.assertEqual(menu.fileUrl, 'https://example.com/dir/')
        self.assertEqual(menu.MD5, '12345678901234567890123456789012')
        self.assertEqual(menu.updateurl, 'https://example.com/dir/test.tar.gz')

    def test_common_channel_list_screen_version_callback(self):
        screen = CommonChannelListScreen(session=None)
        screen.versionInfoCallBack('version: 20221219\nurl: http://example.com/list.tgz', ltype="1x")
        self.assertEqual(screen.canDownload, 1)
        self.assertEqual(screen.url1x, 'http://example.com/list.tgz')

if __name__ == '__main__':
    unittest.main()
