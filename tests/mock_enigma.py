import sys
from unittest.mock import MagicMock

class MockSize:
    def width(self):
        return 1920

class MockDesktop:
    def size(self):
        return MockSize()

enigma = MagicMock()
enigma.getDesktop.return_value = MockDesktop()
enigma.RT_HALIGN_LEFT = 0
enigma.RT_VALIGN_TOP = 0
enigma.gFont = lambda x, y: None

sys.modules['enigma'] = enigma
sys.modules['Components'] = MagicMock()
sys.modules['Components.Label'] = MagicMock()
sys.modules['Components.ActionMap'] = MagicMock()
sys.modules['Components.Sources'] = MagicMock()
sys.modules['Components.Sources.List'] = MagicMock()
sys.modules['Components.Sources.Progress'] = MagicMock()
sys.modules['Components.Sources.StaticText'] = MagicMock()
sys.modules['Components.Task'] = MagicMock()

mock_language = MagicMock()
mock_language.language.getLanguage.return_value = "pl_PL"
sys.modules['Components.Language'] = mock_language

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
sys.modules['Tools.Downloader'] = MagicMock()
sys.modules['Plugins'] = MagicMock()
sys.modules['Plugins.Plugin'] = MagicMock()

# Mock twisted
mock_twisted_web_client = MagicMock()
sys.modules['twisted'] = MagicMock()
sys.modules['twisted.web'] = MagicMock()
sys.modules['twisted.web.client'] = mock_twisted_web_client
