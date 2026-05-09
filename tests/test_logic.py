
import sys
import os
import unittest
from unittest.mock import MagicMock, patch, mock_open
import types

# Create a helper to create mock modules
def mock_module(name):
    m = types.ModuleType(name)
    sys.modules[name] = m
    return m

# Mock Enigma2 modules
enigma = mock_module('enigma')
enigma.getDesktop = MagicMock()
enigma.eDVBDB = MagicMock()

mock_module('Components')
mock_module('Components.Label')
sys.modules['Components.Label'].Label = MagicMock()
mock_module('Components.ActionMap')
sys.modules['Components.ActionMap'].ActionMap = MagicMock()
mock_module('Components.Sources')
mock_module('Components.Sources.List')
sys.modules['Components.Sources.List'].List = MagicMock()
mock_module('Components.Sources.Progress')
sys.modules['Components.Sources.Progress'].Progress = MagicMock()
mock_module('Components.Sources.StaticText')
sys.modules['Components.Sources.StaticText'].StaticText = MagicMock()
mock_module('Components.PluginList')
sys.modules['Components.PluginList'].resolveFilename = MagicMock()
mock_module('Components.Task')
sys.modules['Components.Task'].Task = MagicMock()
sys.modules['Components.Task'].Job = MagicMock()
sys.modules['Components.Task'].job_manager = MagicMock()
sys.modules['Components.Task'].Condition = MagicMock()

mock_module('Screens')
mock_module('Screens.Screen')
class MockScreen:
    def __init__(self, *args, **kwargs):
        self.widgets = {}
    def __setitem__(self, key, value):
        self.widgets[key] = value
    def __getitem__(self, key):
        return self.widgets[key]
    def setTitle(self, *args, **kwargs):
        pass
    def close(self, *args, **kwargs):
        pass
sys.modules['Screens.Screen'].Screen = MockScreen
mock_module('Screens.MessageBox')
sys.modules['Screens.MessageBox'].MessageBox = MagicMock()
mock_module('Screens.Standby')
sys.modules['Screens.Standby'].TryQuitMainloop = MagicMock()
mock_module('Screens.InfoBar')
sys.modules['Screens.InfoBar'].InfoBar = MagicMock()
mock_module('Screens.TaskView')
sys.modules['Screens.TaskView'].JobView = MagicMock()
mock_module('Screens.ChoiceBox')
sys.modules['Screens.ChoiceBox'].ChoiceBox = MagicMock()

mock_module('Tools')
mock_module('Tools.LoadPixmap')
sys.modules['Tools.LoadPixmap'].LoadPixmap = MagicMock()
mock_module('Tools.Directories')
sys.modules['Tools.Directories'].fileExists = MagicMock()
sys.modules['Tools.Directories'].SCOPE_PLUGINS = 'plugins'
mock_module('Tools.Downloader')
sys.modules['Tools.Downloader'].downloadWithProgress = MagicMock()

mock_module('Plugins')
mock_module('Plugins.Plugin')
sys.modules['Plugins.Plugin'].PluginDescriptor = MagicMock()

# Mock twisted
mock_module('twisted')
mock_module('twisted.web')
mock_module('twisted.web.client')
sys.modules['twisted.web.client'].getPage = MagicMock()
sys.modules['twisted.web.client'].downloadPage = MagicMock()

# Add src to path
sys.path.append(os.path.abspath('src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater'))

# Define _ for gettext
import builtins
builtins._ = lambda x: x

class TestSecurityLogic(unittest.TestCase):
    def test_is_path_safe(self):
        from utils import is_path_safe
        self.assertTrue(is_path_safe('/', '/etc/enigma2/settings'))
        self.assertTrue(is_path_safe('/tmp', '/tmp/test.txt'))
        self.assertFalse(is_path_safe('/tmp', '/etc/passwd'))
        self.assertFalse(is_path_safe('/tmp', '/tmp/../etc/passwd'))

    @patch('os.path.realpath')
    def test_is_path_safe_prefix(self, mock_realpath):
        from utils import is_path_safe
        mock_realpath.side_effect = lambda x: x
        self.assertFalse(is_path_safe('/tmp/foo', '/tmp/foobar'))
        self.assertTrue(is_path_safe('/tmp/foo', '/tmp/foo/bar'))

    def test_djcrash_version_parsing(self):
        from utils import Djcrash
        # Mocking Screen.__init__ via MockScreen
        dj = Djcrash(MagicMock())

        # Test getCurrentChListVersion with valid file
        m = mock_open(read_data="DATE=20240522\nVER=123")
        with patch('builtins.open', m):
            version = dj.getCurrentChListVersion()
            self.assertEqual(version, "20240522")

        # Test getCurrentChListVersion with invalid file
        m = mock_open(read_data="INVALID")
        with patch('builtins.open', m):
            dj.curVersion = "nieznana"
            version = dj.getCurrentChListVersion()
            self.assertEqual(version, "nieznana")

if __name__ == '__main__':
    unittest.main()
