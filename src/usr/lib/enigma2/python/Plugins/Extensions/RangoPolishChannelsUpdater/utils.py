#!/usr/bin/python -u
# -*- coding: UTF-8 -*-
#
# This code base on Areq source code from RitcherUpdater Plugin
#

from enigma import eDVBDB

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InfoBar import InfoBar

from Components.Label import Label
from Components.ActionMap import ActionMap

from Tools.Downloader import downloadWithProgress
from Tools.Directories import fileExists

import traceback
import os, tarfile, zipfile, shutil, glob
from twisted.web.client import getPage, downloadPage

from . import _

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
	except Exception:
		print("[ChannelListUpdate] error reloading channel list !")
		traceback.print_exc()

def is_path_safe(base, path):
	base = os.path.realpath(base)
	path = os.path.realpath(path)
	if base == '/':
		allowed_prefixes = ['/usr', '/etc', '/tmp', '/var', '/lib']
		return any(path.startswith(os.path.realpath(p)) for p in allowed_prefixes)
	return os.path.commonpath([base, path]) == base

def safe_tar_extract(src, dst, **kwargs):
	if not os.path.exists(dst):
		os.makedirs(dst)
	with tarfile.open(src, 'r:gz') as tar:
		for member in tar.getmembers():
			member_path = os.path.join(dst, member.name)
			if not is_path_safe(dst, member_path):
				print("[ChannelListUpdate] UNSAFE PATH in tar: %s" % member.name)
				continue
			tar.extract(member, dst, **kwargs)

def safe_zip_extract(src, dst):
	if not os.path.exists(dst):
		os.makedirs(dst)
	with zipfile.ZipFile(src, 'r') as zf:
		for member in zf.infolist():
			member_path = os.path.join(dst, member.filename)
			if not is_path_safe(dst, member_path):
				print("[ChannelListUpdate] UNSAFE PATH in zip: %s" % member.filename)
				continue
			zf.extract(member, dst)

