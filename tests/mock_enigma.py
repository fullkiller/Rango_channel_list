import sys
from unittest.mock import MagicMock
import os

# Create mock modules
mock_enigma = MagicMock()
mock_enigma.getDesktop.return_value.size.return_value.width.return_value = 1920
sys.modules['enigma'] = mock_enigma

sys.modules['Components.Label'] = MagicMock()
sys.modules['Components.ActionMap'] = MagicMock()
sys.modules['Components.Sources.List'] = MagicMock()
sys.modules['Components.PluginList'] = MagicMock()
sys.modules['Components.Sources.Progress'] = MagicMock()
sys.modules['Components.Sources.StaticText'] = MagicMock()
sys.modules['Components.Language'] = MagicMock()
sys.modules['Screens.Standby'] = MagicMock()
sys.modules['Screens.MessageBox'] = MagicMock()

# Mock Screen to be a real class so we can instantiate it and have instance attributes
class MockScreen(object):
    def __init__(self, *args, **kwargs):
        self._elements = {}
    def __setitem__(self, key, value):
        self._elements[key] = value
    def __getitem__(self, key):
        return self._elements[key]
    def setTitle(self, title):
        pass
    def close(self):
        pass

sys.modules['Screens.Screen'] = MagicMock()
sys.modules['Screens.Screen'].Screen = MockScreen

sys.modules['Screens.InfoBar'] = MagicMock()
sys.modules['Screens.TaskView'] = MagicMock()
sys.modules['Screens.ChoiceBox'] = MagicMock()
sys.modules['Tools.LoadPixmap'] = MagicMock()
sys.modules['Tools.Directories'] = MagicMock()
sys.modules['Tools.Downloader'] = MagicMock()
sys.modules['Plugins.Plugin'] = MagicMock()
sys.modules['Components.Task'] = MagicMock()

# Mock getPage and downloadPage in twisted.web.client
mock_twisted = MagicMock()
sys.modules['twisted'] = mock_twisted
sys.modules['twisted.web'] = MagicMock()
sys.modules['twisted.web.client'] = MagicMock()

# Setup os.environ for Language
os.environ['LANGUAGE'] = 'en'

def mock_gettext(x):
    return x

import builtins
builtins._ = mock_gettext
