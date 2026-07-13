#!/usr/bin/python -u
# -*- coding: UTF-8 -*-

from . import _
from enigma import eDVBDB

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InfoBar import InfoBar
from Screens.ChoiceBox import ChoiceBox
from Screens.Standby import TryQuitMainloop

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Task import Task, Job

from Tools.Downloader import downloadWithProgress
from Tools.Directories import fileExists

import traceback
import os, tarfile, zipfile, shutil, glob
from twisted.web.client import getPage, downloadPage

def reloadChannelList():
	try:
		print("[ChannelListUpdate] reloading channel list")
		eDVBDB.getInstance().removeServices()
		eDVBDB.getInstance().reloadServicelist()
		eDVBDB.getInstance().reloadBouquets()
		if InfoBar.instance is not None:
			servicelist = InfoBar.instance.servicelist
			root = servicelist.getRoot()
			currentref = servicelist.getCurrentSelection()
			servicelist.setRoot(root)
			servicelist.setCurrentSelection(currentref)
	except:
		print("[ChannelListUpdate] error reloading channel list !")
		traceback.print_exc()

def is_path_safe(base, path):
	base = os.path.realpath(base)
	path = os.path.realpath(path)
	if base == '/':
		allowed_prefixes = ['/usr', '/etc', '/media', '/tmp', '/var', '/hdd']
		for prefix in allowed_prefixes:
			if path.startswith(prefix + os.sep) or path == prefix:
				return True
		return False
	return path.startswith(base + os.sep) or path == base

def safe_tar_extract(tar, path=".", **kwargs):
	for member in tar.getmembers():
		member_path = os.path.join(path, member.name)
		if not is_path_safe(path, member_path):
			raise Exception("Unsafe path in tarfile: %s" % member.name)
	tar.extractall(path, **kwargs)

def safe_zip_extract(zf, path="."):
	for member in zf.namelist():
		member_path = os.path.join(path, member)
		if not is_path_safe(path, member_path):
			raise Exception("Unsafe path in zipfile: %s" % member)
	zf.extractall(path)

