import sys
from mock import MagicMock

# Stubs for Twisted legacy functions if they are missing
import twisted.web.client
if not hasattr(twisted.web.client, 'getPage'):
    twisted.web.client.getPage = MagicMock()
if not hasattr(twisted.web.client, 'downloadPage'):
    twisted.web.client.downloadPage = MagicMock()

mock_enigma = MagicMock()
sys.modules['enigma'] = mock_enigma

mock_screens_screen = MagicMock()
sys.modules['Screens.Screen'] = mock_screens_screen

mock_screens_messagebox = MagicMock()
sys.modules['Screens.MessageBox'] = mock_screens_messagebox

mock_screens_infobar = MagicMock()
sys.modules['Screens.InfoBar'] = mock_screens_infobar

mock_screens_taskview = MagicMock()
sys.modules['Screens.TaskView'] = mock_screens_taskview

mock_screens_choicebox = MagicMock()
sys.modules['Screens.ChoiceBox'] = mock_screens_choicebox

mock_screens_standby = MagicMock()
sys.modules['Screens.Standby'] = mock_screens_standby

mock_components_label = MagicMock()
sys.modules['Components.Label'] = mock_components_label

mock_components_actionmap = MagicMock()
sys.modules['Components.ActionMap'] = mock_components_actionmap

mock_components_task = MagicMock()
sys.modules['Components.Task'] = mock_components_task

mock_components_sources_list = MagicMock()
sys.modules['Components.Sources.List'] = mock_components_sources_list

mock_components_sources_progress = MagicMock()
sys.modules['Components.Sources.Progress'] = mock_components_sources_progress

mock_components_sources_statictext = MagicMock()
sys.modules['Components.Sources.StaticText'] = mock_components_sources_statictext

mock_tools_loadpixmap = MagicMock()
sys.modules['Tools.LoadPixmap'] = mock_tools_loadpixmap

mock_tools_directories = MagicMock()
sys.modules['Tools.Directories'] = mock_tools_directories

mock_tools_downloader = MagicMock()
sys.modules['Tools.Downloader'] = mock_tools_downloader

mock_plugins_plugin = MagicMock()
sys.modules['Plugins.Plugin'] = mock_plugins_plugin

mock_components_language = MagicMock()
sys.modules['Components.Language'] = mock_components_language

import os
os.environ['LANGUAGE'] = 'pl_PL'
