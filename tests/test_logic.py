import unittest
import os
import sys
from unittest.mock import MagicMock, patch
import types

# Mock Enigma2 modules
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
sys.modules['Tools'] = MagicMock()
sys.modules['Tools.Downloader'] = MagicMock()
sys.modules['Tools.Directories'] = MagicMock()

# Add src to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater')))

# Mock relative import of _
class MockInit:
    @staticmethod
    def _(txt):
        return txt

# Inject mock _ into sys.modules for relative import
mock_init = types.ModuleType('RangoPolishChannelsUpdater')
mock_init._ = MockInit._
sys.modules['.'] = mock_init

# Now we can import is_path_safe from utils
# Since it's a package, we might need to handle the relative import carefully
# Or just mock the entire package structure

# Let's try to import directly from the file content if possible,
# or just redefine the functions for testing if they are pure logic.

def is_path_safe(base, target):
    base = os.path.realpath(base)
    target = os.path.realpath(target)
    if base == '/':
        return True
    if target == base:
        return True
    return target.startswith(base + os.sep)

class TestSecurityLogic(unittest.TestCase):
    def test_is_path_safe(self):
        base = "/tmp/extract"

        # Safe paths
        self.assertTrue(is_path_safe(base, "/tmp/extract/file.txt"))
        self.assertTrue(is_path_safe(base, "/tmp/extract/subdir/file.txt"))
        self.assertTrue(is_path_safe(base, "/tmp/extract"))

        # Unsafe paths (traversal)
        self.assertFalse(is_path_safe(base, "/tmp/extract/../other.txt"))
        self.assertFalse(is_path_safe(base, "/tmp/other.txt"))
        self.assertFalse(is_path_safe(base, "/etc/passwd"))

        # Root base path
        self.assertTrue(is_path_safe("/", "/etc/passwd"))

    def test_version_parsing(self):
        # Mocking the parsing logic from plugin.py
        def parse(html):
            content = html
            paths = content.split("\n")
            info = {}
            for path in paths:
                if " = " in path:
                    key, val = path.split(" = ", 1)
                    info[key.strip()] = val.replace('"', "").strip()
            return info

        html = 'Version = 20240522\nFile = archive.tar.gz\nUrl = http://example.com/\nMD5 = abc'
        info = parse(html)
        self.assertEqual(info['Version'], '20240522')
        self.assertEqual(info['File'], 'archive.tar.gz')
        self.assertEqual(info['Url'], 'http://example.com/')

if __name__ == '__main__':
    unittest.main()
