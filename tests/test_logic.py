import unittest
import os
import sys

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import mock_enigma
from utils import decode_html, is_path_safe

class TestPluginLogic(unittest.TestCase):
	def test_decode_html(self):
		self.assertEqual(decode_html(b"test"), "test")
		self.assertEqual(decode_html("test"), "test")
		self.assertEqual(decode_html("zażółć gęślą jaźń".encode('utf-8')), "zażółć gęślą jaźń")

	def test_is_path_safe(self):
		# Test base path
		base = "/tmp/test_extract"
		if not os.path.exists(base):
			os.makedirs(base)

		self.assertTrue(is_path_safe(base, os.path.join(base, "file.txt")))
		self.assertTrue(is_path_safe(base, os.path.join(base, "subdir/file.txt")))

		# Test traversal
		self.assertFalse(is_path_safe(base, os.path.join(base, "../traversal.txt")))
		self.assertFalse(is_path_safe(base, "/etc/passwd"))

		# Test allowed paths for root base
		self.assertTrue(is_path_safe("/", "/etc/enigma2/settings"))
		self.assertTrue(is_path_safe("/", "/usr/share/enigma2/skin.xml"))
		self.assertFalse(is_path_safe("/", "/root/.ssh/authorized_keys"))

		import shutil
		shutil.rmtree(base)

if __name__ == '__main__':
	unittest.main()
