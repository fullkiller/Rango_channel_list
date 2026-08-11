import os
import unittest
from unittest.mock import MagicMock, patch
import sys
import types

# Mock twisted before it's imported
twisted = types.ModuleType('twisted')
sys.modules['twisted'] = twisted
twisted_web = types.ModuleType('twisted.web')
sys.modules['twisted.web'] = twisted_web
twisted_web_client = types.ModuleType('twisted.web.client')
sys.modules['twisted.web.client'] = twisted_web_client
twisted_web_client.getPage = MagicMock()
twisted_web_client.downloadPage = MagicMock()

# Mock enigma module
enigma = types.ModuleType('enigma')
enigma.eDVBDB = MagicMock()
enigma.getDesktop = MagicMock()
sys.modules['enigma'] = enigma

# Mock Components and other Enigma2 modules
sys.modules['Components'] = types.ModuleType('Components')
sys.modules['Components.Label'] = types.ModuleType('Components.Label')
sys.modules['Components.Label'].Label = MagicMock
sys.modules['Components.ActionMap'] = types.ModuleType('Components.ActionMap')
sys.modules['Components.ActionMap'].ActionMap = MagicMock
sys.modules['Components.Sources'] = types.ModuleType('Components.Sources')
sys.modules['Components.Sources.List'] = types.ModuleType('Components.Sources.List')
sys.modules['Components.Sources.List'].List = MagicMock
sys.modules['Components.Sources.Progress'] = types.ModuleType('Components.Sources.Progress')
sys.modules['Components.Sources.Progress'].Progress = MagicMock
sys.modules['Components.Sources.StaticText'] = types.ModuleType('Components.Sources.StaticText')
sys.modules['Components.Sources.StaticText'].StaticText = MagicMock
sys.modules['Components.PluginList'] = types.ModuleType('Components.PluginList')
sys.modules['Components.PluginList'].resolveFilename = MagicMock()
sys.modules['Components.Task'] = types.ModuleType('Components.Task')
sys.modules['Components.Task'].Task = MagicMock
sys.modules['Components.Task'].Job = MagicMock
sys.modules['Components.Task'].Condition = MagicMock
sys.modules['Components.Task'].job_manager = MagicMock()

sys.modules['Screens'] = types.ModuleType('Screens')
sys.modules['Screens.Screen'] = types.ModuleType('Screens.Screen')
sys.modules['Screens.Screen'].Screen = MagicMock
sys.modules['Screens.MessageBox'] = types.ModuleType('Screens.MessageBox')
sys.modules['Screens.MessageBox'].MessageBox = MagicMock
sys.modules['Screens.InfoBar'] = types.ModuleType('Screens.InfoBar')
sys.modules['Screens.InfoBar'].InfoBar = MagicMock
sys.modules['Screens.TaskView'] = types.ModuleType('Screens.TaskView')
sys.modules['Screens.TaskView'].JobView = MagicMock
sys.modules['Screens.ChoiceBox'] = types.ModuleType('Screens.ChoiceBox')
sys.modules['Screens.ChoiceBox'].ChoiceBox = MagicMock
sys.modules['Screens.Standby'] = types.ModuleType('Screens.Standby')
sys.modules['Screens.Standby'].TryQuitMainloop = MagicMock

sys.modules['Tools'] = types.ModuleType('Tools')
sys.modules['Tools.LoadPixmap'] = types.ModuleType('Tools.LoadPixmap')
sys.modules['Tools.LoadPixmap'].LoadPixmap = MagicMock()
sys.modules['Tools.Directories'] = types.ModuleType('Tools.Directories')
sys.modules['Tools.Directories'].fileExists = os.path.exists
sys.modules['Tools.Directories'].SCOPE_PLUGINS = 0
sys.modules['Tools.Downloader'] = types.ModuleType('Tools.Downloader')
sys.modules['Tools.Downloader'].downloadWithProgress = MagicMock

sys.modules['Plugins'] = types.ModuleType('Plugins')
sys.modules['Plugins.Plugin'] = types.ModuleType('Plugins.Plugin')
sys.modules['Plugins.Plugin'].PluginDescriptor = MagicMock

# Mock gettext _
import builtins
builtins._ = lambda x: x

# Add src to path
# We need to simulate the package structure for relative imports
package_path = os.path.abspath('src/usr/lib/enigma2/python/Plugins/Extensions')
sys.path.append(package_path)

from RangoPolishChannelsUpdater.utils import is_path_safe

class TestLogic(unittest.TestCase):
    def test_path_safe(self):
        base = "/tmp/extract"
        self.assertTrue(is_path_safe(base, "/tmp/extract/file.txt"))
        self.assertTrue(is_path_safe(base, "/tmp/extract/dir/file.txt"))
        self.assertFalse(is_path_safe(base, "/tmp/extract/../other.txt"))
        self.assertFalse(is_path_safe(base, "/etc/passwd"))
        # edge case: base as prefix
        self.assertFalse(is_path_safe(base, "/tmp/extract_secret/file.txt"))

    def test_imports(self):
        # Test if we can import the modules without errors (meaning syntax is ok for python3)
        try:
            from RangoPolishChannelsUpdater import utils
            from RangoPolishChannelsUpdater import plugin
        except Exception as e:
            self.fail(f"Import failed: {e}")

if __name__ == '__main__':
    unittest.main()
