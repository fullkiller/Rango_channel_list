import unittest
import os
import sys
from types import ModuleType

# Improved Mocking
def mock_module(name, **kwargs):
    m = ModuleType(name)
    for k, v in kwargs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m

mock_module('enigma', eDVBDB=ModuleType('eDVBDB'))
mock_module('Screens.Screen', Screen=object)
mock_module('Screens.MessageBox', MessageBox=object)
mock_module('Screens.InfoBar', InfoBar=object)
mock_module('Screens.TaskView', JobView=object)
mock_module('Screens.ChoiceBox', ChoiceBox=object)
mock_module('Screens.Standby', TryQuitMainloop=object)

mock_module('Components.Label', Label=object)
mock_module('Components.ActionMap', ActionMap=object)
mock_module('Components.Task', Task=object, Job=object, job_manager=object, Condition=object)

mock_module('Tools.Downloader', downloadWithProgress=lambda x, y: None)
mock_module('Tools.Directories', fileExists=os.path.exists)

mock_module('twisted.web.client', getPage=lambda x: None, downloadPage=lambda x, y: None)

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater')))

# Now we can import the logic we want to test
from utils import is_path_safe

class TestLogic(unittest.TestCase):
    def test_is_path_safe(self):
        # In sandbox, we should use paths that exist or can be resolved
        # is_path_safe uses realpath
        base = os.path.abspath("/tmp")
        self.assertTrue(is_path_safe(base, os.path.join(base, "file.txt")))
        self.assertTrue(is_path_safe("/", "/etc/enigma2/lamedb"))
        self.assertTrue(is_path_safe(base, base))

        # Test path traversal attempt
        traversal_target = os.path.join(base, "subdir/../outside.txt")
        # resolved traversal_target will be /tmp/outside.txt which IS under /tmp
        # So we need a better example

        base_dir = os.path.abspath("/tmp/myplugin")
        if not os.path.exists(base_dir): os.makedirs(base_dir)

        safe_path = os.path.join(base_dir, "safe.txt")
        unsafe_path = os.path.join(base_dir, "../unsafe.txt")

        self.assertTrue(is_path_safe(base_dir, safe_path))
        self.assertFalse(is_path_safe(base_dir, unsafe_path))

    def test_version_parsing(self):
        line = "DATE=20240522\n"
        if "=" in line:
            key = line.split("=")[0].strip()
            val = line.split("=")[1].strip()
            self.assertEqual(key, "DATE")
            self.assertEqual(val, "20240522")

if __name__ == '__main__':
    unittest.main()
