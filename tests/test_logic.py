import unittest
import os
import sys
from types import ModuleType

# Setup mock Enigma2 modules
def mock_gettext(txt): return txt

# Prepare Tools.Directories
dir_mod = ModuleType('Tools.Directories')
dir_mod.resolveFilename = lambda x, y=None: ""
dir_mod.SCOPE_PLUGINS = 0
dir_mod.fileExists = os.path.exists
sys.modules['Tools.Directories'] = dir_mod

# Prepare Components.Language
lang_mod = ModuleType('Components.Language')
lang_mod.language = ModuleType('language')
lang_mod.language.addCallback = lambda x: None
sys.modules['Components.Language'] = lang_mod

# Prepare enigma
enigma_mod = ModuleType('enigma')
enigma_mod.eDVBDB = ModuleType('eDVBDB')
enigma_mod.getDesktop = lambda x: None
sys.modules['enigma'] = enigma_mod

# Prepare Screens
screen_mod = ModuleType('Screens.Screen')
screen_mod.Screen = type('Screen', (object,), {})
sys.modules['Screens.Screen'] = screen_mod

mb_mod = ModuleType('Screens.MessageBox')
mb_mod.MessageBox = type('MessageBox', (object,), {})
sys.modules['Screens.MessageBox'] = mb_mod

infobar_mod = ModuleType('Screens.InfoBar')
infobar_mod.InfoBar = type('InfoBar', (object,), {})
sys.modules['Screens.InfoBar'] = infobar_mod

tv_mod = ModuleType('Screens.TaskView')
tv_mod.JobView = type('JobView', (object,), {})
sys.modules['Screens.TaskView'] = tv_mod

cb_mod = ModuleType('Screens.ChoiceBox')
cb_mod.ChoiceBox = type('ChoiceBox', (object,), {})
sys.modules['Screens.ChoiceBox'] = cb_mod

standby_mod = ModuleType('Screens.Standby')
standby_mod.TryQuitMainloop = type('TryQuitMainloop', (object,), {})
sys.modules['Screens.Standby'] = standby_mod

# Prepare Components
label_mod = ModuleType('Components.Label')
label_mod.Label = type('Label', (object,), {})
sys.modules['Components.Label'] = label_mod

am_mod = ModuleType('Components.ActionMap')
am_mod.ActionMap = type('ActionMap', (object,), {})
sys.modules['Components.ActionMap'] = am_mod

task_mod = ModuleType('Components.Task')
task_mod.Task = type('Task', (object,), {})
task_mod.Job = type('Job', (object,), {})
task_mod.Condition = type('Condition', (object,), {})
task_mod.job_manager = None
sys.modules['Components.Task'] = task_mod

# Prepare Tools
dl_mod = ModuleType('Tools.Downloader')
dl_mod.downloadWithProgress = lambda x, y: None
sys.modules['Tools.Downloader'] = dl_mod

# Mock twisted
twc_mod = ModuleType('twisted.web.client')
twc_mod.getPage = lambda x: None
twc_mod.downloadPage = lambda x, y: None
sys.modules['twisted.web.client'] = twc_mod

# Add package to path
sys.path.append(os.path.join(os.getcwd(), 'src/usr/lib/enigma2/python/Plugins/Extensions'))

# Mock the _ in the package BEFORE importing utils
import RangoPolishChannelsUpdater
RangoPolishChannelsUpdater._ = mock_gettext

from RangoPolishChannelsUpdater.utils import is_path_safe

class TestLogic(unittest.TestCase):
	def test_is_path_safe_subdir(self):
		base = "/tmp/test"
		self.assertTrue(is_path_safe(base, "/tmp/test/file.txt"))
		self.assertTrue(is_path_safe(base, "/tmp/test/subdir/file.txt"))
		self.assertFalse(is_path_safe(base, "/tmp/test/../other.txt"))
		self.assertFalse(is_path_safe(base, "/etc/passwd"))

	def test_is_path_safe_root(self):
		base = "/"
		self.assertTrue(is_path_safe(base, "/usr/lib/enigma2/python/Plugins/Extensions/Test"))
		self.assertTrue(is_path_safe(base, "/etc/enigma2/userbouquet.tv"))
		self.assertTrue(is_path_safe(base, "/media/hdd/picon"))
		# /root is typically NOT in allowed prefixes
		self.assertFalse(is_path_safe(base, "/root/.bashrc"))
		self.assertFalse(is_path_safe(base, "/home/jules/.bashrc"))

if __name__ == '__main__':
	unittest.main()
