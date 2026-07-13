import unittest
import os
import sys
from unittest.mock import MagicMock

# Mock Enigma2 modules more thoroughly
class MockModule(MagicMock):
    def __getattr__(self, name):
        return MagicMock()

def mock_package(name):
    m = MagicMock()
    sys.modules[name] = m
    return m

mock_package('enigma')
mock_package('Components')
mock_package('Components.Label')
mock_package('Components.ActionMap')
mock_package('Components.Sources')
mock_package('Components.Sources.List')
mock_package('Components.Sources.Progress')
mock_package('Components.Sources.StaticText')
mock_package('Components.Language')
mock_package('Components.Task')
mock_package('Components.PluginList')
mock_package('Screens')
mock_package('Screens.Screen')
mock_package('Screens.MessageBox')
mock_package('Screens.Standby')
mock_package('Screens.InfoBar')
mock_package('Screens.TaskView')
mock_package('Screens.ChoiceBox')
mock_package('Tools')
mock_package('Tools.LoadPixmap')
mock_package('Tools.Directories')
mock_package('Tools.Downloader')
mock_package('Plugins')
mock_package('Plugins.Plugin')
mock_package('twisted')
mock_package('twisted.web')
mock_package('twisted.web.client')

# Mock gettext
import builtins
builtins._ = lambda x: x

# Add src path
plugin_base = os.path.join(os.getcwd(), 'src/usr/lib/enigma2/python/Plugins/Extensions')
sys.path.append(plugin_base)

from RangoPolishChannelsUpdater import utils

class TestSecurityLogic(unittest.TestCase):
    def test_is_path_safe(self):
        # We need to mock os.path.realpath to behave predictably in this environment
        with unittest.mock.patch('os.path.realpath', side_effect=lambda x: x):
            self.assertTrue(utils.is_path_safe('/tmp', '/tmp/file.txt'))
            self.assertTrue(utils.is_path_safe('/tmp/', '/tmp/subdir/file.txt'))
            # os.path.relpath('/tmp/../etc/passwd', '/tmp') -> '../../etc/passwd'
            self.assertFalse(utils.is_path_safe('/tmp', '/etc/passwd'))

    def test_is_path_safe_root(self):
        with unittest.mock.patch('os.path.realpath', side_effect=lambda x: x):
            self.assertTrue(utils.is_path_safe('/', '/usr/lib/enigma2'))
            self.assertTrue(utils.is_path_safe('/', '/etc/enigma2'))
            self.assertFalse(utils.is_path_safe('/', '/root/.ssh/id_rsa'))

if __name__ == '__main__':
    unittest.main()
