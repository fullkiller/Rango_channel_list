import sys
from unittest.mock import MagicMock

# Mocking twisted
mock_twisted_client = MagicMock()
sys.modules['twisted'] = MagicMock()
sys.modules['twisted.web'] = MagicMock()
sys.modules['twisted.web.client'] = mock_twisted_client

# Mocking enigma and other set-top box components
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
sys.modules['Components.Sources'] = MagicMock()
sys.modules['Components.Sources.List'] = MagicMock()
sys.modules['Components.PluginList'] = MagicMock()
sys.modules['Components.Sources.Progress'] = MagicMock()
sys.modules['Components.Sources.StaticText'] = MagicMock()
sys.modules['Tools'] = MagicMock()
sys.modules['Tools.LoadPixmap'] = MagicMock()
sys.modules['Tools.Directories'] = MagicMock()
sys.modules['Tools.Downloader'] = MagicMock()
sys.modules['Plugins'] = MagicMock()
sys.modules['Plugins.Plugin'] = MagicMock()

def _(text):
    return text

import builtins
builtins._ = _
