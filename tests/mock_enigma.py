import sys
from unittest.mock import MagicMock

class FakeScreen(dict):
    def __init__(self, *args, **kwargs):
        pass
    def setTitle(self, title):
        pass
    def close(self):
        pass

def setup_mocks():
    # Mock enigma module
    enigma = MagicMock()
    sys.modules['enigma'] = enigma

    # Mock Screens
    sys.modules['Screens'] = MagicMock()

    screen_mod = MagicMock()
    screen_mod.Screen = FakeScreen
    sys.modules['Screens.Screen'] = screen_mod

    sys.modules['Screens.MessageBox'] = MagicMock()
    sys.modules['Screens.InfoBar'] = MagicMock()
    sys.modules['Screens.TaskView'] = MagicMock()
    sys.modules['Screens.ChoiceBox'] = MagicMock()
    sys.modules['Screens.Standby'] = MagicMock()

    # Mock Components
    sys.modules['Components'] = MagicMock()
    sys.modules['Components.Label'] = MagicMock()
    sys.modules['Components.ActionMap'] = MagicMock()
    sys.modules['Components.Sources'] = MagicMock()
    sys.modules['Components.Sources.List'] = MagicMock()
    sys.modules['Components.Sources.Progress'] = MagicMock()
    sys.modules['Components.Sources.StaticText'] = MagicMock()
    sys.modules['Components.Task'] = MagicMock()
    sys.modules['Components.Language'] = MagicMock()
    sys.modules['Components.MultiContent'] = MagicMock()

    # Mock Tools
    sys.modules['Tools'] = MagicMock()
    sys.modules['Tools.LoadPixmap'] = MagicMock()
    sys.modules['Tools.Directories'] = MagicMock()
    sys.modules['Tools.Downloader'] = MagicMock()

    # Mock Plugins
    sys.modules['Plugins'] = MagicMock()
    sys.modules['Plugins.Plugin'] = MagicMock()

    # Mock twisted
    sys.modules['twisted'] = MagicMock()
    sys.modules['twisted.web'] = MagicMock()
    sys.modules['twisted.web.client'] = MagicMock()

    def _(txt):
        return txt

    import builtins
    builtins._ = _

setup_mocks()