class CommonChannelListScreen(Screen):
	skin = """
		<screen position="center,center" size="1150,340" >
			<widget name="typ" 		position="30,10" size="130,40" font="Regular;32" halign="left" />
			<widget name="typ0" 		position="300,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="typ1"		position="600,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="typ2"		position="900,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="sats0" 		position="30,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats1x" 		position="300,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats2x" 		position="600,90" size="290,25" font="Regular;18" halign="left" />
			<widget name="sats3x" 		position="900,90" size="240,25" font="Regular;18" halign="left" />
			<widget name="new0" 		position="30,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion1x" 	position="300,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion2x" 	position="600,150" size="290,25" font="Regular;18" halign="left" />
			<widget name="newVersion3x" 	position="900,150" size="240,25" font="Regular;18" halign="left" />
			<eLabel 			position="5,60" size="1140,2" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="270,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="560,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="860,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,200" size="1140,2" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="1145,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="key_red"		position="270,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="red" />
			<widget name="key_green"	position="570,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="green" />
			<widget name="status"		position="5,300" size="1140,40" font="Regular;24" halign="center" valign="center" backgroundColor="blue" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.session = session
		self.url1x = ''
		self.url2x = ''
		self.url3x = ''
		self.canDownload = 0
		self.url1 = ''
		self.url2 = ''
		self.url3 = None

		self["typ"] = Label("DiSEqC")
		self["typ0"] = Label("1x1")
		self["typ1"] = Label("2x1")
		self["typ2"] = Label("")

		self["sats0"] = Label(_("Satelity:"))
		self["new0"] = Label(_("Dostępna lista:"))

		self["sats1x"] = Label("Hotbird 13.0E")
		self["sats2x"] = Label("Hotbird 13.0E & Astra 19.2E")
		self["sats3x"] = Label("")

		self["status"] = Label()
		self["status"].hide()

		try:
			self.channelListVersion = open('/etc/enigma2/userbouquet.version').read().split('\n')[0]
		except:
			self.channelListVersion = _('nieznana')

		self["newVersion1x"] = Label(_("sprawdzam..."))
		self["newVersion2x"] = Label(_("sprawdzam..."))
		self["newVersion3x"] = Label("")

		self["key_red"] = Label(_("Pobierz"))
		self["key_green"] = Label(_("Pobierz"))

		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"red": self.red, "green": self.green, "cancel": self.close , "ok": self.close}, -1)

	def red(self):
		self["status"].show()
		try:
			if self.url1x != '' and self.canDownload == 1:
				self["status"].setText(_('Status: Pobieranie listy'))
				downloadPage(self.url1x.encode('utf-8'), '/tmp/chList1x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList1x1.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText(_('Status: Nie mogę się połączyć z serwerem !'))
			self.reloadUrlList(self.url1, self.url2, self.url3)

	def green(self):
		self["status"].show()
		try:
			if self.url2x != '' and self.canDownload == 1:
				self["status"].setText(_('Status: Pobieranie listy'))
				downloadPage(self.url2x.encode('utf-8'), '/tmp/chList2x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList2x1.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText(_('Status: Nie mogę się połączyć z serwerem !'))
			self.reloadUrlList(self.url1, self.url2, self.url3)

	def reloadUrlList(self, url1, url2, url3=None):
		self.url1 = url1
		self.url2 = url2
		self.url3 = url3

		getPage(self.url1.encode('utf-8')).addCallback(self.versionInfoCallBack, "1x").addErrback(self.errorUpdate)
		getPage(self.url2.encode('utf-8')).addCallback(self.versionInfoCallBack, "2x").addErrback(self.errorUpdate)
		if self.url3:
			getPage(self.url3.encode('utf-8')).addCallback(self.versionInfoCallBack, "3x").addErrback(self.errorUpdate)

	def versionInfoCallBack(self, html, ltype="1x"):
		try:
			content = html.decode('utf-8')
			new = dict([ l.split(':',1) for l in content.split("\n") if l.find(":") > 0])
			if 'version' in new:
				self["newVersion%s" % ltype].setText(new['version'])
				setattr(self, "url%s" % ltype, new['url'])
				self.canDownload = 1
		except Exception as error:
			 print(error)

	def downloadCallBack(self, html, plik = "/tmp/chList1x1.tgz"):
		try:
			for f in glob.glob('/etc/enigma2/*.tv'): os.remove(f)
			for f in glob.glob('/etc/enigma2/*.radio'): os.remove(f)
			files_to_remove = ['/etc/enigma2/lamedb', '/etc/enigma2/satellites.xml', '/etc/enigma2/whitelist', '/etc/enigma2/blacklist', '/etc/enigma2/revision']
			for f in files_to_remove:
				if os.path.exists(f): os.remove(f)

			self["status"].setText(_('Status: Rozpakowywanie'))
			with tarfile.open(name = plik, mode = "r:gz") as t:
				safe_tar_extract(t, "/")

			reloadChannelList()
			self["status"].setText(_('Status: Zainstalowano nową wersję listy kanałów'))
			if os.path.exists(plik): os.remove(plik)
		except:
			self["status"].setText(_('Status: Błąd archiwum !'))

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText(_('Status: Nie mogę się połączyć z serwerem !'))
		self["newVersion1x"].setText(_("Błąd"))
		self["newVersion2x"].setText(_("Błąd"))

class Djcrash(Screen):
	skin = """
		<screen position="center,center" size="1150,340" >
			<widget name="typ" 		position="30,10" size="130,40" font="Regular;32" halign="left" />
			<widget name="typ0" 		position="290,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="typ1"		position="490,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="typ2"		position="690,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="typ3"		position="890,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="sats0" 		position="30,70" size="200,25" font="Regular;18" halign="left" />
			<widget name="new0" 		position="30,170" size="200,25" font="Regular;18" halign="left" />
			<eLabel 			position="5,60" size="1140,2" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="sats1x" 		position="300,70" size="180,25" font="Regular;18" halign="left" />
			<widget name="newVersion1x" 	position="300,170" size="180,25" font="Regular;18" halign="left" />
			<eLabel 			position="270,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="sats2x" 		position="490,70" size="200,75" font="Regular;18" halign="left" />
			<widget name="newVersion2x" 	position="490,170" size="200,25" font="Regular;18" halign="left" />
			<eLabel 			position="470,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="670,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="sats4x" 		position="690,70" size="180,70" font="Regular;18" halign="left" />
			<widget name="newVersion4x" 	position="690,170" size="200,25" font="Regular;18" halign="left" />
			<eLabel 			position="870,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="sats20x" 		position="890,70" size="250,100" font="Regular;18" halign="left" />
			<widget name="newVersion20x" 	position="890,170" size="250,25" font="Regular;18" halign="left" />
			<eLabel 			position="1145,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,200" size="1140,2" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="key_red"		position="275,230" size="190,40" font="Regular;24" halign="center" valign="center" backgroundColor="red" />
			<widget name="key_green"	position="475,230" size="190,40" font="Regular;24" halign="center" valign="center" backgroundColor="green" />
			<widget name="key_yellow"	position="675,230" size="190,40" font="Regular;24" halign="center" valign="center" backgroundColor="yellow" />
			<widget name="key_blue"		position="875,230" size="260,40" font="Regular;24" halign="center" valign="center" backgroundColor="blue" />
			<widget name="status"		position="5,300" size="1140,40" font="Regular;24" halign="center" valign="center" backgroundColor="blue" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.session = session

		self.newVersion = _("brak")
		self.curVersion = _("nieznana")
		self.chooseList = "1x1"
		self.chID = "0"
		self.canDownload = 0

		Screen.setTitle(self, _("Listy kanałów DjCrash - zainstalowana wersja: " + self.getCurrentChListVersion()))

		self["typ"] = Label("DiSEqC")
		self["typ0"] = Label("1x1")
		self["typ1"] = Label("2x1")
		self["typ2"] = Label("4x1")
		self["typ3"] = Label("20x1")

		self["sats0"] = Label(_("Satelity:"))
		self["new0"] = Label(_("Dostępna lista:"))

		self["sats1x"] = Label("Hotbird 13.0E")
		self["sats2x"] = Label("Hotbird 13.0E, Astra19.2E")
		self["sats4x"] = Label("Thor 0.8W, Hotbird 13.0E, Astra 19.2E, Astra 23.5E")
		self["sats20x"] = Label("30.0W, 7.0W, 5.0W, 4.0W, 0.8W, 4.8E, 7.0E, 9.0E, 10.0E, 13.0E, 16.0E, 19.2E, 21,5E, 23,5E, 25.5E, 26.0E, 28.2E, 36,0E, 39.0E")

		self["status"] = Label()
		self["status"].hide()

		self["newVersion1x"] = Label(_("sprawdzam..."))
		self["newVersion2x"] = Label(_("sprawdzam..."))
		self["newVersion4x"] = Label(_("sprawdzam..."))
		self["newVersion20x"] = Label(_("sprawdzam..."))

		self["key_red"] = Label(_("Pobierz"))
		self["key_green"] = Label(_("Pobierz"))
		self["key_yellow"] = Label(_("Pobierz"))
		self["key_blue"] = Label(_("Pobierz"))

		self.reloadUrlList()

		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"red": self.red, "green": self.green, "yellow": self.yellow, "blue": self.blue, "cancel": self.close , "ok": self.close}, -1)

	def getCurrentChListVersion(self):
		try:
			if os.path.exists("/etc/enigma2/revision"):
				with open("/etc/enigma2/revision", 'r') as f:
					content = f.read()
					paths = content.split("\n")
					for path in paths:
						if '=' in path:
							self.curVersion = path.split("=")[1]
		except:
			return self.curVersion
		return self.curVersion

	def getNewChListVersion(self, html):
		try:
			if os.path.exists("/tmp/revision"):
				with open("/tmp/revision", 'r') as f:
					content = f.read()
					paths = content.split("\n")
					for path in paths:
						if '=' in path:
							key, val = path.split("=", 1)
							if key == "DATE":
								self.newVersion = val.replace('"', "").strip()
							if key == "VER":
								self.chID = val.replace('"', "").strip()

				self["newVersion1x"].setText(self.newVersion)
				self["newVersion2x"].setText(self.newVersion)
				self["newVersion4x"].setText(self.newVersion)
				self["newVersion20x"].setText(self.newVersion)

				self.canDownload = 1
		except:
			pass

	def red(self):
		self.chooseList = "1x1"
		self.commonButton()

	def green(self):
		self.chooseList = "2x1"
		self.commonButton()

	def yellow(self):
		self.chooseList = "4x1"
		self.commonButton()

	def blue(self):
		self.chooseList = "20x1"
		self.commonButton()

	def commonButton(self):
		self["status"].show()
		if self.canDownload == 1:
			self.downloadFromPKT()
		else:
			self.reloadUrlList()

	def reloadUrlList(self):
		downloadPage("http://addon.pkteam.pl/channel_lists_e2/revision".encode('utf-8'), '/tmp/revision').addCallback(self.getNewChListVersion).addErrback(self.errorUpdate)

	def downloadFromUpload(self):
		self["status"].setText(_("Status: Pobieranie listy ") + self.chooseList)
		downloadPage(("http://upload.sat-elita.net.pl/download.php?id=" + self.chID).encode('utf-8'), '/tmp/lista.zip').addCallback(self.installChList).addErrback(self.errorUpdate)

	def downloadFromPKT(self, html=None):
		self["status"].setText(_("Status: Pobieranie listy ") + self.chooseList)
		downloadPage(("http://addon.pkteam.pl/channel_lists_e2/enigma2_list_by_djcrash-" + self.newVersion + ".zip").encode('utf-8'), '/tmp/lista.zip').addCallback(self.installChList).addErrback(self.downloadFromUpload)

	def installChList(self, html):
		self["status"].setText(_('Status: Rozpakowywanie'))
		try:
			if os.path.exists("/tmp/chList/"): shutil.rmtree("/tmp/chList/")
			os.makedirs("/tmp/chList/")
			with zipfile.ZipFile("/tmp/lista.zip") as zf:
				safe_zip_extract(zf, "/tmp/chList/")
		except:
			self["status"].setText(_('Status: Błąd archiwum !'))
			return

		self["status"].setText(_('Status: Instalowanie'))

		for f in glob.glob('/etc/enigma2/*.tv'): os.remove(f)
		for f in glob.glob('/etc/enigma2/*.radio'): os.remove(f)
		files_to_remove = ['/etc/enigma2/lamedb', '/etc/enigma2/satellites.xml', '/etc/enigma2/whitelist', '/etc/enigma2/blacklist', '/etc/enigma2/revision']
		for f in files_to_remove:
			if os.path.exists(f): os.remove(f)

		src_dir = '/tmp/chList/list_by_djcrash-e2_' + self.chooseList + '/'
		if os.path.exists(src_dir):
			for item in os.listdir(src_dir):
				s = os.path.join(src_dir, item)
				d = os.path.join('/etc/enigma2/', item)
				if os.path.isdir(s):
					if os.path.exists(d): shutil.rmtree(d)
					shutil.copytree(s, d)
				else:
					shutil.copy2(s, d)

		if os.path.exists('/tmp/chList/revision'):
			shutil.copy2('/tmp/chList/revision', '/etc/enigma2/')

		reloadChannelList()
		if os.path.exists('/tmp/chList'): shutil.rmtree('/tmp/chList')
		if os.path.exists('/tmp/lista.zip'): os.remove('/tmp/lista.zip')
		self.setTitle(_("Listy kanałów DjCrash - zainstalowana wersja: " + self.getCurrentChListVersion()))
		self["status"].setText(_('Status: Zainstalowano nową wersję listy kanałów'))

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText(_('Status: Nie mogę się połączyć z serwerem !'))
		self["newVersion1x"].setText(_("Błąd"))
		self["newVersion2x"].setText(_("Błąd"))
		self["newVersion4x"].setText(_("Błąd"))
		self["newVersion20x"].setText(_("Błąd"))

