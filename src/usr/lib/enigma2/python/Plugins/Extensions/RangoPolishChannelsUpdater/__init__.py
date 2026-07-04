from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os, gettext

def localeInit():
	lang = language.getLanguage()[:2]
	os.environ["LANGUAGE"] = lang
	gettext.bindtextdomain("RangoPolishChannelsUpdater", resolveFilename(SCOPE_PLUGINS, "Extensions/RangoPolishChannelsUpdater/locale"))

def _(txt):
	t = gettext.dgettext("RangoPolishChannelsUpdater", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)
