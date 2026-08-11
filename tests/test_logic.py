import sys
import os
from types import ModuleType

# Mock Enigma2 components
enigma = ModuleType('enigma')
enigma.getDesktop = lambda x: type('Desktop', (), {'size': lambda: type('Size', (), {'width': lambda: 1920})()})()
enigma.eDVBDB = type('eDVBDB', (), {'getInstance': lambda: type('Instance', (), {'removeServices': lambda: None, 'reloadServicelist': lambda: None, 'reloadBouquets': lambda: None})()})
sys.modules['enigma'] = enigma

components_label = ModuleType('Components.Label')
components_label.Label = type('Label', (), {'__init__': lambda self, x: None, 'setText': lambda self, x: None, 'hide': lambda self: None, 'show': lambda self: None})
sys.modules['Components.Label'] = components_label

components_actionmap = ModuleType('Components.ActionMap')
components_actionmap.ActionMap = type('ActionMap', (), {'__init__': lambda self, x, y, z=None: None})
sys.modules['Components.ActionMap'] = components_actionmap

components_sources_list = ModuleType('Components.Sources.List')
components_sources_list.List = type('List', (), {'__init__': lambda self, x: None})
sys.modules['Components.Sources.List'] = components_sources_list

components_pluginlist = ModuleType('Components.PluginList')
components_pluginlist.resolveFilename = lambda x, y=None: "/tmp/"
sys.modules['Components.PluginList'] = components_pluginlist

components_sources_progress = ModuleType('Components.Sources.Progress')
components_sources_progress.Progress = type('Progress', (), {'__init__': lambda self: None})
sys.modules['Components.Sources.Progress'] = components_sources_progress

components_sources_statictext = ModuleType('Components.Sources.StaticText')
components_sources_statictext.StaticText = type('StaticText', (), {'__init__': lambda self: None})
sys.modules['Components.Sources.StaticText'] = components_sources_statictext

screens_standby = ModuleType('Screens.Standby')
screens_standby.TryQuitMainloop = type('TryQuitMainloop', (), {})
sys.modules['Screens.Standby'] = screens_standby

screens_messagebox = ModuleType('Screens.MessageBox')
screens_messagebox.MessageBox = type('MessageBox', (), {'TYPE_INFO': 0, 'TYPE_YESNO': 1})
sys.modules['Screens.MessageBox'] = screens_messagebox

screens_screen = ModuleType('Screens.Screen')
class MockScreen:
    def __init__(self, *args, **kwargs): pass
    def setTitle(self, title): pass
screens_screen.Screen = MockScreen
sys.modules['Screens.Screen'] = screens_screen

tools_loadpixmap = ModuleType('Tools.LoadPixmap')
tools_loadpixmap.LoadPixmap = lambda x: None
sys.modules['Tools.LoadPixmap'] = tools_loadpixmap

tools_directories = ModuleType('Tools.Directories')
tools_directories.fileExists = os.path.exists
tools_directories.SCOPE_PLUGINS = 0
sys.modules['Tools.Directories'] = tools_directories

tools_downloader = ModuleType('Tools.Downloader')
tools_downloader.downloadWithProgress = lambda x, y: None
sys.modules['Tools.Downloader'] = tools_downloader

plugins_plugin = ModuleType('Plugins.Plugin')
plugins_plugin.PluginDescriptor = type('PluginDescriptor', (), {'__init__': lambda *args, **kwargs: None, 'WHERE_MENU': 0, 'WHERE_PLUGINMENU': 1})
sys.modules['Plugins.Plugin'] = plugins_plugin

# Mock more from utils
sys.modules['Screens.InfoBar'] = ModuleType('Screens.InfoBar')
sys.modules['Screens.InfoBar'].InfoBar = type('InfoBar', (), {'instance': None})
sys.modules['Screens.TaskView'] = ModuleType('Screens.TaskView')
sys.modules['Screens.TaskView'].JobView = type('JobView', (), {})
sys.modules['Screens.ChoiceBox'] = ModuleType('Screens.ChoiceBox')
sys.modules['Screens.ChoiceBox'].ChoiceBox = type('ChoiceBox', (), {})
sys.modules['Components.Task'] = ModuleType('Components.Task')
sys.modules['Components.Task'].Task = type('Task', (), {})
sys.modules['Components.Task'].Job = type('Job', (), {})
sys.modules['Components.Task'].job_manager = type('job_manager', (), {})
sys.modules['Components.Task'].Condition = type('Condition', (), {})

# Mock twisted.web.client
twisted_web_client = ModuleType('twisted.web.client')
twisted_web_client.getPage = lambda *args, **kwargs: None
twisted_web_client.downloadPage = lambda *args, **kwargs: None
sys.modules['twisted.web.client'] = twisted_web_client

# Define global _ for localization
import builtins
builtins._ = lambda x: x

# Import our code
sys.path.append(os.path.abspath('src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater'))
import utils

def test_path_safety():
    print("Testing path safety...")
    base = "/tmp/test"
    os.makedirs(base, exist_ok=True)

    assert utils.is_path_safe(base, "/tmp/test/file.txt") == True
    assert utils.is_path_safe(base, "/tmp/test/subdir/file.txt") == True
    assert utils.is_path_safe(base, "/tmp/test/../other/file.txt") == False
    assert utils.is_path_safe(base, "/etc/passwd") == False
    print("Path safety tests passed!")

def test_version_parsing():
    print("Testing version parsing logic...")
    # Mocking a subset of what plugin.py does
    html = b"[plugin]\nVersion = 20240522\nFile = rango.tar.gz\nUrl = http://test.com/\nMD5 = abc"

    import io
    try:
        import configparser as ConfigParser
    except:
        import ConfigParser

    content = html.decode('utf-8')
    config = ConfigParser.ConfigParser()
    config.read_file(io.StringIO(content))

    assert config.get("plugin", "Version") == "20240522"
    assert config.get("plugin", "File") == "rango.tar.gz"
    print("Version parsing tests passed!")

if __name__ == "__main__":
    try:
        test_path_safety()
        test_version_parsing()
        print("All tests passed!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Tests failed: {e}")
        sys.exit(1)
