# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock
import os

# Mock Enigma2 modules
mock_enigma = MagicMock()
sys.modules['enigma'] = mock_enigma

mock_components = MagicMock()
sys.modules['Components'] = mock_components
sys.modules['Components.Label'] = mock_components.Label
sys.modules['Components.ActionMap'] = mock_components.ActionMap
sys.modules['Components.Sources'] = mock_components.Sources
sys.modules['Components.Sources.List'] = mock_components.Sources.List
sys.modules['Components.Sources.Progress'] = mock_components.Sources.Progress
sys.modules['Components.Sources.StaticText'] = mock_components.Sources.StaticText
sys.modules['Components.Language'] = mock_components.Language
sys.modules['Components.Task'] = mock_components.Task

mock_screens = MagicMock()
sys.modules['Screens'] = mock_screens
sys.modules['Screens.Screen'] = mock_screens.Screen
sys.modules['Screens.MessageBox'] = mock_screens.MessageBox
sys.modules['Screens.Standby'] = mock_screens.Standby
sys.modules['Screens.InfoBar'] = mock_screens.InfoBar
sys.modules['Screens.TaskView'] = mock_screens.TaskView
sys.modules['Screens.ChoiceBox'] = mock_screens.ChoiceBox

mock_tools = MagicMock()
sys.modules['Tools'] = mock_tools
sys.modules['Tools.LoadPixmap'] = mock_tools.LoadPixmap
sys.modules['Tools.Directories'] = mock_tools.Directories
sys.modules['Tools.Downloader'] = mock_tools.Downloader

mock_plugins = MagicMock()
sys.modules['Plugins'] = mock_plugins
sys.modules['Plugins.Plugin'] = mock_plugins.Plugin

# Mock twisted
mock_twisted = MagicMock()
sys.modules['twisted'] = mock_twisted
sys.modules['twisted.web'] = mock_twisted.web
sys.modules['twisted.web.client'] = mock_twisted.web.client

# Mock getPage and downloadPage if not present in mock
def getPage(url, *args, **kwargs):
    return MagicMock()

def downloadPage(url, file, *args, **kwargs):
    return MagicMock()

sys.modules['twisted.web.client'].getPage = getPage
sys.modules['twisted.web.client'].downloadPage = downloadPage

os.environ['LANGUAGE'] = 'en'
