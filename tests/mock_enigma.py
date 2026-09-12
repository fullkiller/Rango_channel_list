# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock

# Mocking Enigma2 components
class MockEnigma:
	def __init__(self):
		self.size = MagicMock(return_value=MagicMock(width=1920, height=1080))
		self.width = 1920
		self.height = 1080

mock_enigma = MagicMock()
mock_enigma.getDesktop.return_value.size.return_value.width = 1920
sys.modules['enigma'] = mock_enigma

sys.modules['Screens'] = MagicMock()
class Screen:
	def __init__(self, *args, **kwargs):
		self.dict = {}
	def __setitem__(self, key, value):
		self.dict[key] = value
	def __getitem__(self, key):
		return self.dict[key]
	def setTitle(self, *args, **kwargs):
		pass
	def close(self, *args, **kwargs):
		pass

sys.modules['Screens.Screen'] = MagicMock()
sys.modules['Screens.Screen'].Screen = Screen
sys.modules['Screens.MessageBox'] = MagicMock()
sys.modules['Screens.InfoBar'] = MagicMock()
sys.modules['Screens.TaskView'] = MagicMock()
sys.modules['Screens.ChoiceBox'] = MagicMock()
sys.modules['Screens.Standby'] = MagicMock()

sys.modules['Components'] = MagicMock()
sys.modules['Components.Label'] = MagicMock()
sys.modules['Components.ActionMap'] = MagicMock()
sys.modules['Components.Sources'] = MagicMock()
sys.modules['Components.Sources.List'] = MagicMock()
sys.modules['Components.Sources.Progress'] = MagicMock()
sys.modules['Components.Sources.StaticText'] = MagicMock()
sys.modules['Components.Task'] = MagicMock()
sys.modules['Components.Language'] = MagicMock()

sys.modules['Tools'] = MagicMock()
sys.modules['Tools.LoadPixmap'] = MagicMock()
sys.modules['Tools.Directories'] = MagicMock()
sys.modules['Tools.Downloader'] = MagicMock()

sys.modules['Plugins'] = MagicMock()
sys.modules['Plugins.Plugin'] = MagicMock()

# Mock Twisted
mock_twisted = MagicMock()
sys.modules['twisted'] = mock_twisted
sys.modules['twisted.web'] = MagicMock()
sys.modules['twisted.web.client'] = MagicMock()

def _(txt):
	return txt

import builtins
builtins._ = _
