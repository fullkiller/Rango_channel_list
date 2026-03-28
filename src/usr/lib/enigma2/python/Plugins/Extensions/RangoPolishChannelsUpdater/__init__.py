import gettext
from os import environ

def _(txt):
    t = gettext.dgettext("RangoPolishChannelsUpdater", txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t
