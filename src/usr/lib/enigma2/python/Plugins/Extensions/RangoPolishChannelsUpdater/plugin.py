# -*- coding: utf-8 -*-
from enigma import getDesktop, gFont, RT_HALIGN_LEFT, RT_VALIGN_TOP

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.PluginList import resolveFilename
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
try:
	import configparser
except ImportError:
	import ConfigParser as configparser
import io

from .utils import reloadChannelList, CommonChannelListScreen, Djcrash, CommonPiconListScreen, safe_tar_extract
import os

version = "20250522"

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

		self["key_red"] = Label("Aktualizacja pluginu")

		self.updateList()
		self.check_updates(0)

		self["info"] = Label("Plugin do aktualizacji list kanałow tworzonych przez HSWG, DjCrash'a, Krzyśka80 ,fullkiller™ i @Seto. Bez ich pracy nie było by list kanałów.\n\nRango - %s" % version)
		self["actions"] = ActionMap(["WizardActions", "ColorActions"], {"red": self.check_updates, "ok": self.KeyOk, "back": self.close})

	def KeyOk(self):
		self.sel = self["list"].getCurrent()
		if not self.sel:
			return
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

		mypixmap = (mypath + "hswg.png")
		png = LoadPixmap(mypixmap)
		name = (_("Pobierz listę od HSWG_(bzyk83)"))
		desc = (_("Listy dla HotBird 13.0E oraz Astra 19.2E"))
		idx = "hswg"
		res = (name,png,idx,desc)
		self.list.append(res)

		mypixmap = (mypath + "djcrash.png")
		png = LoadPixmap(mypixmap)
		name = (_("Pobierz listę od DjCrasha"))
		desc = (_("Listy dla HotBird 13.0E, 19.2E, 23,5E, 28,2E oraz obrotnica"))
		idx = "djcrash"
		res = (name,png,idx,desc)
		self.list.append(res)

		mypixmap = (mypath + "k80.png")
		png = LoadPixmap(mypixmap)
		name = (_("Pobierz listę od Krzysiek80"))
		desc = (_("Listy dla HotBird 13.0E"))
		idx = "k80"
		res = (name,png,idx,desc)
		self.list.append(res)

		mypixmap = (mypath + "fk.png")
		png = LoadPixmap(mypixmap)
		name = (_("Pobierz listę od fullkiller™"))
		desc = (_("Listy dla HotBird 13.0E"))
		idx = "fk"
		res = (name,png,idx,desc)
		self.list.append(res)

		mypixmap = (mypath + "ms.png")
		png = LoadPixmap(mypixmap)
		name = (_("Pobierz config mulistalker"))
		desc = (_("MAC links"))
		idx = "master"
		res = (name,png,idx,desc)
		self.list.append(res)

		mypixmap = (mypath + "seto.png")
		png = LoadPixmap(mypixmap)
		name = (_("Pobierz listę od @Seto"))
		desc = (_("Listy dla HotBird 13.0E oraz Astra 19.2E"))
		idx = "seto"
		res = (name,png,idx,desc)
		self.list.append(res)

		mypixmap = (mypath + "picon.png")
		png = LoadPixmap(mypixmap)
		name = (_("Pobierz Picony od @Seto i RJ"))
		desc = (_("Picony dla HotBird 13.0E oraz Astra 19.2E"))
		idx = "masterpicon"
		res = (name,png,idx,desc)
		self.list.append(res)

		self["list"].list = self.list

	def errorUpdate(self, html):
		message = _('Błąd sprawdzania nowej wersji Rango Polskie Listy Kanałów. Serwer nie odpowiada.')
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO, 3)

	def check_updates(self, tryb = 1):
		try:
			self.url = 'https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/version.txt'
			if tryb == 0:
				getPage(self.url.encode('utf-8')).addCallback(self.versionInfoCallBack, True).addErrback(self.errorUpdate)
			else:
				getPage(self.url.encode('utf-8')).addCallback(self.versionInfoCallBack, False).addErrback(self.errorUpdate)
		except Exception as error:
			print(error)

	def versionInfoCallBack(self, html, quiet=False):
		content = html.decode('utf-8')
		config = configparser.ConfigParser()
		try:
			config.read_file(io.StringIO(u'[plugin]\n' + content))
			self.newVersion = config.get('plugin', 'Version')
			self.newFile = config.get('plugin', 'File')
			self.fileUrl = config.get('plugin', 'Url')
			self.MD5 = config.get('plugin', 'MD5')
		except:
			# Fallback to manual parsing if configparser fails
			paths = content.split("\n")
			for path in paths:
				if "Version =" in path: self.newVersion = path.split("=")[1].strip()
				if "File =" in path: self.newFile = path.split("=")[1].strip()
				if "Url =" in path: self.fileUrl = path.split("=")[1].strip()
				if "MD5 =" in path: self.MD5 = path.split("=")[1].strip()

		print("Current Version : ", int(version), " Server Version : ", self.newVersion)
		self.updateurl = self.fileUrl.rstrip('/') + "/" + self.newFile

		if int(self.newVersion) > int(version):
			message = '%s %s\n%s %s\n\n%s' % (_('Wersja na Serwerze:'),
			self.newVersion,
			_('Wersja zainstalowana:'),
			version,
			_('Aktualizacja jest dostępna!\n\nCzy chcesz uruchomic akutalizację teraz?'))
			self.session.openWithCallback(self.update, MessageBox, message, MessageBox.TYPE_YESNO)
		elif not quiet:
			if int(self.newVersion) == int(version):
				message = '%s %s\n%s %s\n\n%s' % (_('Wersja na Serwerze:'),
				self.newVersion,
				_('Wersja zainstalowana:'),
				version,
				_('Posiadasz aktualna wersje pluginu !'))
				self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
			else:
				message = '%s %s\n%s %s\n\n%s' % (_('Wersja na Serwerze:'),
				self.newVersion,
				_('Wersja zainstalowana:'),
				version,
				_('Posiadasz nowszą wersję pluginu niż na serwerze!'))
				self.session.open(MessageBox, message, MessageBox.TYPE_INFO)

	def update(self, answer):
		if answer is True:
			self.session.open(ChannelListUpdateUpdater, self.updateurl)

