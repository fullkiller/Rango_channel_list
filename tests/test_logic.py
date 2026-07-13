import sys
import os
import unittest
from unittest.mock import MagicMock
import types

# Mock Enigma2 modules
sys.modules['enigma'] = MagicMock()
sys.modules['Screens'] = MagicMock()
sys.modules['Screens.Screen'] = MagicMock()
sys.modules['Screens.MessageBox'] = MagicMock()
sys.modules['Screens.InfoBar'] = MagicMock()
sys.modules['Screens.TaskView'] = MagicMock()
sys.modules['Screens.ChoiceBox'] = MagicMock()
sys.modules['Screens.Standby'] = MagicMock()
sys.modules['Components'] = MagicMock()
sys.modules['Components.Label'] = MagicMock()
sys.modules['Components.ActionMap'] = MagicMock()
sys.modules['Components.Task'] = MagicMock()
sys.modules['Tools'] = MagicMock()
sys.modules['Tools.Downloader'] = MagicMock()
sys.modules['Tools.Directories'] = MagicMock()

# Mock twisted
mock_twisted_client = MagicMock()
sys.modules['twisted'] = MagicMock()
sys.modules['twisted.web'] = MagicMock()
sys.modules['twisted.web.client'] = mock_twisted_client

# Define mock _ function
def mock_underscore(txt):
    return txt

# Add tests directory to path to allow importing from RangoPolishChannelsUpdater
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# We need to mock the _ function in the package
import RangoPolishChannelsUpdater
RangoPolishChannelsUpdater._ = mock_underscore

# Now import utils from the package
from RangoPolishChannelsUpdater import utils

class TestPluginLogic(unittest.TestCase):
    def test_decode_html(self):
        self.assertEqual(utils.decode_html(b"test"), "test")
        self.assertEqual(utils.decode_html("test"), "test")

    def test_is_path_safe(self):
        self.assertTrue(utils.is_path_safe("/tmp", "/tmp/file"))
        self.assertTrue(utils.is_path_safe("/tmp", "/tmp/dir/file"))
        self.assertFalse(utils.is_path_safe("/tmp", "/etc/passwd"))
        self.assertTrue(utils.is_path_safe("/", "/etc/passwd")) # Root is always safe in this context
        self.assertTrue(utils.is_path_safe("/tmp", "/tmp"))

    def test_version_parsing(self):
        html = "version:20240522\nurl:http://example.com/file.tgz"
        new = dict([ l.split(':',1) for l in html.split("\n") if l.find(":") > 0])
        self.assertEqual(new['version'], "20240522")
        self.assertEqual(new['url'], "http://example.com/file.tgz")

if __name__ == '__main__':
    unittest.main()
