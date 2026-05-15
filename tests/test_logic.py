import unittest
import os
import sys
import types

# Mock twisted
mock_twisted = types.ModuleType('twisted')
sys.modules['twisted'] = mock_twisted
mock_twisted_web = types.ModuleType('twisted.web')
sys.modules['twisted.web'] = mock_twisted_web
mock_twisted_web_client = types.ModuleType('twisted.web.client')
sys.modules['twisted.web.client'] = mock_twisted_web_client
mock_twisted_web_client.getPage = lambda *args, **kwargs: None
mock_twisted_web_client.downloadPage = lambda *args, **kwargs: None

# Mock enigma2 components properly
def mock_module(name):
    m = types.ModuleType(name)
    sys.modules[name] = m
    return m

class MockBase:
    def __init__(self, *args, **kwargs):
        pass

enigma = mock_module('enigma')
enigma.eDVBDB = types.ModuleType('eDVBDB')

mock_module('Screens')
mock_module('Screens.Screen').Screen = MockBase
mock_module('Screens.MessageBox').MessageBox = types.ModuleType('MessageBox')
mock_module('Screens.InfoBar').InfoBar = types.ModuleType('InfoBar')
mock_module('Screens.TaskView').JobView = types.ModuleType('JobView')
mock_module('Screens.ChoiceBox').ChoiceBox = types.ModuleType('ChoiceBox')
mock_module('Screens.Standby').TryQuitMainloop = types.ModuleType('TryQuitMainloop')

mock_module('Components')
mock_module('Components.Label').Label = types.ModuleType('Label')
mock_module('Components.ActionMap').ActionMap = types.ModuleType('ActionMap')
mock_module('Components.Task')
sys.modules['Components.Task'].Task = MockBase
sys.modules['Components.Task'].Job = MockBase
sys.modules['Components.Task'].job_manager = types.ModuleType('job_manager')
sys.modules['Components.Task'].Condition = MockBase

mock_module('Tools')
mock_module('Tools.Downloader').downloadWithProgress = lambda *args: None
mock_module('Tools.Directories').fileExists = os.path.exists

# Now import our code
sys.path.append(os.path.abspath('src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater'))
from utils import is_path_safe

class TestLogic(unittest.TestCase):
    def test_is_path_safe(self):
        # Base path / should always be safe
        self.assertTrue(is_path_safe('/', '/etc/enigma2/lamedb'))
        self.assertTrue(is_path_safe('/', '/tmp/test'))

        # Specific base path
        base = '/tmp/extract'
        base = os.path.realpath(base)
        self.assertTrue(is_path_safe(base, os.path.join(base, 'file.txt')))
        self.assertTrue(is_path_safe(base, os.path.join(base, 'dir/file.txt')))
        self.assertTrue(is_path_safe(base, base))

        # Path traversal attempts
        self.assertFalse(is_path_safe(base, os.path.join(base, '../other/file.txt')))
        self.assertFalse(is_path_safe(base, '/tmp/other/file.txt'))
        self.assertFalse(is_path_safe(base, '/etc/passwd'))

        # Prefix match exploit
        self.assertFalse(is_path_safe('/tmp/ext', '/tmp/extract/file.txt'))

    def test_version_parsing_logic(self):
        # Simulated version.txt content
        html = "Version = 20240522\nFile = archive.tar.gz\nUrl = http://example.com\nMD5 = abc"
        lines = html.split("\n")
        newVersion = None
        for path in lines:
            if path.split(" = ")[0] == "Version":
                newVersion = path.split("=")[1].replace('"', "").strip()
        self.assertEqual(newVersion, "20240522")

if __name__ == '__main__':
    unittest.main()
