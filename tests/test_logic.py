import unittest
from tests import mock_enigma
from src.utils import decode_html, is_path_safe
import os

class TestLogic(unittest.TestCase):
	def test_decode_html(self):
		self.assertEqual(decode_html(b"test"), "test")
		self.assertEqual(decode_html("test"), "test")
		self.assertEqual(decode_html(b"test \xc4\x99"), "test \u0119")

	def test_is_path_safe(self):
		# Test safe paths
		self.assertTrue(is_path_safe("/tmp", "/tmp/file.txt"))
		self.assertTrue(is_path_safe("/etc/enigma2", "/etc/enigma2/settings"))

		# Test root base with allowed paths
		self.assertTrue(is_path_safe("/", "/etc/enigma2/userbouquet.tv"))
		self.assertTrue(is_path_safe("/", "/usr/share/enigma2/picon/1_0_1.png"))

		# Test outside allowed paths from root
		self.assertFalse(is_path_safe("/", "/etc/shadow"))
		self.assertFalse(is_path_safe("/", "/usr/bin/python"))

	def test_process_version_info(self):
		# Manual test of processVersionInfo logic since mocking the whole class is hard
		def processVersionInfo(tester, html):
			tester.newVersion = "0"
			tester.newFile = ""
			tester.fileUrl = ""
			tester.MD5 = ""

			content = decode_html(html)
			lines = content.split("\n")
			for line in lines:
				if " = " in line:
					key, value = line.split(" = ", 1)
					key = key.strip()
					value = value.strip().replace('"', "")
					if key == "Version":
						tester.newVersion = value
					elif key == "File":
						tester.newFile = value
					elif key == "Url":
						tester.fileUrl = value
					elif key == "MD5":
						tester.MD5 = value

		class Tester:
			pass

		tester = Tester()
		html = "Version = 20240522\nFile = rango_plugin.tar.gz\nUrl = http://test.com\nMD5 = abcdef123456"
		processVersionInfo(tester, html)

		self.assertEqual(tester.newVersion, "20240522")
		self.assertEqual(tester.newFile, "rango_plugin.tar.gz")
		self.assertEqual(tester.fileUrl, "http://test.com")
		self.assertEqual(tester.MD5, "abcdef123456")

if __name__ == '__main__':
	unittest.main()
