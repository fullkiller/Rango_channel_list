import unittest
import os
import sys

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock enigma before importing utils
import mock_enigma

from utils import is_path_safe, decode_html

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

if __name__ == '__main__':
    unittest.main()
