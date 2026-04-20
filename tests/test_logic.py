import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import types

# Mock Twisted before it's imported
twisted = types.ModuleType('twisted')
sys.modules['twisted'] = twisted
twisted_web = types.ModuleType('twisted.web')
sys.modules['twisted.web'] = twisted_web
twisted_web_client = types.ModuleType('twisted.web.client')
twisted_web_client.getPage = MagicMock()
twisted_web_client.downloadPage = MagicMock()
sys.modules['twisted.web.client'] = twisted_web_client

# Mock Enigma2 modules
enigma = types.ModuleType('enigma')
enigma.getDesktop = MagicMock()
enigma.eDVBDB = MagicMock()
sys.modules['enigma'] = enigma

components_label = types.ModuleType('Components.Label')
components_label.Label = MagicMock
sys.modules['Components.Label'] = components_label

components_actionmap = types.ModuleType('Components.ActionMap')
components_actionmap.ActionMap = MagicMock
sys.modules['Components.ActionMap'] = components_actionmap

components_sources_list = types.ModuleType('Components.Sources.List')
components_sources_list.List = MagicMock
sys.modules['Components.Sources.List'] = components_sources_list

components_pluginlist = types.ModuleType('Components.PluginList')
components_pluginlist.resolveFilename = MagicMock(return_value="/tmp/")
sys.modules['Components.PluginList'] = components_pluginlist

components_sources_progress = types.ModuleType('Components.Sources.Progress')
components_sources_progress.Progress = MagicMock
sys.modules['Components.Sources.Progress'] = components_sources_progress

components_sources_statictext = types.ModuleType('Components.Sources.StaticText')
components_sources_statictext.StaticText = MagicMock
sys.modules['Components.Sources.StaticText'] = components_sources_statictext

components_task = types.ModuleType('Components.Task')
components_task.Task = MagicMock
components_task.Job = MagicMock
components_task.job_manager = MagicMock
components_task.Condition = MagicMock
sys.modules['Components.Task'] = components_task

screens_standby = types.ModuleType('Screens.Standby')
screens_standby.TryQuitMainloop = MagicMock
sys.modules['Screens.Standby'] = screens_standby

screens_messagebox = types.ModuleType('Screens.MessageBox')
screens_messagebox.MessageBox = MagicMock
sys.modules['Screens.MessageBox'] = screens_messagebox

screens_screen = types.ModuleType('Screens.Screen')
screens_screen.Screen = MagicMock
sys.modules['Screens.Screen'] = screens_screen

screens_infobar = types.ModuleType('Screens.InfoBar')
screens_infobar.InfoBar = MagicMock()
sys.modules['Screens.InfoBar'] = screens_infobar

screens_taskview = types.ModuleType('Screens.TaskView')
screens_taskview.JobView = MagicMock
sys.modules['Screens.TaskView'] = screens_taskview

screens_choicebox = types.ModuleType('Screens.ChoiceBox')
screens_choicebox.ChoiceBox = MagicMock
sys.modules['Screens.ChoiceBox'] = screens_choicebox

tools_loadpixmap = types.ModuleType('Tools.LoadPixmap')
tools_loadpixmap.LoadPixmap = MagicMock
sys.modules['Tools.LoadPixmap'] = tools_loadpixmap

tools_directories = types.ModuleType('Tools.Directories')
tools_directories.fileExists = os.path.exists
tools_directories.SCOPE_PLUGINS = 1
sys.modules['Tools.Directories'] = tools_directories

tools_downloader = types.ModuleType('Tools.Downloader')
tools_downloader.downloadWithProgress = MagicMock
sys.modules['Tools.Downloader'] = tools_downloader

plugins_plugin = types.ModuleType('Plugins.Plugin')
plugins_plugin.PluginDescriptor = MagicMock
sys.modules['Plugins.Plugin'] = plugins_plugin

# Add src to path
sys.path.append(os.path.abspath('src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater'))

from utils import is_path_safe

class TestLogic(unittest.TestCase):
    def test_is_path_safe(self):
        # Test safe paths
        self.assertTrue(is_path_safe('/tmp', '/tmp/file.txt'))
        self.assertTrue(is_path_safe('/etc/enigma2', '/etc/enigma2/lamedb'))
        self.assertTrue(is_path_safe('/', '/usr/lib/enigma2'))

        # Test unsafe paths (traversal)
        self.assertFalse(is_path_safe('/tmp', '/tmp/../etc/passwd'))
        self.assertFalse(is_path_safe('/etc/enigma2', '/etc/enigma2/../../etc/passwd'))

    def test_version_parsing(self):
        html = "version:20240522\nurl:http://example.com/file.tgz"
        new = dict([ l.split(':',1) for l in html.split("\n") if l.find(":") > 0])
        self.assertEqual(new['version'], '20240522')
        self.assertEqual(new['url'], 'http://example.com/file.tgz')
        self.assertTrue('version' in new)

if __name__ == '__main__':
    unittest.main()
