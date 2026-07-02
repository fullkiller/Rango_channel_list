import sys
from unittest.mock import MagicMock

def getPage(url, *args, **kwargs):
    return MagicMock()

def downloadPage(url, filename, *args, **kwargs):
    return MagicMock()

sys.modules['twisted'] = MagicMock()
sys.modules['twisted.web'] = MagicMock()
sys.modules['twisted.web.client'] = MagicMock()
sys.modules['twisted.web.client'].getPage = getPage
sys.modules['twisted.web.client'].downloadPage = downloadPage
