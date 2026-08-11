import os
import sys
import unittest
import shutil
import tarfile
import zipfile
from io import StringIO
import types

# Mock twisted.web.client before it's imported in utils
mock_twisted = types.ModuleType('twisted')
mock_twisted_web = types.ModuleType('twisted.web')
mock_twisted_web_client = types.ModuleType('twisted.web.client')
mock_twisted_web_client.getPage = lambda x: None
mock_twisted_web_client.downloadPage = lambda x, y: None
sys.modules['twisted'] = mock_twisted
sys.modules['twisted.web'] = mock_twisted_web
sys.modules['twisted.web.client'] = mock_twisted_web_client

# Mock Enigma2 modules
mock_enigma = types.ModuleType('enigma')
mock_enigma.eDVBDB = types.ModuleType('eDVBDB')
mock_enigma.getDesktop = lambda x: None
sys.modules['enigma'] = mock_enigma

mock_components = types.ModuleType('Components')
mock_components.__path__ = []
mock_components.Label = types.ModuleType('Label')
mock_components.Label.Label = lambda x: None
mock_components.ActionMap = types.ModuleType('ActionMap')
mock_components.ActionMap.ActionMap = lambda x, y, z=None: None
mock_components.Sources = types.ModuleType('Sources')
mock_components.Sources.__path__ = []
mock_components.Sources.List = types.ModuleType('List')
mock_components.Sources.List.List = lambda x: None
mock_components.PluginList = types.ModuleType('PluginList')
mock_components.PluginList.resolveFilename = lambda x, y=None: ""
mock_components.Sources.Progress = types.ModuleType('Progress')
mock_components.Sources.Progress.Progress = lambda: None
mock_components.Sources.StaticText = types.ModuleType('StaticText')
mock_components.Sources.StaticText.StaticText = lambda: None
mock_components.Task = types.ModuleType('Task')
mock_components.Task.Task = object
mock_components.Task.Job = object
mock_components.Task.job_manager = None
mock_components.Task.Condition = object
sys.modules['Components'] = mock_components
sys.modules['Components.Label'] = mock_components.Label
sys.modules['Components.ActionMap'] = mock_components.ActionMap
sys.modules['Components.Sources'] = mock_components.Sources
sys.modules['Components.Sources.List'] = mock_components.Sources.List
sys.modules['Components.PluginList'] = mock_components.PluginList
sys.modules['Components.Sources.Progress'] = mock_components.Sources.Progress
sys.modules['Components.Sources.StaticText'] = mock_components.Sources.StaticText
sys.modules['Components.Task'] = mock_components.Task

mock_screens = types.ModuleType('Screens')
mock_screens.__path__ = []
mock_screens.Screen = types.ModuleType('Screen')
class MockScreen:
    def __init__(self, *args, **kwargs): pass
    def setTitle(self, *args): pass
mock_screens.Screen.Screen = MockScreen
mock_screens.MessageBox = types.ModuleType('MessageBox')
mock_screens.MessageBox.MessageBox = MockScreen
mock_screens.Standby = types.ModuleType('Standby')
mock_screens.Standby.TryQuitMainloop = MockScreen
mock_screens.InfoBar = types.ModuleType('InfoBar')
mock_screens.InfoBar.InfoBar = MockScreen
mock_screens.TaskView = types.ModuleType('TaskView')
mock_screens.TaskView.JobView = MockScreen
mock_screens.ChoiceBox = types.ModuleType('ChoiceBox')
mock_screens.ChoiceBox.ChoiceBox = MockScreen
sys.modules['Screens'] = mock_screens
sys.modules['Screens.Screen'] = mock_screens.Screen
sys.modules['Screens.MessageBox'] = mock_screens.MessageBox
sys.modules['Screens.Standby'] = mock_screens.Standby
sys.modules['Screens.InfoBar'] = mock_screens.InfoBar
sys.modules['Screens.TaskView'] = mock_screens.TaskView
sys.modules['Screens.ChoiceBox'] = mock_screens.ChoiceBox

mock_tools = types.ModuleType('Tools')
mock_tools.__path__ = []
mock_tools.LoadPixmap = types.ModuleType('LoadPixmap')
mock_tools.Directories = types.ModuleType('Directories')
mock_tools.Directories.fileExists = os.path.exists
mock_tools.Directories.SCOPE_PLUGINS = 0
mock_tools.Downloader = types.ModuleType('Downloader')
mock_tools.Downloader.downloadWithProgress = lambda x, y: None
sys.modules['Tools'] = mock_tools
sys.modules['Tools.LoadPixmap'] = mock_tools.LoadPixmap
sys.modules['Tools.Directories'] = mock_tools.Directories
sys.modules['Tools.Downloader'] = mock_tools.Downloader

mock_plugins = types.ModuleType('Plugins')
mock_plugins.Plugin = types.ModuleType('Plugin')
sys.modules['Plugins'] = mock_plugins
sys.modules['Plugins.Plugin'] = mock_plugins.Plugin

# Add src to sys.path
src_path = os.path.join(os.getcwd(), 'src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater')
sys.path.append(src_path)

import utils

class TestLogic(unittest.TestCase):
    def test_is_path_safe(self):
        self.assertTrue(utils.is_path_safe('/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater/plugin.py', '/'))
        self.assertTrue(utils.is_path_safe('/etc/enigma2/userbouquet.tv', '/'))
        self.assertFalse(utils.is_path_safe('/root/.ssh/authorized_keys', '/'))
        self.assertTrue(utils.is_path_safe('/tmp/test', '/tmp'))
        self.assertFalse(utils.is_path_safe('/tmp/../etc/passwd', '/tmp'))

    def test_safe_tar_extract(self):
        # Create a malicious tarball
        tar_path = 'malicious.tar.gz'
        from io import BytesIO
        with tarfile.open(tar_path, 'w:gz') as tar:
            # Safe member
            safe_file = 'safe.txt'
            with open(safe_file, 'wb') as f: f.write(b'safe')
            tar.add(safe_file)

            # Malicious member
            malicious_member = tarfile.TarInfo(name='../../tmp/evil.txt')
            malicious_member.size = 4
            tar.addfile(malicious_member, BytesIO(b'evil'))

        extract_path = 'extract_test'
        os.makedirs(extract_path, exist_ok=True)

        with tarfile.open(tar_path, 'r:gz') as tar:
            utils.safe_tar_extract(tar, extract_path)

        self.assertTrue(os.path.exists(os.path.join(extract_path, 'safe.txt')))
        self.assertFalse(os.path.exists('/tmp/evil.txt'))
        self.assertFalse(os.path.exists(os.path.join(extract_path, '../../tmp/evil.txt')))

        # Cleanup
        os.remove(tar_path)
        os.remove(safe_file)
        shutil.rmtree(extract_path)

    def test_config_parsing(self):
        content = "[plugin]\nVersion = 20240522\nFile = test.tar.gz\nUrl = http://example.com\nMD5 = abc"
        import configparser as ConfigParser
        import io
        config = ConfigParser.ConfigParser()
        config.read_file(io.StringIO(content))
        self.assertEqual(config.get('plugin', 'Version'), '20240522')

if __name__ == '__main__':
    unittest.main()
