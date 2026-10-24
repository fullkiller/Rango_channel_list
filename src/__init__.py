# -*- coding: utf-8 -*-
try:
	from Components.Language import language
	from Tools.Directories import resolveFilename, SCOPE_PLUGINS
	import gettext

	PluginLanguageDomain = "RangoPolishChannelsUpdater"
	PluginLanguagePath = "Extensions/RangoPolishChannelsUpdater/locale"

	def localeInit(lang=None):
		gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

	def _(txt):
		t = gettext.dgettext(PluginLanguageDomain, txt)
		if t == txt:
			t = gettext.gettext(txt)
		return t

	localeInit()
	language.addCallback(localeInit)
except Exception:
	def _(txt):
		return txt
