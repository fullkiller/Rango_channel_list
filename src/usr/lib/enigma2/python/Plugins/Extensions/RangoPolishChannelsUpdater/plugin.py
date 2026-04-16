# -*- coding: utf-8 -*-
from enigma import getDesktop, RT_HALIGN_LEFT, RT_VALIGN_TOP, gFont

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.Progress import Progress
from Components.Sources.StaticText import StaticText
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend

from Screens.Standby import TryQuitMainloop
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists, SCOPE_PLUGINS
from Tools.Downloader import downloadWithProgress

from Plugins.Plugin import PluginDescriptor

from twisted.web.client import getPage, downloadPage
import os, hashlib, tarfile
from .utils import reloadChannelList, CommonChannelListScreen, Djcrash, CommonPiconListScreen, safe_tar_extract
from . import _

try:
	from Components.PluginList import resolveFilename
except:
	from Tools.Directories import resolveFilename

try:
	import configparser
except ImportError:
	import ConfigParser as configparser

version = "20240522"

class ChannelListUpdateMenu(Screen):
	skin = '''<screen name="ChannelListUpdateMenu" position="center,center" size="750,460" title="Polskie listy kanałów mod by fullkiller™" >
			<widget source="list" render="Listbox" position="10,10" size="730,240" scrollbarMode="showOnDemand" transparent="1">
				<convert type="TemplatedMultiContent">
				{"template": [
					MultiContentEntryText(pos = (115, 2), size = (620, 26), font=0, color=0x3589ff, flags = RT_HALIGN_LEFT, text = 0),
					MultiContentEntryPixmapAlphaBlend(pos = (2, 5), size = (100, 40), png = 1),
					MultiContentEntryText(pos = (115, 30), size = (620, 26), font=1, flags = RT_VALIGN_TOP | RT_HALIGN_LEFT, text = 3),
					],
					"fonts": [gFont("Regular", 24),gFont("Regular", 22)],
					"itemHeight": 60
				}
				</convert>
			</widget>
			<widget name="key_red"		position="270,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="red" />
			<widget name="info" position="5,280" size="740,180" font="Regular;28" halign="center" backgroundColor="#193e"/>
		  </screen>'''

	def __init__(self, session):
		Screen.__init__(self, session)
		self.list = []
		self["list"] = List(self.list)

		self["key_red"] = Label(_("Aktualizacja pluginu"))

		self.updateList()
		self.check_updates(0)

		self["info"] = Label(_("Plugin do aktualizacji list kanałów tworzonych przez HSWG, DjCrash'a, Krzyśka80, fullkiller™ i @Seto. Bez ich pracy nie byłoby list kanałów.\n\nRango - %s") % version)
		self["actions"] = ActionMap(["WizardActions", "ColorActions"], {"red": self.check_updates, "ok": self.KeyOk, "back": self.close})

	def KeyOk(self):
		self.sel = self["list"].getCurrent()
		returnValue = self.sel[2]
		if returnValue == "hswg":
				self.session.open(HSWG)
		elif returnValue == "djcrash":
				self.session.open(Djcrash)
		elif returnValue == "k80":
				self.session.open(K80)
		elif returnValue == "fk":
				self.session.open(Fk)
		elif returnValue == "master":
				self.session.open(Master)
		elif returnValue == "seto":
				self.session.open(Seto)
		elif returnValue == "masterpicon":
				self.session.open(MasterPicon)

	def updateList(self):
		self.list = []
		mypath = resolveFilename(SCOPE_PLUGINS)
		mypath = os.path.join(mypath, "Extensions/RangoPolishChannelsUpdater/images/")

		options = [
			("hswg.png", _("Pobierz listę od HSWG_(bzyk83)"), _("Listy dla HotBird 13.0E oraz Astra 19.2E"), "hswg"),
			("djcrash.png", _("Pobierz listę od DjCrasha"), _("Listy dla HotBird 13.0E, 19.2E, 23.5E, 28.2E oraz obrotnica"), "djcrash"),
			("k80.png", _("Pobierz listę od Krzysiek80"), _("Listy dla HotBird 13.0E"), "k80"),
			("fk.png", _("Pobierz listę od fullkiller™"), _("Listy dla HotBird 13.0E"), "fk"),
			("ms.png", _("Pobierz config mulistalker"), _("MAC links"), "master"),
			("seto.png", _("Pobierz listę od @Seto"), _("Listy dla HotBird 13.0E oraz Astra 19.2E"), "seto"),
			("picon.png", _("Pobierz Picony od @Seto i RJ"), _("Picony dla HotBird 13.0E oraz Astra 19.2E"), "masterpicon")
		]

		for icon, name, desc, idx in options:
			mypixmap = os.path.join(mypath, icon)
			if fileExists(mypixmap):
				png = LoadPixmap(mypixmap)
				self.list.append((name, png, idx, desc))

		self["list"].list = self.list

	def errorUpdate(self, html):
		message = _('Błąd sprawdzania nowej wersji Rango Polskie Listy Kanałów. Serwer nie odpowiada.')
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO, 3)

	def check_updates(self, tryb = 1):
		try:
			self.url = 'https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/version.txt'
			if tryb == 0:
				getPage(self.url.encode('utf-8')).addCallback(self.versionInfoCallBackQuiet).addErrback(self.errorUpdate)
			else:
				getPage(self.url.encode('utf-8')).addCallback(self.versionInfoCallBack).addErrback(self.errorUpdate)
		except Exception as error:
			print(error)

	def parseVersion(self, html):
		content = html.decode('utf-8')
		if '[plugin]' not in content:
			content = '[plugin]\n' + content

		import io
		config = configparser.ConfigParser()
		if hasattr(config, 'read_file'):
			config.read_file(io.StringIO(content))
		else:
			config.readfp(io.StringIO(content))

		self.newVersion = config.get('plugin', 'Version', fallback="0").replace('"', '').strip()
		self.newFile = config.get('plugin', 'File', fallback="").replace('"', '').strip()
		self.fileUrl = config.get('plugin', 'Url', fallback="").replace('"', '').strip()
		self.MD5 = config.get('plugin', 'MD5', fallback="00000000000000000000000000000000").replace('"', '').strip()
		self.updateurl = self.fileUrl + "/" + self.newFile

	def versionInfoCallBackQuiet(self, html):
		self.parseVersion(html)
		if int(self.newVersion) > int(version):
			message = '%s %s\n%s %s\n\n%s' % (_('Wersja na Serwerze:'), self.newVersion, _('Wersja zainstalowana:'), version, _('Aktualizacja jest dostępna!\n\nCzy chcesz uruchomić aktualizację teraz?'))
			self.session.openWithCallback(self.update, MessageBox, message, MessageBox.TYPE_YESNO)

	def versionInfoCallBack(self, html):
		self.parseVersion(html)
		if int(self.newVersion) == int(version):
			message = '%s %s\n%s %s\n\n%s' % (_('Wersja na Serwerze:'), self.newVersion, _('Wersja zainstalowana:'), version, _('Posiadasz aktualną wersję pluginu !'))
			self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
		elif int(self.newVersion) > int(version):
			message = '%s %s\n%s %s\n\n%s' % (_('Wersja na Serwerze:'), self.newVersion, _('Wersja zainstalowana:'), version, _('Aktualizacja jest dostępna!\n\nCzy chcesz uruchomić aktualizację teraz?'))
			self.session.openWithCallback(self.update, MessageBox, message, MessageBox.TYPE_YESNO)
		else:
			message = '%s %s\n%s %s\n\n%s' % (_('Wersja na Serwerze:'), self.newVersion, _('Wersja zainstalowana:'), version, _('Posiadasz nowszą wersję pluginu niż na serwerze!'))
			self.session.open(MessageBox, message, MessageBox.TYPE_INFO)

	def update(self, answer):
		if answer is True:
			self.session.open(ChannelListUpdateUpdater, self.updateurl, self.MD5)

