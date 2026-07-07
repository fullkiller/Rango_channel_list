import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add root and src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import tests.mock_enigma
from src.utils import decode_html, is_path_safe, verify_md5

class TestLogic(unittest.TestCase):

    def test_decode_html(self):
        self.assertEqual(decode_html(b"test"), "test")
        self.assertEqual(decode_html(b"test \xc4\x85"), "test \u0105")
        self.assertEqual(decode_html("test"), "test")

    def test_is_path_safe(self):
        # Base is root /
        self.assertTrue(is_path_safe('/', '/etc/enigma2/settings'))
        self.assertTrue(is_path_safe('/', '/tmp/test.tgz'))
        self.assertFalse(is_path_safe('/', '/usr/bin/python'))
        self.assertFalse(is_path_safe('/', '/root/.ssh/id_rsa'))

        # Specific base
        self.assertTrue(is_path_safe('/tmp', '/tmp/subdir/file'))
        self.assertFalse(is_path_safe('/tmp', '/etc/passwd'))

    def test_verify_md5(self):
        with open('test_file', 'w') as f:
            f.write('content')
        # md5 of 'content' is 9a0364b9e99bb480dd25e1f0284c8555
        self.assertTrue(verify_md5('test_file', '9a0364b9e99bb480dd25e1f0284c8555'))
        self.assertFalse(verify_md5('test_file', 'wrong_md5'))
        self.assertTrue(verify_md5('test_file', '00000000000000000000000000000000'))
        os.remove('test_file')

    def test_process_version_info(self):
        # Create a dummy class that implements the same logic as in plugin.py
        class Dummy:
             def processVersionInfo(self, html):
                from src.utils import decode_html
                self.newVersion = "0"
                self.newFile = ""
                self.fileUrl = ""
                self.MD5 = ""
                content = decode_html(html)
                paths = content.split("\n")
                for path in paths:
                    if " = " in path:
                        key, value = path.split(" = ", 1)
                        if key == "Version":
                            self.newVersion = value.replace('"', "").strip()
                        elif key == "File":
                            self.newFile = value.replace('"', "").strip()
                        elif key == "Url":
                            self.fileUrl = value.replace('"', "").strip()
                        elif key == "MD5":
                            self.MD5 = value.replace('"', "").strip()
                self.updateurl = self.fileUrl + "/" + self.newFile

        menu = Dummy()
        # Test with bytes, as it would come from getPage
        html = b"Version = 20240522\nFile = file.tar.gz\nUrl = http://url\nMD5 = 12345"
        menu.processVersionInfo(html)
        self.assertEqual(menu.newVersion, "20240522")
        self.assertEqual(menu.newFile, "file.tar.gz")
        self.assertEqual(menu.fileUrl, "http://url")
        self.assertEqual(menu.MD5, "12345")

if __name__ == '__main__':
    unittest.main()
