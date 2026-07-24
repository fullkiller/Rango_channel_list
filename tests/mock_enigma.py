# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock

# Create necessary module mocks
class MockLanguage(MagicMock):
    def addCallback(self, cb):
        pass

# Populate Components.Language mock
Components = MagicMock()
sys.modules['Components'] = Components
Components.Language = MagicMock()
Components.Language.language = MockLanguage()

# Populate other modules
sys.modules['enigma'] = MagicMock()
sys.modules['Components.Label'] = MagicMock()
sys.modules['Components.ActionMap'] = MagicMock()
sys.modules['Components.Sources'] = MagicMock()
sys.modules['Components.Sources.List'] = MagicMock()
sys.modules['Components.Sources.Progress'] = MagicMock()
sys.modules['Components.Sources.StaticText'] = MagicMock()
sys.modules['Components.PluginList'] = MagicMock()
sys.modules['Components.MultiContent'] = MagicMock()

sys.modules['Screens'] = MagicMock()
sys.modules['Screens.Standby'] = MagicMock()
sys.modules['Screens.MessageBox'] = MagicMock()
sys.modules['Screens.Screen'] = MagicMock()
sys.modules['Screens.InfoBar'] = MagicMock()
sys.modules['Screens.TaskView'] = MagicMock()
sys.modules['Screens.ChoiceBox'] = MagicMock()

# Setup Screens.Screen.Screen as a class inheriting from dict
class MockScreen(dict):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.title = ""
    def setTitle(self, title):
        self.title = title
    def close(self, *args, **kwargs):
        pass
sys.modules['Screens.Screen'].Screen = MockScreen

sys.modules['Tools'] = MagicMock()
sys.modules['Tools.LoadPixmap'] = MagicMock()
sys.modules['Tools.Directories'] = MagicMock()
sys.modules['Tools.Directories'].SCOPE_PLUGINS = 'plugins'
sys.modules['Tools.Directories'].resolveFilename = lambda scope, path="": "src/"
sys.modules['Tools.Directories'].fileExists = lambda path: True

sys.modules['Tools.Downloader'] = MagicMock()
sys.modules['Plugins'] = MagicMock()
sys.modules['Plugins.Plugin'] = MagicMock()
sys.modules['Components.Task'] = MagicMock()

# Mock Twisted client
import twisted.web.client
twisted.web.client.getPage = MagicMock()
twisted.web.client.downloadPage = MagicMock()
sys.modules['twisted.web.client'] = sys.modules['twisted.web.client']
