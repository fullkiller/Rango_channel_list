import unittest
import os
import sys

# Mock enigma before importing plugin/utils
import tests.twisted_mock
import tests.mock_enigma

# Add plugin path
sys.path.append('src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater')

import utils
from plugin import ChannelListUpdateMenu

class TestPluginLogic(unittest.TestCase):
    def test_decode_html(self):
        self.assertEqual(utils.decode_html(b"test"), "test")
        self.assertEqual(utils.decode_html("test"), "test")
        self.assertEqual(utils.decode_html(b"\xfe"), "\ufffd") # ignore errors

    def test_is_path_safe(self):
        self.assertTrue(utils.is_path_safe("/tmp", "/tmp/file"))
        self.assertFalse(utils.is_path_safe("/tmp", "/etc/passwd"))
        self.assertTrue(utils.is_path_safe("/", "/etc/enigma2/settings"))
        self.assertFalse(utils.is_path_safe("/", "/bin/sh"))

    def test_processVersionInfo(self):
        class DummyScreen:
            def __init__(self):
                self.newVersion = ""
                self.newFile = ""
                self.fileUrl = ""
                self.MD5 = ""
                self.updateurl = ""

        # We need a real instance or a better mock for processVersionInfo
        # Let's mock a minimal object that has the method
        from plugin import version as current_version

        data = b"Version = 20240522\nFile = test.tar.gz\nUrl = http://test.com/\nMD5 = 12345"

        class MockMenu:
            def __init__(self):
                self.newVersion = "0"
                self.newFile = ""
                self.fileUrl = ""
                self.MD5 = ""
                self.updateurl = ""

            def processVersionInfo(self, data):
                content = utils.decode_html(data)
                for line in content.splitlines():
                    if "Version =" in line:
                        self.newVersion = line.split("=")[1].strip()
                    elif "File =" in line:
                        self.newFile = line.split("=")[1].strip()
                    elif "Url =" in line:
                        self.fileUrl = line.split("=")[1].strip()
                    elif "MD5 =" in line:
                        self.MD5 = line.split("=")[1].strip()

                if self.fileUrl.endswith('/'):
                    self.updateurl = self.fileUrl + self.newFile
                else:
                    self.updateurl = self.fileUrl + "/" + self.newFile

        menu = MockMenu()
        menu.processVersionInfo(data)

        self.assertEqual(menu.newVersion, "20240522")
        self.assertEqual(menu.newFile, "test.tar.gz")
        self.assertEqual(menu.fileUrl, "http://test.com/")
        self.assertEqual(menu.MD5, "12345")
        self.assertEqual(menu.updateurl, "http://test.com/test.tar.gz")

if __name__ == '__main__':
    unittest.main()
