import unittest
import os
import sys
import tarfile
import zipfile
import shutil
from io import BytesIO, StringIO
from unittest.mock import MagicMock, patch, mock_open

# Mocking Enigma2 modules
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

# Mocking twisted
sys.modules['twisted'] = MagicMock()
sys.modules['twisted.web'] = MagicMock()
sys.modules['twisted.web.client'] = MagicMock()

# Import the code to test
# We need to adjust sys.path to find the module
plugin_path = os.path.abspath('src/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater')
sys.path.append(plugin_path)

import utils

class TestUtils(unittest.TestCase):
    def test_is_path_safe(self):
        self.assertTrue(utils.is_path_safe('/tmp', '/tmp/test.txt'))
        self.assertFalse(utils.is_path_safe('/tmp', '/etc/passwd'))
        self.assertTrue(utils.is_path_safe('/', '/usr/lib/enigma2'))
        # /bin/sh on this system might resolve to /usr/bin/dash which IS allowed.
        # Let's use something definitely not allowed if it exists, or just a dummy path.
        self.assertFalse(utils.is_path_safe('/', '/root/.ssh'))
        self.assertTrue(utils.is_path_safe('/', '/hdd/picon'))

    def test_safe_tar_extract_traversal(self):
        # Create a malicious tar file in memory
        tar_data = BytesIO()
        with tarfile.open(fileobj=tar_data, mode='w:gz') as tar:
            tarinfo = tarfile.TarInfo(name='../../etc/passwd')
            tarinfo.size = 0
            tar.addfile(tarinfo, BytesIO())
        tar_data.seek(0)

        with tarfile.open(fileobj=tar_data, mode='r:gz') as tar:
            with self.assertRaises(Exception) as cm:
                utils.safe_tar_extract(tar, '/tmp')
            self.assertEqual(str(cm.exception), "Attempted Path Traversal in Tar File")

    def test_safe_zip_extract_traversal(self):
        # Create a malicious zip file in memory
        zip_data = BytesIO()
        with zipfile.ZipFile(zip_data, mode='w') as zf:
            zf.writestr('../../etc/passwd', 'content')
        zip_data.seek(0)

        with zipfile.ZipFile(zip_data, mode='r') as zf:
            with self.assertRaises(Exception) as cm:
                utils.safe_zip_extract(zf, '/tmp')
            self.assertEqual(str(cm.exception), "Attempted Path Traversal in Zip File")

if __name__ == '__main__':
    unittest.main()
