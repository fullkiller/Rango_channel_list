import sys
from unittest.mock import MagicMock

# Create a package-like structure for mocks
class MockModule(MagicMock):
    def __getattr__(self, name):
        return MagicMock()

def create_mock_package(name):
    m = MockModule()
    sys.modules[name] = m
    return m

# Initialize mocks
enigma = create_mock_package('enigma')
enigma.getDesktop.return_value.size.return_value.width.return_value = 1920
enigma.RT_HALIGN_LEFT = 0
enigma.RT_VALIGN_TOP = 0
enigma.gFont = MagicMock()

create_mock_package('Components')
create_mock_package('Components.Label')
create_mock_package('Components.ActionMap')
create_mock_package('Components.Sources')
create_mock_package('Components.Sources.List')
create_mock_package('Components.PluginList')
create_mock_package('Components.Sources.Progress')
create_mock_package('Components.Sources.StaticText')
create_mock_package('Components.Language')
create_mock_package('Components.Task')

create_mock_package('Screens')
create_mock_package('Screens.Standby')
create_mock_package('Screens.MessageBox')
create_mock_package('Screens.Screen')
create_mock_package('Screens.InfoBar')
create_mock_package('Screens.TaskView')
create_mock_package('Screens.ChoiceBox')

create_mock_package('Tools')
create_mock_package('Tools.LoadPixmap')
create_mock_package('Tools.Directories')
create_mock_package('Tools.Downloader')

create_mock_package('Plugins')
create_mock_package('Plugins.Plugin')

# Mock twisted
create_mock_package('twisted')
create_mock_package('twisted.web')
create_mock_package('twisted.web.client')

import os
os.environ['LANGUAGE'] = 'en'
def _(txt): return txt
import builtins
builtins._ = _
