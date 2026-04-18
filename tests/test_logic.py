import unittest
import os
import shutil
import tempfile

def is_path_safe(base, target):
	base = os.path.realpath(base)
	target = os.path.realpath(target)
	if base == os.path.sep:
		return True
	return os.path.commonprefix([base, target]) == base and (len(target) == len(base) or target[len(base)] == os.path.sep)

class TestSecurityLogic(unittest.TestCase):
    def test_path_traversal_detection(self):
        base = "/tmp/plugin_extract"

        # Safe paths
        self.assertTrue(is_path_safe(base, "/tmp/plugin_extract/file.txt"))
        self.assertTrue(is_path_safe(base, "/tmp/plugin_extract/dir/file.txt"))

        # Unsafe paths (traversal)
        self.assertFalse(is_path_safe(base, "/tmp/plugin_extract/../file.txt"))
        self.assertFalse(is_path_safe(base, "/etc/passwd"))

        # Partial name match protection
        self.assertFalse(is_path_safe("/usr", "/usr_backup/file.txt"))

    def test_root_path_safety(self):
        # Root path is always safe (special case in our logic)
        self.assertTrue(is_path_safe("/", "/etc/enigma2/bouquets.tv"))

if __name__ == "__main__":
    unittest.main()
