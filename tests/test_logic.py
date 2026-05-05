import unittest
import os
import sys
from types import ModuleType

# Mock Twisted before it's imported
mock_twisted = ModuleType('twisted')
sys.modules['twisted'] = mock_twisted
mock_twisted_web = ModuleType('twisted.web')
sys.modules['twisted.web'] = mock_twisted_web
mock_twisted_web_client = ModuleType('twisted.web.client')
sys.modules['twisted.web.client'] = mock_twisted_web_client
mock_twisted_web_client.getPage = lambda x: None
mock_twisted_web_client.downloadPage = lambda x, y: None

# Comprehensive Mocking for Enigma2 environment
def mock_package(name):
    m = ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
    return m

mock_enigma = mock_package('enigma')
mock_enigma.eDVBDB = type('eDVBDB', (object,), {'getInstance': lambda: None})
mock_enigma.getDesktop = lambda x: None

mock_screens = mock_package('Screens')
mock_screens_screen = mock_package('Screens.Screen')
mock_screens_screen.Screen = type('Screen', (object,), {})

mock_screens_msg = mock_package('Screens.MessageBox')
mock_screens_msg.MessageBox = type('MessageBox', (object,), {})

mock_screens_infobar = mock_package('Screens.InfoBar')
mock_screens_infobar.InfoBar = type('InfoBar', (object,), {'instance': None})

mock_screens_task = mock_package('Screens.TaskView')
mock_screens_task.JobView = type('JobView', (object,), {})

mock_screens_choice = mock_package('Screens.ChoiceBox')
mock_screens_choice.ChoiceBox = type('ChoiceBox', (object,), {})

mock_screens_standby = mock_package('Screens.Standby')
mock_screens_standby.TryQuitMainloop = type('TryQuitMainloop', (object,), {})

mock_comp = mock_package('Components')
mock_comp_label = mock_package('Components.Label')
mock_comp_label.Label = type('Label', (object,), {})

mock_comp_action = mock_package('Components.ActionMap')
mock_comp_action.ActionMap = type('ActionMap', (object,), {})

mock_comp_task = mock_package('Components.Task')
mock_comp_task.Task = type('Task', (object,), {})
mock_comp_task.Job = type('Job', (object,), {})
mock_comp_task.job_manager = None
mock_comp_task.Condition = type('Condition', (object,), {})

mock_tools = mock_package('Tools')
mock_tools_down = mock_package('Tools.Downloader')
mock_tools_down.downloadWithProgress = None

mock_tools_dir = mock_package('Tools.Directories')
mock_tools_dir.fileExists = lambda x: True

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater')))

from utils import is_path_safe

class TestSecurityLogic(unittest.TestCase):
    def test_is_path_safe(self):
        # Test with standard base
        base = "/tmp/plugin"
        base = os.path.realpath(base)

        self.assertTrue(is_path_safe(os.path.join(base, "file.txt"), base))
        self.assertTrue(is_path_safe(base, base))
        self.assertFalse(is_path_safe("/etc/passwd", base))
        self.assertFalse(is_path_safe(os.path.join(base, "../other/file.txt"), base))
        self.assertFalse(is_path_safe("/tmp/plugin_suffix", base))

        # Test with root base (important fix!)
        self.assertTrue(is_path_safe("/usr/lib/enigma2", "/"))
        self.assertTrue(is_path_safe("/etc/enigma2", "/"))
        self.assertTrue(is_path_safe("/", "/"))

    def test_bytes_decoding_simulation(self):
        # Simulate the fix for Python 3 bytes handling
        html_bytes = b"version:20240522\nurl:http://example.com"
        if isinstance(html_bytes, bytes):
            html_str = html_bytes.decode('utf-8')
        else:
            html_str = str(html_bytes)

        self.assertEqual(html_str, "version:20240522\nurl:http://example.com")

        new = dict([ l.split(':',1) for l in html_str.split("\n") if l.find(":") > 0])
        self.assertEqual(new['version'], '20240522')

if __name__ == '__main__':
    unittest.main()