class HSWG(CommonChannelListScreen):
	def __init__(self, session, args = None):
		CommonChannelListScreen.__init__(self, session)

		self.url1 = 'http://s4aupdater.one.pl/listy_kanalow/bzyk83/latest_HB'
		self.url2 = 'http://s4aupdater.one.pl/listy_kanalow/bzyk83/latest_dual'

		self.reloadUrlList(self.url1, self.url2)
		self.setTitle(_("Listy kanałów HSWG - zainstalowana wersja: " + self.channelListVersion))

class K80(CommonChannelListScreen):
	def __init__(self, session, args = None):
		CommonChannelListScreen.__init__(self, session)

		self.url1 = 'http://fullkiller.ugu.pl/RangoPolskieListyKanalow/listy/k80/latest5x.txt'
		self.url2 = 'https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/latest6x.txt'

		self.reloadUrlList(self.url1, self.url2)
		self.setTitle(_("Listy kanałów K80 - zainstalowana wersja: " + self.channelListVersion))

class Fk(CommonChannelListScreen):
	def __init__(self, session, args = None):
		CommonChannelListScreen.__init__(self, session)

		self.url1 = 'http://fullkiller.ugu.pl/RangoPolskieListyKanalow/listy/fk/latest1x.txt'
		self.url2 = 'https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/latest2x.txt'

		self.reloadUrlList(self.url1, self.url2)
		self.setTitle(_("Listy kanałów Fk - zainstalowana wersja: " + self.channelListVersion))

class Master(CommonChannelListScreen):
	def __init__(self, session, args = None):
		CommonChannelListScreen.__init__(self, session)

		self.url1 = 'https://fullkiller.000webhostapp.com/lista/Rango/stalker/stalker.txt'
		self.url2 = 'https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/stalker1.txt'

		self.reloadUrlList(self.url1, self.url2)
		self.setTitle(_("MAC address - zainstalowana wersja: " + self.channelListVersion))