class CommonPiconListScreen(Screen):
	skin = """
		<screen position="center,center" size="1150,340" >
			<widget name="typ" 		position="30,10" size="230,40" font="Regular;32" halign="left" />
			<widget name="typ0" 		position="300,10" size="500,40" font="Regular;32" halign="left" />
			<widget name="typ1"		position="600,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="typ2"		position="900,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="sats0" 		position="30,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats1x" 		position="300,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats2x" 		position="600,90" size="290,25" font="Regular;18" halign="left" />
			<widget name="sats3x" 		position="900,90" size="240,25" font="Regular;18" halign="left" />
			<widget name="new0" 		position="30,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion1x" 	position="300,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion2x" 	position="600,150" size="290,25" font="Regular;18" halign="left" />
			<widget name="newVersion3x" 	position="900,150" size="240,25" font="Regular;18" halign="left" />
			<eLabel 			position="5,60" size="1140,2" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="270,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="560,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="860,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,200" size="1140,2" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="1145,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="key_red"		position="270,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="red" />
			<widget name="key_green"	position="570,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="green" />
			<widget name="status"		position="5,300" size="1140,40" font="Regular;24" halign="center" valign="center" backgroundColor="blue" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.session = session

		self.newVersion1x = 'unknown'
		self.piconPositionToInstall = "130"
		self.piconTypeToInstall = "ZZPicon"
		self.piconLocationToInstall = "/"
		self.canDownload = 0

		self.baseUrl = ''
		self.url1 = ''
		self.url2 = ''
		self.url3 = ''

		self["typ"] = Label("MasterPolo")
		self["typ0"] = Label(_("Aktualne picony do Twojego tunera"))
		self["typ1"] = Label("")
		self["typ2"] = Label("")

		self["sats0"] = Label(_("Satelity:"))
		self["new0"] = Label(_("Ostatnia aktualizacja:"))

		self["sats1x"] = Label("Hotbird 13.0E")
		self["sats2x"] = Label("Astra 19.2E")
		self["sats3x"] = Label("DVB-T")

		self["status"] = Label()
		self["status"].hide()

		try:
			self.piconListVersion = open('/etc/enigma2/picon.version').read().split('\n')[0]
		except:
			self.piconListVersion = _('nieznana')

		self["newVersion1x"] = Label(_("sprawdzam..."))
		self["newVersion2x"] = Label(_("sprawdzam..."))
		self["newVersion3x"] = Label(_("sprawdzam..."))

		self["key_red"] = Label(_("Pobierz"))
		self["key_green"] = Label(_("Pobierz"))

		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"red": self.red, "green": self.green, "cancel": self.close , "ok": self.close}, -1)

	def choiceBoxPiconSize(self):
		menu = []
		menu.append((_("XPicon - 220x132"), "XPicons"))
		menu.append((_("XPicon BLACK - 220x132"), "XPiconsBLACK"))
		menu.append((_("SetoXPicon - 220x132"), "SetoXPicons"))
		menu.append((_("ZZPicon - 400x170"), "ZZPicon"))
		menu.append((_("ChristmasZZPicon - 400x170"), "ZZPiconChristmas"))
		menu.append((_("ZZPicon GLASS - 400x170"), "ZZPiconGLASS"))
		menu.append((_("ZZPicon BLACK - 400x170"), "ZZPiconBLACK"))
		menu.append((_("ZZPicon_RJ - 400x170"), "ZZPiconRJ"))
		menu.append((_("MasterPicon - 1920x150"), "MasterPicon"))
		self.session.openWithCallback(self.choicePiconSizeCB, ChoiceBox, title=_("Wybierz rozmiar picon"), list=menu)

	def choicePiconSizeCB(self, choice):
		if choice is None:
			return
		else:
			self.piconTypeToInstall = choice[1]
			self.choiceBoxPiconLocation()

	def choiceBoxPiconLocation(self):
		(mycf, myusb, myusb2, myusb3, mysd, myhdd, myhdd2) = ('', '', '', '', '', '', '')
		if fileExists('/proc/mounts'):
			with open('/proc/mounts', 'r') as f:
				for line in f.readlines():
					if '/media/cf' in line: mycf = '/media/cf/'
					elif '/media/usb' in line: myusb = '/media/usb/'
					elif '/media/usb2' in line: myusb2 = '/media/usb2/'
					elif '/media/usb3' in line: myusb3 = '/media/usb3/'
					elif '/media/card' in line: mysd = '/media/card/'
					elif '/hdd' in line: myhdd = '/media/hdd/'
					elif '/hdd2' in line: myhdd2 = '/media/hdd2/'

		menu = []
		if mycf: menu.append((_("Compact Flash (/media/cf/%s/picon)") % self.piconTypeToInstall, mycf + self.piconTypeToInstall))
		if myusb:
			menu.append((_("USB-1 (/media/usb/%s/picon)") % self.piconTypeToInstall, myusb + self.piconTypeToInstall))
			menu.append((_("USB-1 (/media/usb/picon)"), myusb))
		if myusb2:
			menu.append((_("USB-2 (/media/usb2/%s/picon)") % self.piconTypeToInstall, myusb2 + self.piconTypeToInstall))
			menu.append((_("USB-2 (/media/usb2/picon)"), myusb2))
		if myusb3:
			menu.append((_("USB-3 (/media/usb3/%s/picon)") % self.piconTypeToInstall, myusb3 + self.piconTypeToInstall))
			menu.append((_("USB-3 (/media/usb3/picon)"), myusb3))
		if mysd: menu.append((_("SD Card (/media/card/%s/picon)") % self.piconTypeToInstall, mysd + self.piconTypeToInstall))
		if myhdd:
			menu.append((_("HDD (/media/hdd/%s/picon)") % self.piconTypeToInstall, myhdd + self.piconTypeToInstall))
			menu.append((_("HDD (/media/hdd/picon)"), myhdd))
		if myhdd2:
			menu.append((_("HDD2 (/media/hdd2/%s/picon)") % self.piconTypeToInstall, myhdd2 + self.piconTypeToInstall))
			menu.append((_("HDD2 (/media/hdd2/picon)"), myhdd2))

		if self.piconTypeToInstall not in ("MasterPicon", "ZZPiconGLASS", "ZZPiconBLACK", "ZZPiconRJ", "ZZPiconChristmas"):
			menu.append((_("Flash (/%s/picon)") % self.piconTypeToInstall, "/" + self.piconTypeToInstall))
			menu.append((_("Flash (/usr/share/%s/picon)") % self.piconTypeToInstall, "/usr/share/enigma2/" + self.piconTypeToInstall))
			menu.append((_("Flash (/picon)"), "/"))
			menu.append((_("Flash (/usr/share/picon)"), "/usr/share/enigma2/"))

		self.session.openWithCallback(self.choiceBoxPiconLocationCB, ChoiceBox, title=_("Wybierz localizację picon"), list=menu)

	def choiceBoxPiconLocationCB(self, choice):
		if choice is None:
			return
		else:
			self.piconLocationToInstall = choice[1]
		self.prepareDownload()

	def prepareDownload(self):
		self.finalUrl = self.baseUrl + "/" + self.piconPositionToInstall + "/" + self.piconTypeToInstall + "/"+ self.piconTypeToInstall + self.piconPositionToInstall + ".tar.gz"
		self["status"].show()
		try:
			if self.finalUrl != '' and self.canDownload == 1:
				self["status"].setText(_('Status: Pobieranie piconów'))
				downloadPage(self.finalUrl.encode('utf-8'), '/tmp/picon.tgz').addCallback(self.downloadCallBack, "/tmp/picon.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText(_('Status: Nie mogę się połączyć z serwerem !'))
			self.reloadUrlList(self.baseUrl, self.url1, self.url2, self.url3)

	def red(self):
		self.piconPositionToInstall = "130"
		self.choiceBoxPiconSize()

	def green(self):
		self.piconPositionToInstall = "192"
		self.choiceBoxPiconSize()

	def reloadUrlList(self, baseUrl, url1, url2, url3=None):
		self.baseUrl = baseUrl
		self.url1 = url1
		self.url2 = url2
		self.url3 = url3

		getPage(self.url1.encode('utf-8')).addCallback(self.versionInfoCallBack, "1x").addErrback(self.errorUpdate)
		getPage(self.url2.encode('utf-8')).addCallback(self.versionInfoCallBack, "2x").addErrback(self.errorUpdate)
		if self.url3:
			getPage(self.url3.encode('utf-8')).addCallback(self.versionInfoCallBack, "3x").addErrback(self.errorUpdate)

	def versionInfoCallBack(self, html, ltype="1x"):
		try:
			content = html.decode('utf-8')
			new = dict([ l.split(':',1) for l in content.split("\n") if l.find(":") > 0])
			if 'version' in new:
				self["newVersion%s" % ltype].setText(new['version'])
				self.canDownload = 1
		except Exception as error:
			print(error)

	def downloadCallBack(self, html, plik = "/tmp/picon.tgz"):
		try:
			self["status"].setText(_('Status: Rozpakowywanie'))

			loc = self.piconLocationToInstall
			if self.piconTypeToInstall in ("ZZPiconGLASS", "ZZPiconBLACK", "ZZPiconRJ", "ZZPiconChristmas"):
				loc = loc.replace(self.piconTypeToInstall, "ZZPicon")
			elif self.piconTypeToInstall in ("XPiconsBLACK", "SetoXPicons"):
				loc = loc.replace(self.piconTypeToInstall, "XPicons")

			dest_picon = os.path.join(loc, "picon")
			if not os.path.exists(dest_picon):
				os.makedirs(dest_picon)

			self["status"].setText(_('Status: Instalowanie'))
			with tarfile.open(name = plik, mode = "r:gz") as t:
				safe_tar_extract(t, loc)

			self["status"].setText(_('Status: Zainstalowano nową wersję piconów'))
			if os.path.exists(plik): os.remove(plik)
			self.askRestart()
		except:
			self["status"].setText(_('Status: Błąd archiwum !'))

	def askRestart(self):
		message = _("Aby picony były wczytane należy zrestartować GUI.\nZrestartować teraz?")
		ybox = self.session.openWithCallback(self.restartBox, MessageBox, message, MessageBox.TYPE_YESNO)
		ybox.setTitle(_("Restart GUI"))

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText(_('Status: Nie mogę się połączyć z serwerem !'))
		self["newVersion1x"].setText(_("Błąd"))
		self["newVersion2x"].setText(_("Błąd"))

	def restartBox(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()
