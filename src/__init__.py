# -*- coding: utf-8 -*-
import os
import gettext

PluginLanguageDomain = "RangoPolishChannelsUpdater"
PluginLanguagePath = "Extensions/RangoPolishChannelsUpdater/locale"

try:
    from Components.Language import language
    from Tools.Directories import resolveFilename, SCOPE_PLUGINS

    def localeInit():
        gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

    localeInit()
    language.addCallback(localeInit)
except Exception as e:
    print("[ChannelListUpdate] Localization initialization fallback: %s" % e)

def _(txt):
    t = gettext.dgettext(PluginLanguageDomain, txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t
