import sys
from unittest.mock import MagicMock

class MockEnigma:
    def getDesktop(self, n):
        desktop = MagicMock()
        desktop.size.return_value.width.return_value = 1920
        return desktop

class MockLanguage:
    def getLanguage(self):
        return "pl_PL"

mock_enigma = MockEnigma()
sys.modules['enigma'] = MagicMock()
sys.modules['enigma'].getDesktop = mock_enigma.getDesktop
sys.modules['enigma'].RT_HALIGN_LEFT = 0
sys.modules['enigma'].RT_VALIGN_TOP = 0
sys.modules['enigma'].gFont = MagicMock()
sys.modules['enigma'].eDVBDB = MagicMock()

sys.modules['Components'] = MagicMock()
sys.modules['Components.Label'] = MagicMock()
sys.modules['Components.ActionMap'] = MagicMock()
sys.modules['Components.Sources'] = MagicMock()
sys.modules['Components.Sources.List'] = MagicMock()
sys.modules['Components.Sources.Progress'] = MagicMock()
sys.modules['Components.Sources.StaticText'] = MagicMock()
sys.modules['Components.PluginList'] = MagicMock()
sys.modules['Components.Language'] = MagicMock()
sys.modules['Components.Language'].language = MockLanguage()
sys.modules['Components.Task'] = MagicMock()

sys.modules['Screens'] = MagicMock()
sys.modules['Screens.Screen'] = MagicMock()
sys.modules['Screens.MessageBox'] = MagicMock()
sys.modules['Screens.Standby'] = MagicMock()
sys.modules['Screens.InfoBar'] = MagicMock()
sys.modules['Screens.TaskView'] = MagicMock()
sys.modules['Screens.ChoiceBox'] = MagicMock()

sys.modules['Tools'] = MagicMock()
sys.modules['Tools.LoadPixmap'] = MagicMock()
sys.modules['Tools.Directories'] = MagicMock()
sys.modules['Tools.Directories'].resolveFilename = MagicMock(return_value="/tmp/")
sys.modules['Tools.Downloader'] = MagicMock()

sys.modules['Plugins'] = MagicMock()
sys.modules['Plugins.Plugin'] = MagicMock()
