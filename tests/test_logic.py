# -*- coding: utf-8 -*-
import unittest
import os
import sys

# Add src and tests to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import mock_enigma
from src.utils import is_path_safe, decode_html
from src.plugin import ChannelListUpdateMenu

class TestLogic(unittest.TestCase):
	def test_is_path_safe(self):
		# Test safe paths
		self.assertTrue(is_path_safe("/etc/enigma2", "/etc/enigma2/userbouquet.tv"))
		self.assertTrue(is_path_safe("/", "/etc/enigma2/userbouquet.tv"))
		self.assertTrue(is_path_safe("/", "/tmp/test.tar.gz"))

		# Test unsafe paths
		self.assertFalse(is_path_safe("/etc/enigma2", "/usr/bin/bash"))
		# Since is_path_safe uses abspath, let's test traversal
		self.assertFalse(is_path_safe("/etc/enigma2", "/etc/enigma2/../../usr/bin/bash"))

	def test_decode_html(self):
		self.assertEqual(decode_html(b"test"), "test")
		self.assertEqual(decode_html("test"), "test")
		self.assertEqual(decode_html(b"za\xc5\xbc\xc3\xb3\xc5\x82\xc4\x87"), "zażółć")

	def test_process_version_info(self):
		# Mocking session for ChannelListUpdateMenu
		session = mock_enigma.MagicMock()
		menu = ChannelListUpdateMenu(session)

		data = b'Version = 20240522\nFile = "rango.tar.gz"\nUrl = http://test.com\nMD5 = abc'
		menu.processVersionInfo(data)

		self.assertEqual(menu.newVersion, "20240522")
		self.assertEqual(menu.newFile, "rango.tar.gz")
		self.assertEqual(menu.fileUrl, "http://test.com")
		self.assertEqual(menu.MD5, "abc")
		self.assertEqual(menu.updateurl, "http://test.com/rango.tar.gz")

if __name__ == '__main__':
	unittest.main()
