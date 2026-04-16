import sys
import os
import types
import unittest
from unittest.mock import MagicMock

# Mocking Enigma2 modules
def mock_module(name):
    m = types.ModuleType(name)
    sys.modules[name] = m
    return m

enigma = mock_module("enigma")
enigma.getDesktop = MagicMock()
enigma.getDesktop.return_value.size.return_value.width.return_value = 1920
enigma.RT_HALIGN_LEFT = 0
enigma.RT_VALIGN_TOP = 0
enigma.gFont = MagicMock()
enigma.eDVBDB = MagicMock()

mock_module("Components")
components_label = mock_module("Components.Label")
components_label.Label = MagicMock()
components_actionmap = mock_module("Components.ActionMap")
components_actionmap.ActionMap = MagicMock()
components_sources_list = mock_module("Components.Sources.List")
components_sources_list.List = MagicMock()
components_sources_progress = mock_module("Components.Sources.Progress")
components_sources_progress.Progress = MagicMock()
components_sources_statictext = mock_module("Components.Sources.StaticText")
components_sources_statictext.StaticText = MagicMock()
components_multicontent = mock_module("Components.MultiContent")
components_multicontent.MultiContentEntryText = MagicMock()
components_multicontent.MultiContentEntryPixmapAlphaBlend = MagicMock()
components_pluginlist = mock_module("Components.PluginList")
components_pluginlist.resolveFilename = MagicMock(return_value="/usr/lib/enigma2/python/Plugins/")
components_language = mock_module("Components.Language")
components_language.language = MagicMock()

mock_module("Screens")
screens_screen = mock_module("Screens.Screen")
screens_screen.Screen = MagicMock()
screens_standby = mock_module("Screens.Standby")
screens_standby.TryQuitMainloop = MagicMock()
screens_messagebox = mock_module("Screens.MessageBox")
screens_messagebox.MessageBox = MagicMock()
screens_infobar = mock_module("Screens.InfoBar")
screens_infobar.InfoBar = MagicMock()
screens_taskview = mock_module("Screens.TaskView")
screens_taskview.JobView = MagicMock()
screens_choicebox = mock_module("Screens.ChoiceBox")
screens_choicebox.ChoiceBox = MagicMock()

mock_module("Tools")
tools_loadpixmap = mock_module("Tools.LoadPixmap")
tools_loadpixmap.LoadPixmap = MagicMock()
tools_directories = mock_module("Tools.Directories")
tools_directories.fileExists = MagicMock(return_value=True)
tools_directories.SCOPE_PLUGINS = "plugins"
tools_directories.SCOPE_LANGUAGE = "language"
tools_directories.resolveFilename = MagicMock(return_value="/usr/lib/enigma2/python/Plugins/")
tools_downloader = mock_module("Tools.Downloader")
tools_downloader.downloadWithProgress = MagicMock()

mock_module("Plugins")
mock_module("Plugins.Plugin")
plugins_plugin = mock_module("Plugins.Plugin")
plugins_plugin.PluginDescriptor = MagicMock()

mock_module("Components.Task")
components_task = mock_module("Components.Task")
components_task.Task = MagicMock()
components_task.Job = MagicMock()
components_task.job_manager = MagicMock()
components_task.Condition = MagicMock()

# Mocking Twisted
twisted = mock_module("twisted")
twisted_web = mock_module("twisted.web")
twisted_web_client = mock_module("twisted.web.client")
twisted_web_client.getPage = MagicMock()
twisted_web_client.downloadPage = MagicMock()

# Add src/usr/lib/enigma2/python/Plugins/Extensions to sys.path
sys.path.append(os.path.join(os.getcwd(), 'src/usr/lib/enigma2/python/Plugins/Extensions'))

from RangoPolishChannelsUpdater import utils

class TestLogic(unittest.TestCase):
    def test_is_path_safe(self):
        self.assertTrue(utils.is_path_safe("/tmp", "/tmp/file.txt"))
        self.assertTrue(utils.is_path_safe("/tmp", "/tmp/subdir/file.txt"))
        self.assertFalse(utils.is_path_safe("/tmp", "/tmp/../etc/passwd"))
        self.assertFalse(utils.is_path_safe("/tmp", "/etc/passwd"))
        # Test root base
        self.assertTrue(utils.is_path_safe("/", "/usr/bin/enigma2"))
        self.assertTrue(utils.is_path_safe("/", "/etc/enigma2/settings"))
        self.assertFalse(utils.is_path_safe("/", "/bin/sh")) # Not in allowed prefixes

    def test_version_parsing(self):
        import io
        try:
            import configparser
        except ImportError:
            import ConfigParser as configparser

        content = "[plugin]\nVersion = 20240522\nFile = test.tar.gz\nUrl = http://test.com\nMD5 = abc"
        config = configparser.ConfigParser()
        if hasattr(config, 'read_file'):
            config.read_file(io.StringIO(content))
        else:
            config.readfp(io.StringIO(content))

        self.assertEqual(config.get('plugin', 'Version'), "20240522")

if __name__ == '__main__':
    unittest.main()
