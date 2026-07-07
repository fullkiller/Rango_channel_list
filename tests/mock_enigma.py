import sys
from unittest.mock import MagicMock
import os

# Mock twisted.web.client before it's imported
twisted_mock = MagicMock()
twisted_mock.web.client.getPage = MagicMock()
twisted_mock.web.client.downloadPage = MagicMock()
sys.modules['twisted'] = twisted_mock
sys.modules['twisted.web'] = twisted_mock.web
sys.modules['twisted.web.client'] = twisted_mock.web.client

# Mock enigma and other Enigma2 components
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
sys.modules['Components.Sources.Progress'] = MagicMock()
sys.modules['Components.Sources.StaticText'] = MagicMock()
sys.modules['Components.PluginList'] = MagicMock()
sys.modules['Components.Language'] = MagicMock()
sys.modules['Tools'] = MagicMock()
sys.modules['Tools.LoadPixmap'] = MagicMock()
sys.modules['Tools.Directories'] = MagicMock()
sys.modules['Tools.Downloader'] = MagicMock()
sys.modules['Plugins'] = MagicMock()
sys.modules['Plugins.Plugin'] = MagicMock()

# Setup gettext mock
import builtins
builtins._ = lambda x: x

os.environ['LANGUAGE'] = 'en'