class CommonChannelListScreen(Screen):
	skin = """
		<screen position="center,center" size="860,340" >
			<widget name="typ" 		position="30,10" size="130,40" font="Regular;32" halign="left" />
			<widget name="typ0" 		position="300,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="typ1"		position="600,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="sats0" 		position="30,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats1x" 		position="300,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats2x" 		position="600,90" size="290,25" font="Regular;18" halign="left" />
			<widget name="new0" 		position="30,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion1x" 	position="300,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion2x" 	position="600,150" size="290,25" font="Regular;18" halign="left" />
			<eLabel 			position="5,60" size="850,2" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="270,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="560,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,200" size="850,2" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="855,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="key_red"		position="270,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="red" />
			<widget name="key_green"	position="570,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="green" />
			<widget name="status"		position="5,300" size="865,40" font="Regular;24" halign="center" valign="center" backgroundColor="blue" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.session = session

		self.newVersion1x = 'unknown'

		self.canDownload = 0
		self.url1 = ''
		self.url2 = ''
		self.url1x = ''
		self.url2x = ''
		self.url3 = ''

		self["typ"] = Label("DiSEqC")
		self["typ0"] = Label("1x1")
		self["typ1"] = Label("2x1")

		self["sats0"] = Label(_("Satelity:"))
		self["new0"] = Label(_("Dostepna lista:"))

		self["sats1x"] = Label("Hotbird 13.0E")
		self["sats2x"] = Label("Hotbird 13.0E & Astra 19.2E")

		self["status"] = Label()
		self["status"].hide()

		try:
			with open('/etc/enigma2/userbouquet.version', 'r') as f:
				self.channelListVersion = f.read().split('\n')[0]
		except Exception:
			self.channelListVersion = _('nieznana')

		self["newVersion1x"] = Label(_("sprawdzam..."))
		self["newVersion2x"] = Label(_("sprawdzam..."))

		self["key_red"] = Label(_("Pobierz"))
		self["key_green"] = Label(_("Pobierz"))

		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"red": self.red, "green": self.green, "cancel": self.close , "ok": self.close}, -1)

	def red(self):
		self["status"].show()
		try:
			if self.url1x != '' and self.canDownload == 1:
				self["status"].setText(_('Status: Pobieranie listy'))
				downloadPage(self.url1x.encode('utf-8'), '/tmp/chList1x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList1x1.tgz").addErrback(self.errorUpdate)
		except Exception:
			self["status"].setText(_('Status: Nie mogę się połączyć z serwerem !'))
			self.reloadUrlList(self.url1, self.url2)

	def green(self):
		self["status"].show()
		try:
			if self.url2x != '' and self.canDownload == 1:
				self["status"].setText(_('Status: Pobieranie listy'))
				downloadPage(self.url2x.encode('utf-8'), '/tmp/chList2x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList2x1.tgz").addErrback(self.errorUpdate)
		except Exception:
			self["status"].setText(_('Status: Nie mogę się połączyć z serwerem !'))
			self.reloadUrlList(self.url1, self.url2)

	def reloadUrlList(self, url1, url2, url3=None):
		self.url1 = url1
		self.url2 = url2
		self.url3 = url3

		getPage(self.url1.encode('utf-8')).addCallback(self.versionInfoCallBack, "1x").addErrback(self.errorUpdate)
		getPage(self.url2.encode('utf-8')).addCallback(self.versionInfoCallBack, "2x").addErrback(self.errorUpdate)

	def versionInfoCallBack(self, html, ltype="1x"):
		try:
			if isinstance(html, bytes):
				content = html.decode('utf-8')
			else:
				content = html
			new = dict([ l.split(':',1) for l in content.split("\n") if l.find(":") > 0])
			if 'version' in new:
				self["newVersion%s" % ltype].setText(new['version'])
				if ltype == "1x":
					self.url1x = new['url'].strip()
					self.newVersion1 = new['version'].strip()
				else:
					self.url2x = new['url'].strip()
					self.newVersion2 = new['version'].strip()
					self.canDownload = 1
		except Exception as error:
			 print(error)

	def downloadCallBack(self, html, plik = "/tmp/chList1x1.tgz"):
		try:
			self["status"].setText(_('Status: Rozpakowywanie'))
			for f in glob.glob('/etc/enigma2/*.tv'): os.remove(f)
			for f in glob.glob('/etc/enigma2/*.radio'): os.remove(f)
			for f in ['/etc/enigma2/lamedb', '/etc/enigma2/satellites.xml', '/etc/enigma2/whitelist', '/etc/enigma2/blacklist', '/etc/enigma2/revision']:
				if os.path.exists(f): os.remove(f)

			safe_tar_extract(plik, "/", numeric_owner=True)
			reloadChannelList()
			self["status"].setText(_('Status: Zainstalowano nową wersję listy kanałów'))
			if os.path.exists(plik): os.remove(plik)
		except Exception:
			self["status"].setText(_('Status: Błąd archiwum !'))
			traceback.print_exc()

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
			<widget name="key_red"		position="255,230" size="190,40" font="Regular;24" halign="center" valign="center" backgroundColor="red" />
			<widget name="key_green"	position="455,230" size="190,40" font="Regular;24" halign="center" valign="center" backgroundColor="green" />
			<widget name="key_yellow"	position="655,230" size="190,40" font="Regular;24" halign="center" valign="center" backgroundColor="yellow" />
			<widget name="key_blue"		position="855,230" size="290,40" font="Regular;24" halign="center" valign="center" backgroundColor="blue" />
			<widget name="status"		position="5,300" size="1140,40" font="Regular;24" halign="center" valign="center" backgroundColor="#1a0000" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.session = session

		self.newVersion = _("brak")
		self.curVersion = _("nieznana")
		self.chooseList = "1x1"
		self.chID = "0"
		self.canDownload = 0

		self.setTitle(_("Listy kanałów DjCrash - zainstalowana wersja: " + self.getCurrentChListVersion()))

		self["typ"] = Label("DiSEqC")
		self["typ0"] = Label("1x1")
		self["typ1"] = Label("2x1")
		self["typ2"] = Label("4x1")
		self["typ3"] = Label("20x1")

		self["sats0"] = Label(_("Satelity:"))
		self["new0"] = Label(_("Dostepna lista:"))

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
			with open("/etc/enigma2/revision", 'r') as f:
				content = f.read()
				for line in content.splitlines():
					if "=" in line:
						self.curVersion = line.split("=")[1].strip()
		except Exception:
			pass
		return self.curVersion

	def getNewChListVersion(self, html):
		try:
			with open("/tmp/revision", 'r') as f:
				content = f.read()
				for line in content.splitlines():
					if "=" in line:
						key, val = line.split("=", 1)
						val = val.strip().replace('"', "")
						if key == "DATE":
							self.newVersion = val
						elif key == "VER":
							self.chID = val

			self["newVersion1x"].setText(self.newVersion)
			self["newVersion2x"].setText(self.newVersion)
			self["newVersion4x"].setText(self.newVersion)
			self["newVersion20x"].setText(self.newVersion)
			self.canDownload = 1
		except Exception:
			self.errorUpdate(None)

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

	def downloadFromUpload(self, failure=None):
		self["status"].setText(_("Status: Pobieranie listy ") + self.chooseList)
		downloadPage(("http://upload.sat-elita.net.pl/download.php?id=" + self.chID).encode('utf-8'), '/tmp/lista.zip').addCallback(self.installChList).addErrback(self.errorUpdate)

	def downloadFromPKT(self):
		self["status"].setText(_("Status: Alternatywne pobieranie listy ") + self.chooseList)
		downloadPage(("http://addon.pkteam.pl/channel_lists_e2/enigma2_list_by_djcrash-" + self.newVersion + ".zip").encode('utf-8'), '/tmp/lista.zip').addCallback(self.installChList).addErrback(self.downloadFromUpload)

	def installChList(self, html):
		self["status"].setText(_('Status: Rozpakowywanie'))
		try:
			safe_zip_extract(r"/tmp/lista.zip", r"/tmp/chList/")
		except Exception:
			self["status"].setText(_('Status: Błąd archiwum !'))
			return

		self["status"].setText(_('Status: Instalowanie'))

		for f in glob.glob('/etc/enigma2/*.tv'): os.remove(f)
		for f in glob.glob('/etc/enigma2/*.radio'): os.remove(f)
		for f in ['/etc/enigma2/lamedb', '/etc/enigma2/satellites.xml', '/etc/enigma2/whitelist', '/etc/enigma2/blacklist', '/etc/enigma2/revision']:
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

		rev_src = '/tmp/chList/revision'
		if os.path.exists(rev_src):
			shutil.copy2(rev_src, '/etc/enigma2/revision')

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


#Picon Window
class CommonPiconListScreen(Screen):
	skin = """
		<screen position="center,center" size="1150,340" >
			<widget name="typ" 		position="30,10" size="230,40" font="Regular;32" halign="left" />
			<widget name="typ0" 		position="300,10" size="500,40" font="Regular;32" halign="left" />
			<widget name="typ1"		position="600,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="sats0" 		position="30,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats1x" 		position="300,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats2x" 		position="600,90" size="290,25" font="Regular;18" halign="left" />
			<widget name="sats3" 		position="900,90" size="240,25" font="Regular;18" halign="left" />
			<widget name="new0" 		position="30,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion1x" 	position="300,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion2x" 	position="600,150" size="290,25" font="Regular;18" halign="left" />
			<widget name="newVersion3x" 	position="900,150" size="240,25" font="Regular;18" halign="left" />
			<eLabel 			position="5,60" size="1140,2" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="270,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="560,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="870,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,200" size="1140,2" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="1145,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="key_red"		position="270,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="red" />
			<widget name="key_green"	position="570,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="green" />
			<widget name="status"		position="5,300" size="1140,40" font="Regular;24" halign="center" valign="center" backgroundColor="#1a0000" />
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

		self["sats0"] = Label(_("Satelity:"))
		self["new0"] = Label(_("Ostatnia aktualizacja:"))

		self["sats1x"] = Label("Hotbird 13.0E")
		self["sats2x"] = Label("Astra 19.2E")
		self["sats3"] = Label("DVB-T/T2")

		self["status"] = Label()
		self["status"].hide()

		try:
			with open('/etc/enigma2/picon.version', 'r') as f:
				self.piconListVersion = f.read().split('\n')[0]
		except Exception:
			self.piconListVersion = _('nieznana')

		self["newVersion1x"] = Label(_("sprawdzam..."))
		self["newVersion2x"] = Label(_("sprawdzam..."))
		self["newVersion3x"] = Label(_("sprawdzam..."))

		self["key_red"] = Label(_("Pobierz"))
		self["key_green"] = Label(_("Pobierz"))

		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"red": self.red, "green": self.green, "cancel": self.close , "ok": self.close}, -1)

	def choiceBoxPiconSize(self):
		from Screens.ChoiceBox import ChoiceBox
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
		from Screens.ChoiceBox import ChoiceBox
		(mycf, myusb, myusb2, myusb3, mysd, myhdd, myhdd2) = ('', '', '', '', '', '', '')
		menu = []
		if os.path.exists('/proc/mounts'):
			with open('/proc/mounts', 'r') as f:
				for line in f.readlines():
					if '/media/cf' in line: mycf = '/media/cf/'
					elif '/media/usb' in line: myusb = '/media/usb/'
					elif '/media/usb2' in line: myusb2 = '/media/usb2/'
					elif '/media/usb3' in line: myusb3 = '/media/usb3/'
					elif '/media/card' in line: mysd = '/media/card/'
					elif '/media/hdd' in line: myhdd = '/media/hdd/'
					elif '/media/hdd2' in line: myhdd2 = '/media/hdd2/'
					elif ' /hdd ' in line: myhdd = '/hdd/'

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
			menu.append((_("Flash (/usr/share/enigma2/%s/picon)") % self.piconTypeToInstall, "/usr/share/enigma2/" + self.piconTypeToInstall))
			menu.append((_("Flash (/picon)"), "/"))
			menu.append((_("Flash (/usr/share/enigma2/picon)"), "/usr/share/enigma2/"))

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
		except Exception:
			self["status"].setText(_('Status: Nie mogę się połączyć z serwerem !'))
			self.reloadUrlList(self.baseUrl, self.url1, self.url2, self.url3)

	def red(self):
		self.piconPositionToInstall = "130"
		self.choiceBoxPiconSize()

	def green(self):
		self.piconPositionToInstall = "192"
		self.choiceBoxPiconSize()

	def reloadUrlList(self, baseUrl, url1, url2, url3):
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
			if isinstance(html, bytes):
				content = html.decode('utf-8')
			else:
				content = html
			new = dict([ l.split(':',1) for l in content.split("\n") if l.find(":") > 0])
			if 'version' in new:
				self["newVersion%s" % ltype].setText(new['version'])
				if ltype == "1x":
					self.newVersion1 = new['version']
				elif ltype == "2x":
					self.newVersion2 = new['version']
				elif ltype == "3x":
					self.newVersion3 = new['version']
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

			if not os.path.exists(os.path.join(loc, "picon")):
				os.makedirs(os.path.join(loc, "picon"))

			self["status"].setText(_('Status: Instalowanie'))
			safe_tar_extract(plik, loc)
			self["status"].setText(_('Status: Zainstalowano nową wersję piconów'))
			if os.path.exists(plik): os.remove(plik)
			self.askRestart()
		except Exception:
			self["status"].setText(_('Status: Błąd archiwum !'))
			traceback.print_exc()

	def askRestart(self):
		message = _("Aby picony były wczytane należy zrestartować GUI.\nZrestartować teraz?")
		self.session.openWithCallback(self.restartBox, MessageBox, message, MessageBox.TYPE_YESNO)

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText(_('Status: Nie mogę się połączyć z serwerem !'))
		self["newVersion1x"].setText(_("Błąd"))
		self["newVersion2x"].setText(_("Błąd"))
		if "newVersion3x" in self: self["newVersion3x"].setText(_("Błąd"))

	def restartBox(self, answer):
		if answer is True:
			from Screens.Standby import TryQuitMainloop
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()
