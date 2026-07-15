# -*- coding: utf-8 -*-
import unittest
import os
import sys

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import mock environment
import mock_enigma

from utils import decode_html, is_path_safe

class TestLogic(unittest.TestCase):

    def test_decode_html(self):
        self.assertEqual(decode_html(b"test"), "test")
        self.assertEqual(decode_html("test"), "test")
        self.assertEqual(decode_html(b"\xc4\x85"), "ą")

    def test_is_path_safe(self):
        self.assertTrue(is_path_safe("/", "/etc/enigma2/settings"))
        self.assertTrue(is_path_safe("/", "/usr/share/enigma2/picon"))
        self.assertFalse(is_path_safe("/", "/tmp/evil"))
        self.assertTrue(is_path_safe("/tmp/test", "/tmp/test/file"))
        self.assertFalse(is_path_safe("/tmp/test", "/tmp/evil"))
        self.assertFalse(is_path_safe("/tmp/test", "/tmp/test/../evil"))

if __name__ == '__main__':
    unittest.main()
