#!/usr/bin/python -u
# -*- coding: UTF-8 -*-
#
# This code base on Areq source code from RitcherUpdater Plugin
#

from enigma import eDVBDB

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InfoBar import InfoBar
from Screens.TaskView import JobView
from Screens.ChoiceBox import ChoiceBox
from Screens.Standby import TryQuitMainloop

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Task import Task, Job, job_manager, Condition

from Tools.Downloader import downloadWithProgress
from Tools.Directories import fileExists

import traceback
import re, os, tarfile, zipfile, shutil, glob
from twisted.web.client import getPage, downloadPage

def is_path_safe(base, target):
	base = os.path.realpath(base)
	target = os.path.realpath(target)
	return os.path.commonpath([base]) == os.path.commonpath([base, target])

def safe_tar_extract(tar, path=".", **kwargs):
	for member in tar.getmembers():
		member_path = os.path.join(path, member.name)
		if not is_path_safe(path, member_path):
			raise Exception("Unsafe path in tar: %s" % member.name)
	tar.extractall(path, **kwargs)

def safe_zip_extract(zip_file, path="."):
	for member in zip_file.namelist():
		member_path = os.path.join(path, member)
		if not is_path_safe(path, member_path):
			raise Exception("Unsafe path in zip: %s" % member)
	zip_file.extractall(path)

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

		self["typ"] = Label("DiSEqC")
		self["typ0"] = Label("1x1")
		self["typ1"] = Label("2x1")

		self["sats0"] = Label("Satelity:")
		self["new0"] = Label("Dostepna lista:")

		self["sats1x"] = Label("Hotbird 13.0E")
		self["sats2x"] = Label("Hotbird 13.0E & Astra 19.2E")

		self["status"] = Label()
		self["status"].hide()

		try:
			self.channelListVersion = open('/etc/enigma2/userbouquet.version').read().split('\n')[0]
		except:
			self.channelListVersion = 'nieznana'

		self["newVersion1x"] = Label("sprawdzam...")
		self["newVersion2x"] = Label("sprawdzam...")

		self["key_red"] = Label("Pobierz")
		self["key_green"] = Label("Pobierz")

		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"red": self.red, "green": self.green, "cancel": self.close , "ok": self.close}, -1)

	def red(self):
		self["status"].show()
		try:
			if self.url1x != '' and self.canDownload == 1:
				self["status"].setText('Status: Pobieranie listy')
				downloadPage(self.url1x.encode('utf-8'), '/tmp/chList1x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList1x1.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
			self.reloadUrlList(self.url1, self.url2)

	def green(self):
		self["status"].show()
		try:
			if self.url2x != '' and self.canDownload == 1:
				self["status"].setText('Status: Pobieranie listy')
				downloadPage(self.url2x.encode('utf-8'), '/tmp/chList2x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList2x1.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
			self.reloadUrlList(self.url1, self.url2)

	def reloadUrlList(self, url1, url2):
		self.url1 = url1
		self.url2 = url2

		getPage(self.url1.encode('utf-8')).addCallback(self.versionInfoCallBack, "1x").addErrback(self.errorUpdate)
		getPage(self.url2.encode('utf-8')).addCallback(self.versionInfoCallBack, "2x").addErrback(self.errorUpdate)

	def versionInfoCallBack(self, html, ltype="1x"):
		try:
			html_str = html.decode('utf-8')
			new = dict([ l.split(':',1) for l in html_str.split("\n") if l.find(":") > 0])
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
			for f in glob.glob('/etc/enigma2/*.tv'): os.remove(f)
			for f in glob.glob('/etc/enigma2/*.radio'): os.remove(f)
			for f in ('lamedb', 'satellites.xml', 'whitelist', 'blacklist', 'revision'):
				p = os.path.join('/etc/enigma2', f)
				if os.path.exists(p): os.remove(p)

			self["status"].setText('Status: Rozpakowywanie')
			with tarfile.open(name = plik, mode = "r:gz") as t:
				safe_tar_extract(t, "/")
			reloadChannelList()
			self["status"].setText('Status: Zainstalowano nową wersję listy kanałów')
			if os.path.exists(plik): os.remove(plik)
		except:
			self["status"].setText('Status: Błąd archiwum !')
			traceback.print_exc()

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
		self["newVersion1x"].setText("Błąd")
		self["newVersion2x"].setText("Błąd")

class Djcrash(Screen):
	skin = """
		<screen position="center,center" size="1200,340" >
			<widget name="typ" 		position="30,10" size="130,40" font="Regular;32" halign="left" />
			<widget name="typ0" 		position="290,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="typ1"		position="490,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="typ2"		position="690,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="typ3"		position="890,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="sats0" 		position="30,70" size="200,25" font="Regular;18" halign="left" />
			<widget name="new0" 		position="30,170" size="200,25" font="Regular;18" halign="left" />
			<eLabel 			position="5,60" size="1190,2" font="Regular;18" halign="center" backgroundColor="white" />
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
			<widget name="sats20x" 		position="890,70" size="290,100" font="Regular;18" halign="left" />
			<widget name="newVersion20x" 	position="890,170" size="290,25" font="Regular;18" halign="left" />
			<eLabel 			position="1195,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,200" size="1190,2" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="key_red"		position="275,230" size="190,40" font="Regular;24" halign="center" valign="center" backgroundColor="red" />
			<widget name="key_green"	position="475,230" size="190,40" font="Regular;24" halign="center" valign="center" backgroundColor="green" />
			<widget name="key_yellow"	position="675,230" size="190,40" font="Regular;24" halign="center" valign="center" backgroundColor="yellow" />
			<widget name="key_blue"		position="875,230" size="320,40" font="Regular;24" halign="center" valign="center" backgroundColor="blue" />
			<widget name="status"		position="5,300" size="1190,40" font="Regular;24" halign="center" valign="center" backgroundColor="blue" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.session = session

		self.newVersion = "brak"
		self.curVersion = "nieznana"
		self.chooseList = "1x1"
		self.chID = "0"
		self.canDownload = 0

		Screen.setTitle(self, _("Listy kanałów DjCrash - zainstalowana wersja: " + self.getCurrentChListVersion()))

		self["typ"] = Label("DiSEqC")
		self["typ0"] = Label("1x1")
		self["typ1"] = Label("2x1")
		self["typ2"] = Label("4x1")
		self["typ3"] = Label("20x1")

		self["sats0"] = Label("Satelity:")
		self["new0"] = Label("Dostepna lista:")

		self["sats1x"] = Label("Hotbird 13.0E")
		self["sats2x"] = Label("Hotbird 13.0E, Astra19.2E")
		self["sats4x"] = Label("Thor 0.8W, Hotbird 13.0E, Astra 19.2E, Astra 23.5E")
		self["sats20x"] = Label("30.0W, 7.0W, 5.0W, 4.0W, 0.8W, 4.8E, 7.0E, 9.0E, 10.0E, 13.0E, 16.0E, 19.2E, 21,5E, 23,5E, 25.5E, 26.0E, 28.2E, 36,0E, 39.0E")

		self["status"] = Label()
		self["status"].hide()

		self["newVersion1x"] = Label("sprawdzam...")
		self["newVersion2x"] = Label("sprawdzam...")
		self["newVersion4x"] = Label("sprawdzam...")
		self["newVersion20x"] = Label("sprawdzam...")

		self["key_red"] = Label("Pobierz")
		self["key_green"] = Label("Pobierz")
		self["key_yellow"] = Label("Pobierz")
		self["key_blue"] = Label("Pobierz")

		self.reloadUrlList()

		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"red": self.red, "green": self.green, "yellow": self.yellow, "blue": self.blue, "cancel": self.close , "ok": self.close}, -1)

	def getCurrentChListVersion(self):
		try:
			if os.path.exists("/etc/enigma2/revision"):
				with open("/etc/enigma2/revision", 'r') as f:
					content = f.read()
					paths = content.split("\n")
					for path in paths:
						if "=" in path:
							self.curVersion = path.split("=")[1]
		except:
			pass
		return self.curVersion

	def getNewChListVersion(self, html):
		try:
			if os.path.exists("/tmp/revision"):
				with open("/tmp/revision", 'r') as f:
					content = f.read()
					paths = content.split("\n")
					for path in paths:
						if "=" in path:
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
		except Exception as error:
			print(error)

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
		self["status"].setText("Status: Pobieranie listy " + self.chooseList)
		downloadPage(("http://upload.sat-elita.net.pl/download.php?id=" + self.chID).encode('utf-8'), '/tmp/lista.zip').addCallback(self.installChList).addErrback(self.errorUpdate)

	def downloadFromPKT(self):
		self["status"].setText("Status: Alternatywne pobieranie listy " + self.chooseList)
		downloadPage(("http://addon.pkteam.pl/channel_lists_e2/enigma2_list_by_djcrash-" + self.newVersion + ".zip").encode('utf-8'), '/tmp/lista.zip').addCallback(self.installChList).addErrback(self.downloadFromUpload)

	def installChList(self, html):
		self["status"].setText('Status: Rozpakowywanie')
		try:
			if os.path.exists("/tmp/chList/"): shutil.rmtree("/tmp/chList/")
			os.makedirs("/tmp/chList/")
			with zipfile.ZipFile("/tmp/lista.zip", "r") as zf:
				safe_zip_extract(zf, "/tmp/chList/")
		except:
			self["status"].setText('Status: Błąd archiwum !')
			return

		self["status"].setText('Status: Instalowanie')

		for f in glob.glob('/etc/enigma2/*.tv'): os.remove(f)
		for f in glob.glob('/etc/enigma2/*.radio'): os.remove(f)
		for f in ('lamedb', 'satellites.xml', 'whitelist', 'blacklist', 'revision'):
			p = os.path.join('/etc/enigma2', f)
			if os.path.exists(p): os.remove(p)

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

		rev_file = '/tmp/chList/revision'
		if os.path.exists(rev_file):
			shutil.copy2(rev_file, '/etc/enigma2/revision')

		reloadChannelList()
		if os.path.exists('/tmp/chList'): shutil.rmtree('/tmp/chList')
		self.setTitle(_("Listy kanałów DjCrash - zainstalowana wersja: " + self.getCurrentChListVersion()))
		self["status"].setText('Status: Zainstalowano nową wersję listy kanałów')

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
		self["newVersion1x"].setText("Błąd")
		self["newVersion2x"].setText("Błąd")
		self["newVersion4x"].setText("Błąd")
		self["newVersion20x"].setText("Błąd")


class CommonPiconListScreen(Screen):
	skin = """
		<screen position="center,center" size="1150,340" >
			<widget name="typ" 		position="30,10" size="230,40" font="Regular;32" halign="left" />
			<widget name="typ0" 		position="300,10" size="500,40" font="Regular;32" halign="left" />
			<widget name="typ1"		position="800,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="sats0" 		position="30,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats1x" 		position="300,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats2x" 		position="600,90" size="290,25" font="Regular;18" halign="left" />
			<widget name="new0" 		position="30,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion1x" 	position="300,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion2x" 	position="600,150" size="290,25" font="Regular;18" halign="left" />
			<eLabel 			position="5,60" size="1140,2" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="270,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="560,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="5,200" size="1140,2" font="Regular;18" halign="center" backgroundColor="white" />
			<eLabel 			position="1145,63" size="2,135" font="Regular;18" halign="center" backgroundColor="white" />
			<widget name="key_red"		position="270,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="red" />
			<widget name="key_green"	position="570,230" size="280,40" font="Regular;24" halign="center" valign="center" backgroundColor="green" />
			<widget name="status"		position="5,300" size="1145,40" font="Regular;24" halign="center" valign="center" backgroundColor="blue" />
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
		self["typ0"] = Label("Aktualne picony do Twojego tunera")
		self["typ1"] = Label("")

		self["sats0"] = Label("Satelity:")
		self["new0"] = Label("Ostatnia aktualizacja:")

		self["sats1x"] = Label("Hotbird 13.0E")
		self["sats2x"] = Label("Astra 19.2E")

		self["status"] = Label()
		self["status"].hide()

		try:
			self.piconListVersion = open('/etc/enigma2/picon.version').read().split('\n')[0]
		except:
			self.piconListVersion = 'nieznana'

		self["newVersion1x"] = Label("sprawdzam...")
		self["newVersion2x"] = Label("sprawdzam...")

		self["key_red"] = Label("Pobierz")
		self["key_green"] = Label("Pobierz")

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
		mycf, myusb, myusb2, myusb3, mysd, myhdd, myhdd2 = ('', '', '', '', '', '', '')
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

		if mycf: menu.append((_("Compact Flash (/media/cf/%s/picon)" % self.piconTypeToInstall), os.path.join(mycf, self.piconTypeToInstall)))
		if myusb:
			menu.append((_("USB-1 (/media/usb/%s/picon)" % self.piconTypeToInstall), os.path.join(myusb, self.piconTypeToInstall)))
			menu.append((_("USB-1 (/media/usb/picon)"), myusb))
		if myusb2:
			menu.append((_("USB-2 (/media/usb2/%s/picon)" % self.piconTypeToInstall), os.path.join(myusb2, self.piconTypeToInstall)))
			menu.append((_("USB-2 (/media/usb2/picon)"), myusb2))
		if myusb3:
			menu.append((_("USB-3 (/media/usb3/%s/picon)" % self.piconTypeToInstall), os.path.join(myusb3, self.piconTypeToInstall)))
			menu.append((_("USB-3 (/media/usb3/picon)"), myusb3))
		if mysd: menu.append((_("SD Card (/media/card/%s/picon)" % self.piconTypeToInstall), os.path.join(mysd, self.piconTypeToInstall)))
		if myhdd:
			menu.append((_("HDD (/media/hdd/%s/picon)" % self.piconTypeToInstall), os.path.join(myhdd, self.piconTypeToInstall)))
			menu.append((_("HDD (/media/hdd/picon)"), myhdd))
		if myhdd2:
			menu.append((_("HDD2 (/media/hdd2/%s/picon)" % self.piconTypeToInstall), os.path.join(myhdd2, self.piconTypeToInstall)))
			menu.append((_("HDD2 (/media/hdd2/picon)"), myhdd2))

		if self.piconTypeToInstall not in ("MasterPicon", "ZZPiconGLASS", "ZZPiconBLACK", "ZZPiconRJ", "ZZPiconChristmas"):
			menu.append((_("Flash (/%s/picon)" % self.piconTypeToInstall), "/" + self.piconTypeToInstall))
			menu.append((_("Flash (/usr/share/enigma2/%s/picon)" % self.piconTypeToInstall), "/usr/share/enigma2/" + self.piconTypeToInstall))
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
				self["status"].setText('Status: Pobieranie piconów')
				downloadPage(self.finalUrl.encode('utf-8'), '/tmp/picon.tgz').addCallback(self.downloadCallBack, "/tmp/picon.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
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

	def versionInfoCallBack(self, html, ltype="1x"):
		try:
			html_str = html.decode('utf-8')
			new = dict([ l.split(':',1) for l in html_str.split("\n") if l.find(":") > 0])
			if 'version' in new:
				self["newVersion%s" % ltype].setText(new['version'])
				if ltype == "1x":
					self.newVersion1 = new['version'].strip()
				else:
					self.newVersion2 = new['version'].strip()
				self.canDownload = 1
		except Exception as error:
			print(error)

	def downloadCallBack(self, html, plik = "/tmp/picon.tgz"):
		try:
			self["status"].setText('Status: Rozpakowywanie')

			dest = self.piconLocationToInstall
			if self.piconTypeToInstall == "ZZPiconGLASS": dest = dest.replace("ZZPiconGLASS", "ZZPicon")
			elif self.piconTypeToInstall == "ZZPiconBLACK": dest = dest.replace("ZZPiconBLACK", "ZZPicon")
			elif self.piconTypeToInstall == "ZZPiconRJ": dest = dest.replace("ZZPiconRJ", "ZZPicon")
			elif self.piconTypeToInstall == "ZZPiconChristmas": dest = dest.replace("ZZPiconChristmas", "ZZPicon")
			elif self.piconTypeToInstall == "XPiconsBLACK": dest = dest.replace("XPiconsBLACK", "XPicons")
			elif self.piconTypeToInstall == "SetoXPicons": dest = dest.replace("SetoXPicons", "XPicons")

			picon_dir = os.path.join(dest, "picon")
			if not os.path.exists(picon_dir): os.makedirs(picon_dir)

			self["status"].setText('Status: Instalowanie')
			with tarfile.open(name = plik, mode = "r:gz") as t:
				safe_tar_extract(t, dest)
			self["status"].setText('Status: Zainstalowano nową wersję piconów')
			if os.path.exists(plik): os.remove(plik)
			self.askRestart()
		except:
			self["status"].setText('Status: Błąd archiwum !')
			traceback.print_exc()

	def askRestart(self):
		message = _("Aby picony były wczytane należy zrestartować GUI.\nZrestartować teraz?")
		ybox = self.session.openWithCallback(self.restartBox, MessageBox, message, MessageBox.TYPE_YESNO)
		ybox.setTitle(_("Restart GUI"))

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
		self["newVersion1x"].setText("Błąd")
		self["newVersion2x"].setText("Błąd")

	def restartBox(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

class DownloadJob(Job):
	def __init__(self, url, filename, file):
		Job.__init__(self, _("Downloading %s" %file))
		ChannelListDownloadTask(self, url, filename)

class DownloaderPostcondition(Condition):
	def check(self, task):
		return task.returncode == 0

	def getErrorMessage(self, task):
		return self.error_message

class ChannelListDownloadTask(Task):
	def __init__(self, job, url, path):
		Task.__init__(self, job, _("Downloading"))
		self.postconditions.append(DownloaderPostcondition())
		self.job = job
		self.url = url
		self.path = path
		self.error_message = ""
		self.last_recvbytes = 0
		self.error_message = None
		self.download = None
		self.aborted = False

	def run(self, callback):
		self.callback = callback
		self.download = downloadWithProgress(self.url,self.path)
		self.download.addProgress(self.download_progress)
		self.download.start().addCallback(self.download_finished).addErrback(self.download_failed)
		print("[ChannelListDownloadTask] downloading", self.url, "to", self.path)

	def abort(self):
		print("[ChannelListDownloadTask] aborting", self.url)
		if self.download:
			self.download.stop()
		self.aborted = True

	def download_progress(self, recvbytes, totalbytes):
		if ( recvbytes - self.last_recvbytes  ) > 10000:
			self.progress = int(100*(float(recvbytes)/float(totalbytes)))
			self.name = _("Downloading") + ' ' + "%d of %d kBytes" % (recvbytes/1024, totalbytes/1024)
			self.last_recvbytes = recvbytes

	def download_failed(self, failure_instance=None, error_message=""):
		self.error_message = error_message
		if error_message == "" and failure_instance is not None:
			self.error_message = failure_instance.getErrorMessage()
		Task.processFinished(self, 1)

	def download_finished(self, string=""):
		if self.aborted:
			self.finish(aborted = True)
		else:
			Task.processFinished(self, 0)