class Seto(CommonChannelListScreen):
	def __init__(self, session, args = None):
		CommonChannelListScreen.__init__(self, session)

		self.url1 = 'http://s4aupdater.one.pl/listy_kanalow/seto/latest_HB'
		self.url2 = 'http://s4aupdater.one.pl/listy_kanalow/seto/latest_dual'

		self.reloadUrlList(self.url1, self.url2)
		self.setTitle(_("Listy kanałów SETO - zainstalowana wersja: " + self.channelListVersion))

class MasterPicon(CommonPiconListScreen):
	def __init__(self, session, args = None):
		CommonPiconListScreen.__init__(self, session)
		self.baseUrl = 'http://egami-feed.com/plugins/listy/picony/master'
		self.url1 = 'http://egami-feed.com/plugins/listy/picony/master/latest130.txt'
		self.url2 = 'http://egami-feed.com/plugins/listy/picony/master/latest190.txt'
		self.url3 = 'http://egami-feed.com/plugins/listy/picony/master/latestdtv.txt'

		self.reloadUrlList(self.baseUrl, self.url1, self.url2, self.url3)
		self.setTitle(_("Picony - zainstalowana wersja: " + self.piconListVersion))

class ChannelListUpdateUpdater(Screen):
	def __init__(self, session, updateurl, md5=None):
		self.session = session
		self.updateurl = updateurl
		self.md5 = md5
		skin = '''<screen name="ChannelListUpdateUpdater" position="center,center" size="840,360" backgroundColor="background">
			<widget name="status" position="20,10" size="800,70" transparent="1" font="Regular;16" foregroundColor="foreground" backgroundColor="background" valign="center" halign="left" noWrap="1" />
			<widget source="progress" render="Progress" position="100,153" size="400,6" transparent="1" borderWidth="0" />
			<widget source="progresstext" render="Label" position="333,184" zPosition="2" font="Regular;18" halign="center" transparent="1" size="180,20" foregroundColor="foreground" backgroundColor="background" />
		</screen>'''
		self.skin = skin
		Screen.__init__(self, session)
		self['status'] = Label()
		self['progress'] = Progress()
		self['progresstext'] = StaticText()
		self.startUpdate()
		self["actions"] = ActionMap(["WizardActions", "ColorActions"], {"ok": self.close, "back": self.close})


	def startUpdate(self):
		self['status'].setText(_('Pobieram nowy plugin Rango Channel List Updater'))
		self.dlfile = '/tmp/update_rango.tar.gz'
		self.download = downloadWithProgress(self.updateurl.encode('utf-8'), self.dlfile)
		self.download.addProgress(self.downloadProgress)
		self.download.start().addCallback(self.downloadFinished).addErrback(self.downloadFailed)

	def downloadFinished(self, string = ''):
		if self.md5 and self.md5 != "00000000000000000000000000000000":
			with open(self.dlfile, "rb") as f:
				file_hash = hashlib.md5(f.read()).hexdigest()
				if file_hash != self.md5:
					self['status'].setText(_('Błąd MD5 archiwum!'))
					return

		self['status'].setText(_('Instalowanie aktualizacji!'))
		try:
			with tarfile.open(self.dlfile, "r:gz") as t:
				safe_tar_extract(t, "/")
			if os.path.exists(self.dlfile): os.remove(self.dlfile)
			restartbox = self.session.openWithCallback(self.restartGUI, MessageBox, _('Nowy Rango Channel List Updater został zaktualizowany!!!\nCzy chcesz zrestartować GUI teraz?'), MessageBox.TYPE_YESNO)
			restartbox.setTitle(_('Restart GUI now?'))
		except:
			self['status'].setText(_('Błąd podczas instalacji aktualizacji!'))

	def downloadFailed(self, failure_instance = None, error_message = ''):
		text = _('Błąd pobierania plików!')
		if error_message == '' and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			text += ': ' + error_message
		self['status'].setText(text)
		return

	def downloadProgress(self, recvbytes, totalbytes):
		self['progress'].value = int(100 * recvbytes / float(totalbytes))
		self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (recvbytes / 1024, totalbytes / 1024, 100 * recvbytes / float(totalbytes))

	def restartGUI(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

def main(session, **kwargs):
	session.open(ChannelListUpdateMenu)

def menu(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Polskie listy kanałów"), main, "egami_channellist", 1)]
	return []


def Plugins(**kwargs):
	screenwidth = getDesktop(0).size().width()
	if screenwidth == 1920:
		return [
			PluginDescriptor(name = _("Polskie listy kanałów"), description=_('Najnowsza kolekcja polskich list kanałów'), where = PluginDescriptor.WHERE_MENU, fnc = menu),
			PluginDescriptor(name = _("Polskie listy kanałów"), description=_('Najnowsza kolekcja polskich list kanałów'), icon='pluginhd.png', where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
		]
	else:
		return [
			PluginDescriptor(name = _("Polskie listy kanałów"), description=_('Najnowsza kolekcja polskich list kanałów'), where = PluginDescriptor.WHERE_MENU, fnc = menu),
			PluginDescriptor(name = _("Polskie listy kanałów"), description=_('Najnowsza kolekcja polskich list kanałów'), icon='plugin.png', where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
		]