class HSWG(CommonChannelListScreen):
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		CommonChannelListScreen.__init__(self, session)

		self.url1 = 'http://s4aupdater.one.pl/listy_kanalow/bzyk83/latest_HB'
		self.url2 = 'http://s4aupdater.one.pl/listy_kanalow/bzyk83/latest_dual'

		self.reloadUrlList(self.url1, self.url2)

		Screen.setTitle(self, _("Listy kanałów HSWG - zainstalowana wersja: " + self.channelListVersion))

class K80(CommonChannelListScreen):
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		CommonChannelListScreen.__init__(self, session)

		self.url1 = 'http://fullkiller.ugu.pl/RangoPolskieListyKanalow/listy/k80/latest5x.txt'
		self.url2 = 'https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/latest6x.txt'

		self.reloadUrlList(self.url1, self.url2)

		Screen.setTitle(self, _("Listy kanałów K80 - zainstalowana wersja: " + self.channelListVersion))

class Fk(CommonChannelListScreen):
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		CommonChannelListScreen.__init__(self, session)

		self.url1 = 'http://fullkiller.ugu.pl/RangoPolskieListyKanalow/listy/fk/latest1x.txt'
		self.url2 = 'https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/latest2x.txt'

		self.reloadUrlList(self.url1, self.url2)

		Screen.setTitle(self, _("Listy kanałów Fk - zainstalowana wersja: " + self.channelListVersion))

class Master(CommonChannelListScreen):
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		CommonChannelListScreen.__init__(self, session)

		self.url1 = 'https://fullkiller.000webhostapp.com/lista/Rango/stalker/stalker.txt'
		self.url2 = 'https://raw.githubusercontent.com/fullkiller/Rango_channel_list/main/stalker1.txt'

		self.reloadUrlList(self.url1, self.url2)

		Screen.setTitle(self, _("MAC adrress - zainstalowana wersja: " + self.channelListVersion))

