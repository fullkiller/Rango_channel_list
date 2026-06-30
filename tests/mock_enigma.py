import sys
from unittest.mock import MagicMock
import types

# Define a Screen base class for inheritance
class Screen:
    def __init__(self, *args, **kwargs):
        self.skin = ""
    def __getitem__(self, key):
        return MagicMock()
    def __setitem__(self, key, value):
        pass
    def setTitle(self, title):
        pass
    def close(self, *args, **kwargs):
        pass

class MockEnigma:
    def getDesktop(self, num):
        desktop = MagicMock()
        desktop.size().width.return_value = 1920
        return desktop
    def gFont(self, name, size): return name
    RT_HALIGN_LEFT = 0
    RT_VALIGN_TOP = 0
    def eDVBDB(self): return MagicMock()

sys.modules['enigma'] = MockEnigma()

def mock_pkg(name):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
    return m

comp = mock_pkg('Components')
comp_label = mock_pkg('Components.Label')
comp_label.Label = MagicMock
comp_am = mock_pkg('Components.ActionMap')
comp_am.ActionMap = MagicMock
comp_sources = mock_pkg('Components.Sources')
comp_sources_list = mock_pkg('Components.Sources.List')
comp_sources_list.List = MagicMock
comp_sources_progress = mock_pkg('Components.Sources.Progress')
comp_sources_progress.Progress = MagicMock
comp_sources_st = mock_pkg('Components.Sources.StaticText')
comp_sources_st.StaticText = MagicMock
comp_task = mock_pkg('Components.Task')
comp_task.Task = MagicMock
comp_task.Job = MagicMock
comp_task.job_manager = MagicMock
comp_task.Condition = MagicMock

screens = mock_pkg('Screens')
screens_screen = mock_pkg('Screens.Screen')
screens_screen.Screen = Screen
screens_mb = mock_pkg('Screens.MessageBox')
screens_mb.MessageBox = MagicMock
screens_standby = mock_pkg('Screens.Standby')
screens_standby.TryQuitMainloop = MagicMock
screens_infobar = mock_pkg('Screens.InfoBar')
screens_infobar.InfoBar = MagicMock
screens_tv = mock_pkg('Screens.TaskView')
screens_tv.JobView = MagicMock
screens_cb = mock_pkg('Screens.ChoiceBox')
screens_cb.ChoiceBox = MagicMock

tools = mock_pkg('Tools')
tools_lp = mock_pkg('Tools.LoadPixmap')
tools_lp.LoadPixmap = MagicMock
tools_dir = mock_pkg('Tools.Directories')
tools_dir.fileExists = MagicMock(return_value=True)
tools_dir.SCOPE_PLUGINS = "plugins"
tools_dir.resolveFilename = MagicMock(return_value="resolved")
tools_dl = mock_pkg('Tools.Downloader')
tools_dl.downloadWithProgress = MagicMock

plugins = mock_pkg('Plugins')
plugins_p = mock_pkg('Plugins.Plugin')
plugins_p.PluginDescriptor = MagicMock

# twisted
twisted = mock_pkg('twisted')
twisted_web = mock_pkg('twisted.web')
twisted_web_client = mock_pkg('twisted.web.client')
twisted_web_client.getPage = MagicMock
twisted_web_client.downloadPage = MagicMock

def _(text): return text
import builtins
builtins._ = _
