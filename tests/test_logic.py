import unittest
import os
import sys
import shutil
import tempfile
import io

# Mock enigma module
class MockEnigma:
	class eDVBDB:
		@staticmethod
		def getInstance():
			return MockEnigma.eDVBDB()
		def removeServices(self): pass
		def reloadServicelist(self): pass
		def reloadBouquets(self): pass

sys.modules['enigma'] = MockEnigma

# Mock twisted.web.client
mock_twc = type('module', (), {'getPage': lambda x, **kwargs: None, 'downloadPage': lambda x, y, **kwargs: None})
sys.modules['twisted'] = type('module', (), {})
sys.modules['twisted.web'] = type('module', (), {})
sys.modules['twisted.web.client'] = mock_twc

# Mock Components and Screens
sys.modules['Components'] = type('module', (), {})
sys.modules['Components.Label'] = type('module', (), {'Label': lambda x: None})
sys.modules['Components.ActionMap'] = type('module', (), {'ActionMap': lambda x, y, z=None: None})
sys.modules['Components.Sources'] = type('module', (), {})
sys.modules['Components.Sources.List'] = type('module', (), {'List': lambda x: None})
sys.modules['Components.Sources.Progress'] = type('module', (), {'Progress': lambda: None})
sys.modules['Components.Sources.StaticText'] = type('module', (), {'StaticText': lambda: None})
sys.modules['Components.PluginList'] = type('module', (), {'resolveFilename': lambda x, y=None: ""})
sys.modules['Screens'] = type('module', (), {})
sys.modules['Screens.Standby'] = type('module', (), {'TryQuitMainloop': None})
sys.modules['Screens.MessageBox'] = type('module', (), {'MessageBox': type('MB', (), {'TYPE_INFO': 0, 'TYPE_YESNO': 1})})
sys.modules['Screens.Screen'] = type('module', (), {'Screen': type('Screen', (), {'__init__': lambda x, y, z=None: None, 'setTitle': lambda x, y: None})})
sys.modules['Screens.InfoBar'] = type('module', (), {'InfoBar': type('IB', (), {'instance': None})})
sys.modules['Screens.TaskView'] = type('module', (), {'JobView': None})
sys.modules['Screens.ChoiceBox'] = type('module', (), {'ChoiceBox': None})
sys.modules['Tools'] = type('module', (), {})
sys.modules['Tools.LoadPixmap'] = type('module', (), {'LoadPixmap': lambda x: None})
sys.modules['Tools.Directories'] = type('module', (), {'fileExists': os.path.exists, 'SCOPE_PLUGINS': 0})
sys.modules['Tools.Downloader'] = type('module', (), {'downloadWithProgress': lambda x, y: None})
sys.modules['Plugins'] = type('module', (), {})
sys.modules['Plugins.Plugin'] = type('module', (), {'PluginDescriptor': lambda **kwargs: None})
sys.modules['Components.Task'] = type('module', (), {'Task': object, 'Job': object, 'Condition': object, 'job_manager': None})

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater')))

from utils import is_path_safe

class TestPluginLogic(unittest.TestCase):
	def test_is_path_safe(self):
		base = "/tmp/test"
		self.assertTrue(is_path_safe(base, "/tmp/test/file.txt"))
		self.assertTrue(is_path_safe(base, "/tmp/test/subdir/file.txt"))
		self.assertFalse(is_path_safe(base, "/tmp/test/../outside.txt"))
		self.assertFalse(is_path_safe(base, "/etc/passwd"))
		# Cases with similar prefixes
		self.assertFalse(is_path_safe("/tmp/test", "/tmp/test_suffix/file.txt"))

	def test_version_parsing(self):
		# This test would require more mocking of plugin.py
		pass

if __name__ == '__main__':
	unittest.main()
