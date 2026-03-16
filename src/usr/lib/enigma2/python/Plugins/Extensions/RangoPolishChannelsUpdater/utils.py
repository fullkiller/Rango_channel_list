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

def safe_tar_extract(tar, path=".", **kwargs):
	for member in tar.getmembers():
		member_path = os.path.join(path, member.name)
		if not os.path.abspath(member_path).startswith(os.path.abspath(path)):
			raise Exception("Attempted Path Traversal in Tar File")
	tar.extractall(path, **kwargs)

def safe_zip_extract(zf, path="."):
	for member in zf.infolist():
		member_path = os.path.join(path, member.filename)
		if not os.path.abspath(member_path).startswith(os.path.abspath(path)):
			raise Exception("Attempted Path Traversal in Zip File")
	zf.extractall(path)

def my_sync():
	try:
		os.sync()
	except AttributeError:
		os.system('sync')

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
		self.url1x = ''
		self.url2x = ''
		self.url3x = ''
		self.newVersion1 = '0'
		self.newVersion2 = '0'
		self.newVersion3 = '0'

		self.canDownload = 0
		self.url1 = ''
		self.url2 = ''
		self.url3 = ''

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
				downloadPage(self.url1x.encode(), '/tmp/chList1x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList1x1.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
			self.reloadUrlList(self.url1, self.url2, self.url3)

	def green(self):
		self["status"].show()
		try:
			if self.url2x != '' and self.canDownload == 1:
				self["status"].setText('Status: Pobieranie listy')
				downloadPage(self.url2x.encode(), '/tmp/chList2x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList2x1.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
			self.reloadUrlList(self.url1, self.url2, self.url3)

	def reloadUrlList(self, url1, url2, url3=None):
		self.url1 = url1
		self.url2 = url2
		self.url3 = url3

		getPage(self.url1.encode()).addCallback(self.versionInfoCallBack, "1x").addErrback(self.errorUpdate)
		getPage(self.url2.encode()).addCallback(self.versionInfoCallBack, "2x").addErrback(self.errorUpdate)
		if self.url3:
			getPage(self.url3.encode()).addCallback(self.versionInfoCallBack, "3x").addErrback(self.errorUpdate)

	def versionInfoCallBack(self, html, ltype="1x"):
		try:
			content = html.decode('utf-8')
			new = dict([ l.split(':',1) for l in content.split("\n") if l.find(":") > 0])
			if 'version' in new:
				if "newVersion%s" % ltype in self:
					self["newVersion%s" % ltype].setText(new['version'])
				if ltype == "1x":
					self.url1x = new['url']
					self.newVersion1 = new['version']
				elif ltype == "2x":
					self.url2x = new['url']
					self.newVersion2 = new['version']
					self.canDownload = 1
				elif ltype == "3x":
					self.url3x = new['url']
					self.newVersion3 = new['version']
		except Exception as error:
			 print(error)

	def downloadCallBack(self, html, plik = "/tmp/chList1x1.tgz"):
		try:
			for f in glob.glob('/etc/enigma2/*.tv'): os.remove(f)
			for f in glob.glob('/etc/enigma2/*.radio'): os.remove(f)
			for name in ('lamedb', 'satellites.xml', 'whitelist', 'blacklist', 'revision'):
				if os.path.exists('/etc/enigma2/' + name):
					os.remove('/etc/enigma2/' + name)

			self["status"].setText('Status: Rozpakowywanie')
			t = tarfile.open(name = plik, mode = "r:gz")
			safe_tar_extract(t, "/")
			t.close()
			reloadChannelList()
			self["status"].setText('Status: Zainstalowano nową wersję listy kanałów')
			os.remove(plik)
			my_sync()
		except:
			self["status"].setText('Status: Błąd archiwum !')

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
		if "newVersion1x" in self: self["newVersion1x"].setText("Błąd")
		if "newVersion2x" in self: self["newVersion2x"].setText("Błąd")

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
					for line in f:
						if "=" in line:
							self.curVersion = line.split("=")[1].strip().replace('"', "")
		except:
			pass
		return self.curVersion

	def getNewChListVersion(self, html):
		try:
			if os.path.exists("/tmp/revision"):
				with open("/tmp/revision", 'r') as f:
					for line in f:
						if "=" in line:
							key, val = line.split("=", 1)
							if key.strip() == "DATE":
								self.newVersion = val.strip().replace('"', "")
							if key.strip() == "VER":
								self.chID = val.strip().replace('"', "")

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
		downloadPage(b"http://addon.pkteam.pl/channel_lists_e2/revision", '/tmp/revision').addCallback(self.getNewChListVersion).addErrback(self.errorUpdate)

	def downloadFromUpload(self, failure=None):
		self["status"].setText("Status: Pobieranie listy " + self.chooseList)
		url = "http://upload.sat-elita.net.pl/download.php?id=" + self.chID
		downloadPage(url.encode(), '/tmp/lista.zip').addCallback(self.installChList).addErrback(self.errorUpdate)

	def downloadFromPKT(self):
		self["status"].setText("Status: Alternatywne pobieranie listy " + self.chooseList)
		url = "http://addon.pkteam.pl/channel_lists_e2/enigma2_list_by_djcrash-" + self.newVersion + ".zip"
		downloadPage(url.encode(), '/tmp/lista.zip').addCallback(self.installChList).addErrback(self.downloadFromUpload)

	def installChList(self, html):
		self["status"].setText('Status: Rozpakowywanie')
		try:
			if os.path.exists("/tmp/chList"): shutil.rmtree("/tmp/chList")
			os.makedirs("/tmp/chList")
			zf = zipfile.ZipFile(r"/tmp/lista.zip")
			safe_zip_extract(zf, "/tmp/chList/")
			zf.close()
		except:
			self["status"].setText('Status: Błąd archiwum !')
			return

		self["status"].setText('Status: Instalowanie')

		try:
			for f in glob.glob('/etc/enigma2/*.tv'): os.remove(f)
			for f in glob.glob('/etc/enigma2/*.radio'): os.remove(f)
			for name in ('lamedb', 'satellites.xml', 'whitelist', 'blacklist', 'revision'):
				if os.path.exists('/etc/enigma2/' + name):
					os.remove('/etc/enigma2/' + name)

			src_dir = '/tmp/chList/list_by_djcrash-e2_' + self.chooseList
			if os.path.exists(src_dir):
				for item in os.listdir(src_dir):
					s = os.path.join(src_dir, item)
					d = os.path.join('/etc/enigma2/', item)
					if os.path.isdir(s):
						if os.path.exists(d):
							shutil.rmtree(d)
						shutil.copytree(s, d)
					else:
						shutil.copy2(s, d)

			if os.path.exists('/tmp/chList/revision'):
				shutil.copy2('/tmp/chList/revision', '/etc/enigma2/revision')

			reloadChannelList()
			if os.path.exists("/tmp/chList"): shutil.rmtree("/tmp/chList")
			self.setTitle(_("Listy kanałów DjCrash - zainstalowana wersja: " + self.getCurrentChListVersion()))
			self["status"].setText('Status: Zainstalowano nową wersję listy kanałów')
			my_sync()
		except:
			self["status"].setText('Status: Błąd instalacji !')

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
		self["newVersion1x"].setText("Błąd")
		self["newVersion2x"].setText("Błąd")
		self["newVersion4x"].setText("Błąd")
		self["newVersion20x"].setText("Błąd")


#Picon Window
class CommonPiconListScreen(Screen):
	skin = """
		<screen position="center,center" size="860,340" >
			<widget name="typ" 		position="30,10" size="230,40" font="Regular;32" halign="left" />
			<widget name="typ0" 		position="300,10" size="500,40" font="Regular;32" halign="left" />
			<widget name="typ1"		position="600,10" size="100,40" font="Regular;32" halign="left" />
			<widget name="sats0" 		position="30,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats1x" 		position="300,90" size="190,25" font="Regular;18" halign="left" />
			<widget name="sats2x" 		position="600,90" size="290,25" font="Regular;18" halign="left" />
			<widget name="new0" 		position="30,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion1x" 	position="300,150" size="190,25" font="Regular;18" halign="left" />
			<widget name="newVersion2x" 	position="600,150" size="290,25" font="Regular;18" halign="left" />
			<widget name="newVersion3x" 	position="800,150" size="60,25" font="Regular;18" halign="left" />
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
		self.url1x = ''
		self.url2x = ''
		self.url3x = ''
		self.newVersion1 = '0'
		self.newVersion2 = '0'
		self.newVersion3 = '0'

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
		self["newVersion3x"] = Label("sprawdzam...")

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
		menu = []
		mounts = []
		if os.path.exists('/proc/mounts'):
			with open('/proc/mounts', 'r') as f:
				for line in f:
					parts = line.split()
					if len(parts) > 1:
						mounts.append(parts[1])

		for m in mounts:
			if m.startswith(('/media/cf', '/media/usb', '/media/card', '/media/hdd')):
				menu.append((_("%s (%s/%s/picon)" % (m, m, self.piconTypeToInstall)), os.path.join(m, self.piconTypeToInstall)))
				menu.append((_("%s (%s/picon)" % (m, m)), m))

		if self.piconTypeToInstall not in ("MasterPicon", "ZZPiconGLASS", "ZZPiconBLACK", "ZZPiconRJ", "ZZPiconChristmas" , ):
			menu.append((_("Flash (/%s/picon)" % self.piconTypeToInstall), "/" + self.piconTypeToInstall))
			menu.append((_("Flash (/usr/share/%s/picon)" % self.piconTypeToInstall), "/usr/share/enigma2/"+ self.piconTypeToInstall))
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
				self["status"].setText('Status: Pobieranie piconów')
				downloadPage(self.finalUrl.encode(), '/tmp/picon.tgz').addCallback(self.downloadCallBack, "/tmp/picon.tgz").addErrback(self.errorUpdate)
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

		getPage(self.url1.encode()).addCallback(self.versionInfoCallBack, "1x").addErrback(self.errorUpdate)
		getPage(self.url2.encode()).addCallback(self.versionInfoCallBack, "2x").addErrback(self.errorUpdate)
		getPage(self.url3.encode()).addCallback(self.versionInfoCallBack, "3x").addErrback(self.errorUpdate)

	def versionInfoCallBack(self, html, ltype="1x"):
		try:
			content = html.decode('utf-8')
			new = dict([ l.split(':',1) for l in content.split("\n") if l.find(":") > 0])
			if 'version' in new:
				if "newVersion%s" % ltype in self:
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
			self["status"].setText('Status: Rozpakowywanie')

			loc = self.piconLocationToInstall
			for s in ("GLASS", "BLACK", "RJ", "Christmas"):
				if self.piconTypeToInstall == "ZZPicon" + s:
					loc = loc.replace("ZZPicon" + s, "ZZPicon")
			if self.piconTypeToInstall == "XPiconsBLACK":
				loc = loc.replace("XPiconsBLACK", "XPicons")
			if self.piconTypeToInstall == "SetoXPicons":
				loc = loc.replace("SetoXPicons", "XPicons")

			target = os.path.join(loc, "picon")
			if not os.path.exists(target): os.makedirs(target)

			t = tarfile.open(name = plik, mode = "r:gz")
			safe_tar_extract(t, loc)
			t.close()

			self["status"].setText('Status: Zainstalowano nową wersję piconów')
			os.remove(plik)
			my_sync()
			self.askRestart()
		except:
			self["status"].setText('Status: Błąd archiwum !')

	def askRestart(self):
		message = _("Aby picony były wczytane należy zrestartować GUI.\nZrestartować teraz?")
		ybox = self.session.openWithCallback(self.restartBox, MessageBox, message, MessageBox.TYPE_YESNO)
		ybox.setTitle(_("Restart GUI"))

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
		if "newVersion1x" in self: self["newVersion1x"].setText("Błąd")
		if "newVersion2x" in self: self["newVersion2x"].setText("Błąd")

	def restartBox(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

## for Future use
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
		self.download = downloadWithProgress(self.url.encode() if isinstance(self.url, str) else self.url, self.path.encode() if isinstance(self.path, str) else self.path)
		self.download.addProgress(self.download_progress)
		self.download.start().addCallback(self.download_finished).addErrback(self.download_failed)
		print("[ChannelListDownloadTask] downloading", self.url, "to", self.path)

	def abort(self):
		print("[ChannelListDownloadTask] aborting", self.url)
		if self.download:
			self.download.stop()
		self.aborted = True

	def download_progress(self, recvbytes, totalbytes):
		if ( recvbytes - self.last_recvbytes  ) > 10000: # anti-flicker
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
