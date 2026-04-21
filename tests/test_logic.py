import sys
import os
import unittest
from unittest.mock import MagicMock, patch, mock_open

# Mock twisted.web.client
mock_twisted_web_client = MagicMock()
sys.modules['twisted'] = MagicMock()
sys.modules['twisted.web'] = MagicMock()
sys.modules['twisted.web.client'] = mock_twisted_web_client

# Mock Enigma2 modules
class MockScreen:
    def __init__(self, *args, **kwargs):
        self._items = {}
    def setTitle(self, *args):
        pass
    def __setitem__(self, key, value):
        self._items[key] = value
    def __getitem__(self, key):
        return self._items.get(key, MagicMock())
    def close(self):
        pass

sys.modules['enigma'] = MagicMock()
sys.modules['Components'] = MagicMock()
sys.modules['Components.Label'] = MagicMock()
sys.modules['Components.ActionMap'] = MagicMock()
sys.modules['Components.Sources'] = MagicMock()
sys.modules['Components.Sources.List'] = MagicMock()
sys.modules['Components.PluginList'] = MagicMock()
sys.modules['Components.Sources.Progress'] = MagicMock()
sys.modules['Components.Sources.StaticText'] = MagicMock()
sys.modules['Components.Language'] = MagicMock()
sys.modules['Screens'] = MagicMock()
sys.modules['Screens.Standby'] = MagicMock()
sys.modules['Screens.MessageBox'] = MagicMock()
sys.modules['Screens.Screen'] = MagicMock()
sys.modules['Screens.Screen'].Screen = MockScreen
sys.modules['Screens.InfoBar'] = MagicMock()
sys.modules['Screens.TaskView'] = MagicMock()
sys.modules['Screens.ChoiceBox'] = MagicMock()
sys.modules['Tools'] = MagicMock()
sys.modules['Tools.LoadPixmap'] = MagicMock()
sys.modules['Tools.Directories'] = MagicMock()
sys.modules['Tools.Downloader'] = MagicMock()
sys.modules['Plugins'] = MagicMock()
sys.modules['Plugins.Plugin'] = MagicMock()
sys.modules['Components.Task'] = MagicMock()

# Mock _ (gettext)
import builtins
builtins._ = lambda x: x

# Add the directory containing 'RangoPolishChannelsUpdater' to sys.path
sys.path.append(os.path.abspath('src/usr/lib/enigma2/python/Plugins/Extensions'))

# Mock the __init__.py
import RangoPolishChannelsUpdater
RangoPolishChannelsUpdater._ = lambda x: x

from RangoPolishChannelsUpdater import utils

class TestSecurityLogic(unittest.TestCase):
    def test_is_path_safe(self):
        base = "/tmp"
        self.assertTrue(utils.is_path_safe(base, "/tmp/test.txt"))
        self.assertTrue(utils.is_path_safe(base, "/tmp/dir/test.txt"))
        self.assertFalse(utils.is_path_safe(base, "/tmp/../etc/passwd"))
        self.assertFalse(utils.is_path_safe(base, "/etc/passwd"))
        self.assertTrue(utils.is_path_safe("/etc/enigma2", "/etc/enigma2/userbouquet.tv"))

    def test_safe_tar_extract_vulnerability(self):
        mock_tar = MagicMock()
        mock_member = MagicMock()
        mock_member.name = "../../etc/passwd"
        mock_tar.getmembers.return_value = [mock_member]

        with self.assertRaises(Exception) as cm:
            utils.safe_tar_extract(mock_tar, "/tmp")
        self.assertEqual(str(cm.exception), "Attempted Path Traversal in Tar File")

    def test_safe_zip_extract_vulnerability(self):
        mock_zip = MagicMock()
        mock_zip.namelist.return_value = ["../../etc/passwd"]

        with self.assertRaises(Exception) as cm:
            utils.safe_zip_extract(mock_zip, "/tmp")
        self.assertEqual(str(cm.exception), "Attempted Path Traversal in Zip File")

class TestDjcrashLogic(unittest.TestCase):
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="DATE=2024-05-22\nVER=123")
    def test_getNewChListVersion(self, mock_file, mock_exists):
        mock_exists.return_value = True
        session = MagicMock()

        dj = utils.Djcrash(session)
        dj.getNewChListVersion(None)

        self.assertEqual(dj.newVersion, "2024-05-22")
        self.assertEqual(dj.chID, "123")
        self.assertEqual(dj.canDownload, 1)

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="VER=1.0\nREV=456")
    def test_getCurrentChListVersion(self, mock_file, mock_exists):
        mock_exists.return_value = True
        session = MagicMock()

        dj = utils.Djcrash(session)

        version = dj.getCurrentChListVersion()
        self.assertEqual(version, "456")

if __name__ == '__main__':
    unittest.main()