class Seto(CommonChannelListScreen):
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		CommonChannelListScreen.__init__(self, session)

		self.url1 = 'http://s4aupdater.one.pl/listy_kanalow/seto/latest_HB'
		self.url2 = 'http://s4aupdater.one.pl/listy_kanalow/seto/latest_dual'

		self.reloadUrlList(self.url1, self.url2)

		Screen.setTitle(self, _("Listy kanałów SETO - zainstalowana wersja: " + self.channelListVersion))

class MasterPicon(CommonPiconListScreen):
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		CommonPiconListScreen.__init__(self, session)
		self.baseUrl = 'http://egami-feed.com/plugins/listy/picony/master'
		self.url1 = 'http://egami-feed.com/plugins/listy/picony/master/latest130.txt'
		self.url2 = 'http://egami-feed.com/plugins/listy/picony/master/latest190.txt'
		self.url3 = 'http://egami-feed.com/plugins/listy/picony/master/latestdtv.txt'

		self.reloadUrlList(self.baseUrl, self.url1, self.url2, self.url3)

		Screen.setTitle(self, _("Picony - zainstalowana wersja: " + self.piconListVersion))

class ChannelListUpdateUpdater(Screen):
	skin = '''<screen name="ChannelListUpdateUpdater" position="center,center" size="840,360" backgroundColor="background">
			<widget name="status" position="20,10" size="800,70" transparent="1" font="Regular;16" foregroundColor="foreground" backgroundColor="background" valign="center" halign="left" noWrap="1" />
			<widget source="progress" render="Progress" position="100,153" size="400,6" transparent="1" borderWidth="0" />
			<widget source="progresstext" render="Label" position="333,184" zPosition="2" font="Regular;18" halign="center" transparent="1" size="180,20" foregroundColor="foreground" backgroundColor="background" />
		</screen>'''

	def __init__(self, session, updateurl):
		Screen.__init__(self, session)
		self.session = session
		self.updateurl = updateurl
		self['status'] = Label()
		self['progress'] = Progress()
		self['progresstext'] = StaticText()
		self.startUpdate()
		self["actions"] = ActionMap(["WizardActions", "ColorActions"], {"ok": self.close, "back": self.close})

	def startUpdate(self):
		self['status'].setText(_('Pobieram nowy plugin Rango Channel List Updater'))
		self.dlfile = '/tmp/update_rango.tar.gz'
		self.download = downloadWithProgress(self.updateurl.encode('utf-8'), self.dlfile.encode('utf-8'))
		self.download.addProgress(self.downloadProgress)
		self.download.start().addCallback(self.downloadFinished).addErrback(self.downloadFailed)

	def downloadFinished(self, string = ''):
		self['status'].setText(_('Instalowanie aktualizacji!'))
		if safe_tar_extract(self.dlfile, "/"):
			os.remove(self.dlfile)
			if hasattr(os, 'sync'):
				os.sync()
			else:
				os.system('sync')
			restartbox = self.session.openWithCallback(self.restartGUI, MessageBox, _('Nowy Rango Channel List Updater zostal zaktualizowany!!!\nCzy chcesz zrestartowac GUI teraz?'), MessageBox.TYPE_YESNO)
			restartbox.setTitle(_('Restart GUI now?'))
		else:
			self['status'].setText(_('Błąd instalacji aktualizacji!'))

	def downloadFailed(self, failure_instance = None, error_message = ''):
		text = _('Błąd pobierania plikow!')
		if error_message == '' and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			text += ': ' + error_message
		self['status'].setText(text)

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
			PluginDescriptor(name = "Polskie listy kanałów", description=_('Najnowsza kolekcja polskich list kanałów'), where = PluginDescriptor.WHERE_MENU, fnc = menu),
			PluginDescriptor(name = "Polskie listy kanałów", description=_('Najnowsza kolekcja polskich list kanałów'), icon='pluginhd.png', where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
		]
	else:
		return [
			PluginDescriptor(name = "Polskie listy kanałów", description=_('Najnowsza kolekcja polskich list kanałów'), where = PluginDescriptor.WHERE_MENU, fnc = menu),
			PluginDescriptor(name = "Polskie listy kanałów", description=_('Najnowsza kolekcja polskich list kanałów'), icon='plugin.png', where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
		]
