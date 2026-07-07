import unittest
import os
import sys
from tests import mock_enigma
from src.usr.lib.enigma2.python.Plugins.Extensions.RangoPolishChannelsUpdater.utils import decode_html, is_path_safe

class DummyScreen:
    def __init__(self, *args, **kwargs):
        self.widgets = {}
    def __setitem__(self, key, value):
        self.widgets[key] = value
    def __getitem__(self, key):
        return self.widgets[key]

# Force Screen to be DummyScreen
mock_enigma.sys.modules['Screens.Screen'].Screen = DummyScreen

class TestLogic(unittest.TestCase):
    def test_decode_html(self):
        self.assertEqual(decode_html(b"test"), "test")
        self.assertEqual(decode_html(b"za\xc3\xb3\xc5\xbc"), "zaóż")

    def test_is_path_safe(self):
        self.assertTrue(is_path_safe("/tmp", "/tmp/file"))
        self.assertFalse(is_path_safe("/tmp", "/etc/passwd"))
        self.assertTrue(is_path_safe("/", "/etc/enigma2/settings", allowed_paths=["/etc/enigma2/"]))
        self.assertFalse(is_path_safe("/", "/etc/passwd"))

    def test_processVersionInfo(self):
        from src.usr.lib.enigma2.python.Plugins.Extensions.RangoPolishChannelsUpdater.plugin import ChannelListUpdateMenu

        # Now ChannelListUpdateMenu inherits from DummyScreen due to mock
        menu = ChannelListUpdateMenu.__new__(ChannelListUpdateMenu)
        data = b"Version = 20240522\nFile = file.tar.gz\nUrl = http://test.com\nMD5 = hash"
        menu.processVersionInfo(data)

        self.assertEqual(menu.newVersion, "20240522")
        self.assertEqual(menu.newFile, "file.tar.gz")
        self.assertEqual(menu.fileUrl, "http://test.com")
        self.assertEqual(menu.MD5, "hash")
        self.assertEqual(menu.updateurl, "http://test.com/file.tar.gz")

if __name__ == '__main__':
    unittest.main()
