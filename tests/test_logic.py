import unittest
import os
import sys

# Add src and tests to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import mock_enigma
from src.utils import decode_html, is_path_safe

class TestLogic(unittest.TestCase):
    def test_decode_html(self):
        self.assertEqual(decode_html(b"test"), "test")
        self.assertEqual(decode_html("test"), "test")
        self.assertEqual(decode_html(b"test\xff"), "test\ufffd")

    def test_is_path_safe(self):
        # Test with base as a directory
        self.assertTrue(is_path_safe("/tmp", "/tmp/file.txt"))
        self.assertTrue(is_path_safe("/tmp/", "/tmp/subdir/file.txt"))
        self.assertFalse(is_path_safe("/tmp", "/etc/passwd"))
        self.assertFalse(is_path_safe("/tmp", "/tmp/../etc/passwd"))

        # Test with base as root (special case in our implementation)
        self.assertTrue(is_path_safe("/", "/etc/enigma2/settings"))
        self.assertTrue(is_path_safe("/", "/usr/share/enigma2/skin.xml"))
        self.assertFalse(is_path_safe("/", "/etc/shadow"))

    def test_process_version_info(self):
        # Create a dummy object to test processVersionInfo
        class DummyPlugin:
            def __init__(self):
                self.list = []

            def processVersionInfo(self, html):
                content = decode_html(html)
                paths = content.split("\n")
                self.newVersion = "0"
                self.newFile = ""
                self.fileUrl = ""
                self.MD5 = ""
                for path in paths:
                    if "=" in path:
                        key, value = path.split("=", 1)
                        key = key.strip()
                        value = value.replace('"', "").strip()
                        if key == "Version":
                            self.newVersion = value
                        elif key == "File":
                            self.newFile = value
                        elif key == "Url":
                            self.fileUrl = value
                        elif key == "MD5":
                            self.MD5 = value

                self.updateurl = self.fileUrl + "/" + self.newFile

        plugin = DummyPlugin()

        html = b"Version = 20240101\nFile = update.tar.gz\nUrl = http://example.com\nMD5 = 12345"
        plugin.processVersionInfo(html)

        self.assertEqual(plugin.newVersion, "20240101")
        self.assertEqual(plugin.newFile, "update.tar.gz")
        self.assertEqual(plugin.fileUrl, "http://example.com")
        self.assertEqual(plugin.MD5, "12345")
        self.assertEqual(plugin.updateurl, "http://example.com/update.tar.gz")

if __name__ == '__main__':
    unittest.main()
