#!/usr/bin/python -u
# -*- coding: UTF-8 -*-

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
import re, os, tarfile, zipfile, shutil, sys
from twisted.web.client import getPage, downloadPage

def safe_tar_extract(tar_path, path=".", members=None, numeric_owner=False):
	try:
		with tarfile.open(tar_path) as tar:
			for member in tar.getmembers():
				member_path = os.path.join(path, member.name)
				if not os.path.abspath(member_path).startswith(os.path.abspath(path)):
					print("[ChannelListUpdate] Security alert: path traversal in tar file!")
					return False
			if sys.version_info >= (3, 5):
				tar.extractall(path, members, numeric_owner=numeric_owner)
			else:
				tar.extractall(path, members)
		return True
	except Exception as e:
		print("[ChannelListUpdate] Error extracting tar: %s" % str(e))
		return False

def safe_zip_extract(zip_path, path="."):
	try:
		with zipfile.ZipFile(zip_path, 'r') as z:
			for member in z.namelist():
				member_path = os.path.join(path, member)
				if not os.path.abspath(member_path).startswith(os.path.abspath(path)):
					print("[ChannelListUpdate] Security alert: path traversal in zip file!")
					return False
			z.extractall(path)
		return True
	except Exception as e:
		print("[ChannelListUpdate] Error extracting zip: %s" % str(e))
		return False

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
			with open('/etc/enigma2/userbouquet.version', 'r') as f:
				self.channelListVersion = f.read().split('\n')[0]
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
				downloadPage(self.url1x.encode('utf-8'), b'/tmp/chList1x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList1x1.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
			self.reloadUrlList(self.url1, self.url2)

	def green(self):
		self["status"].show()
		try:
			if self.url2x != '' and self.canDownload == 1:
				self["status"].setText('Status: Pobieranie listy')
				downloadPage(self.url2x.encode('utf-8'), b'/tmp/chList2x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList2x1.tgz").addErrback(self.errorUpdate)
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
			content = html.decode('utf-8')
			new = dict([ l.split(':',1) for l in content.split("\n") if l.find(":") > 0])
			if 'version' in new:
				self["newVersion%s" % ltype].setText(new['version'])
				if ltype == "1x":
					self.url1x = new['url'].strip()
					self.newVersion1 = new['version']
				else:
					self.url2x = new['url'].strip()
					self.newVersion2 = new['version']
				self.canDownload = 1
		except Exception as error:
			 print(error)

	def downloadCallBack(self, html, plik = "/tmp/chList1x1.tgz"):
		try:
			self["status"].setText('Status: Czyszczenie starej listy')
			for f in ["/etc/enigma2/*.tv", "/etc/enigma2/*.radio", "/etc/enigma2/lamedb", "/etc/enigma2/satellites.xml", "/etc/enigma2/whitelist", "/etc/enigma2/blacklist", "/etc/enigma2/revision"]:
				if '*' in f:
					import glob
					for gf in glob.glob(f):
						os.remove(gf)
				elif os.path.exists(f):
					os.remove(f)

			self["status"].setText('Status: Rozpakowywanie')
			if safe_tar_extract(plik, "/"):
				reloadChannelList()
				self["status"].setText('Status: Zainstalowano nową wersję listy kanałów')
				if os.path.exists(plik): os.remove(plik)
				if hasattr(os, 'sync'): os.sync()
				else: os.system('sync')
			else:
				self["status"].setText('Status: Błąd podczas rozpakowywania !')
		except Exception as e:
			print(e)
			self["status"].setText('Status: Błąd podczas instalacji !')

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
			with open("/etc/enigma2/revision", 'r') as f:
				content = f.read()
				paths = content.split("\n")
				for path in paths:
					if '=' in path:
						self.curVersion = path.split("=")[1].strip()
		except:
			return self.curVersion
		return self.curVersion

	def getNewChListVersion(self, html):
		try:
			with open("/tmp/revision", 'r') as f:
				content = f.read()
				paths = content.split("\n")
				for path in paths:
					if path.split("=")[0] == "DATE":
						self.newVersion = path.split("=")[1].replace('"', "").strip()
					if path.split("=")[0] == "VER":
						self.chID = path.split("=")[1].replace('"', "").strip()

			self["newVersion1x"].setText(self.newVersion)
			self["newVersion2x"].setText(self.newVersion)
			self["newVersion4x"].setText(self.newVersion)
			self["newVersion20x"].setText(self.newVersion)
			self.canDownload = 1
		except:
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
		downloadPage(b"http://addon.pkteam.pl/channel_lists_e2/revision", b'/tmp/revision').addCallback(self.getNewChListVersion).addErrback(self.errorUpdate)

	def downloadFromUpload(self, failure=None):
		self["status"].setText("Status: Pobieranie listy " + self.chooseList)
		url = "http://upload.sat-elita.net.pl/download.php?id=" + self.chID
		downloadPage(url.encode('utf-8'), b'/tmp/lista.zip').addCallback(self.installChList).addErrback(self.downloadFailed)

	def downloadFromPKT(self):
		self["status"].setText("Status: Alternatywne pobieranie listy " + self.chooseList)
		url = "http://addon.pkteam.pl/channel_lists_e2/enigma2_list_by_djcrash-" + self.newVersion + ".zip"
		downloadPage(url.encode('utf-8'), b'/tmp/lista.zip').addCallback(self.installChList).addErrback(self.downloadFromUpload)

	def downloadFailed(self, failure):
		self["status"].setText('Status: Błąd pobierania !')

	def installChList(self, html):
		self["status"].setText('Status: Rozpakowywanie')
		tmp_dir = "/tmp/chList/"
		if os.path.exists(tmp_dir):
			shutil.rmtree(tmp_dir)
		os.makedirs(tmp_dir)

		if safe_zip_extract("/tmp/lista.zip", tmp_dir):
			self["status"].setText('Status: Instalowanie')
			for f in ["/etc/enigma2/*.tv", "/etc/enigma2/*.radio", "/etc/enigma2/lamedb", "/etc/enigma2/satellites.xml", "/etc/enigma2/whitelist", "/etc/enigma2/blacklist", "/etc/enigma2/revision"]:
				if '*' in f:
					import glob
					for gf in glob.glob(f): os.remove(gf)
				elif os.path.exists(f): os.remove(f)

			src_dir = os.path.join(tmp_dir, 'list_by_djcrash-e2_' + self.chooseList)
			if os.path.exists(src_dir):
				for item in os.listdir(src_dir):
					s = os.path.join(src_dir, item)
					d = os.path.join('/etc/enigma2/', item)
					if os.path.isdir(s):
						if not os.path.exists(d): os.makedirs(d)
						for subitem in os.listdir(s):
							shutil.copy2(os.path.join(s, subitem), os.path.join(d, subitem))
					else:
						shutil.copy2(s, d)

			rev_file = os.path.join(tmp_dir, 'revision')
			if os.path.exists(rev_file):
				shutil.copy2(rev_file, '/etc/enigma2/revision')

			reloadChannelList()
			shutil.rmtree(tmp_dir)
			if os.path.exists("/tmp/lista.zip"): os.remove("/tmp/lista.zip")
			self.setTitle(_("Listy kanałów DjCrash - zainstalowana wersja: " + self.getCurrentChListVersion()))
			self["status"].setText('Status: Zainstalowano nową wersję listy kanałów')
			if hasattr(os, 'sync'): os.sync()
			else: os.system('sync')
		else:
			self["status"].setText('Status: Błąd archiwum !')

	def errorUpdate(self, html):
		self["status"].show()
		self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
		self["newVersion1x"].setText("Błąd")
		self["newVersion2x"].setText("Błąd")
		self["newVersion4x"].setText("Błąd")
		self["newVersion20x"].setText("Błąd")

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
			<widget name="newVersion3x" 	position="1,1" size="1,1" font="Regular;1" />
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
			with open('/etc/enigma2/picon.version', 'r') as f:
				self.piconListVersion = f.read().split('\n')[0]
		except:
			self.piconListVersion = 'nieznana'

		self["newVersion1x"] = Label("sprawdzam...")
		self["newVersion2x"] = Label("sprawdzam...")
		self["newVersion3x"] = Label("")

		self["key_red"] = Label("Pobierz")
		self["key_green"] = Label("Pobierz")

		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"red": self.red, "green": self.green, "cancel": self.close , "ok": self.close}, -1)

	def choiceBoxPiconSize(self):
		menu = [
			(_("XPicon - 220x132"), "XPicons"),
			(_("XPicon BLACK - 220x132"), "XPiconsBLACK"),
			(_("SetoXPicon - 220x132"), "SetoXPicons"),
			(_("ZZPicon - 400x170"), "ZZPicon"),
			(_("ChristmasZZPicon - 400x170"), "ZZPiconChristmas"),
			(_("ZZPicon GLASS - 400x170"), "ZZPiconGLASS"),
			(_("ZZPicon BLACK - 400x170"), "ZZPiconBLACK"),
			(_("ZZPicon_RJ - 400x170"), "ZZPiconRJ"),
			(_("MasterPicon - 1920x150"), "MasterPicon")
		]
		self.session.openWithCallback(self.choicePiconSizeCB, ChoiceBox, title=_("Wybierz rozmiar picon"), list=menu)

	def choicePiconSizeCB(self, choice):
		if choice:
			self.piconTypeToInstall = choice[1]
			self.choiceBoxPiconLocation()

	def choiceBoxPiconLocation(self):
		menu = []
		if os.path.exists('/proc/mounts'):
			with open('/proc/mounts', 'r') as f:
				for line in f:
					parts = line.split()
					if len(parts) >= 2:
						mount_point = parts[1]
						if any(x in mount_point for x in ['/media/cf', '/media/usb', '/media/card', '/hdd']):
							name = mount_point.split('/')[-1].upper()
							menu.append((_("%s (%s/%s/picon)") % (name, mount_point, self.piconTypeToInstall), os.path.join(mount_point, self.piconTypeToInstall)))
							menu.append((_("%s (%s/picon)") % (name, mount_point), mount_point))

		if self.piconTypeToInstall not in ("MasterPicon", "ZZPiconGLASS", "ZZPiconBLACK", "ZZPiconRJ", "ZZPiconChristmas"):
			menu.append((_("Flash (/%s/picon)") % self.piconTypeToInstall, "/" + self.piconTypeToInstall))
			menu.append((_("Flash (/usr/share/enigma2/%s/picon)") % self.piconTypeToInstall, "/usr/share/enigma2/" + self.piconTypeToInstall))
			menu.append((_("Flash (/picon)"), "/"))
			menu.append((_("Flash (/usr/share/enigma2/picon)"), "/usr/share/enigma2/"))

		self.session.openWithCallback(self.choiceBoxPiconLocationCB, ChoiceBox, title=_("Wybierz lokalizację picon"), list=menu)

	def choiceBoxPiconLocationCB(self, choice):
		if choice:
			self.piconLocationToInstall = choice[1]
			self.prepareDownload()

	def prepareDownload(self):
		self.finalUrl = "%s/%s/%s/%s%s.tar.gz" % (self.baseUrl, self.piconPositionToInstall, self.piconTypeToInstall, self.piconTypeToInstall, self.piconPositionToInstall)
		self["status"].show()
		try:
			if self.canDownload == 1:
				self["status"].setText('Status: Pobieranie piconów')
				downloadPage(self.finalUrl.encode('utf-8'), b'/tmp/picon.tgz').addCallback(self.downloadCallBack, "/tmp/picon.tgz").addErrback(self.errorUpdate)
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
			self["status"].setText('Status: Rozpakowywanie')
			loc = self.piconLocationToInstall
			for t in ["ZZPiconGLASS", "ZZPiconBLACK", "ZZPiconRJ", "ZZPiconChristmas"]:
				if self.piconTypeToInstall == t: loc = loc.replace(t, "ZZPicon")
			for t in ["XPiconsBLACK", "SetoXPicons"]:
				if self.piconTypeToInstall == t: loc = loc.replace(t, "XPicons")

			picon_dir = os.path.join(loc, "picon")
			if not os.path.exists(picon_dir): os.makedirs(picon_dir)

			self["status"].setText('Status: Instalowanie')
			if safe_tar_extract(plik, loc):
				self["status"].setText('Status: Zainstalowano nową wersję piconów')
				if os.path.exists(plik): os.remove(plik)
				self.askRestart()
			else:
				self["status"].setText('Status: Błąd podczas rozpakowywania !')
		except:
			self["status"].setText('Status: Błąd archiwum !')

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
		self.url = url
		self.path = path
		self.last_recvbytes = 0
		self.error_message = None
		self.download = None
		self.aborted = False

	def run(self, callback):
		self.callback = callback
		self.download = downloadWithProgress(self.url.encode('utf-8'), self.path.encode('utf-8'))
		self.download.addProgress(self.download_progress)
		self.download.start().addCallback(self.download_finished).addErrback(self.download_failed)

	def abort(self):
		if self.download: self.download.stop()
		self.aborted = True

	def download_progress(self, recvbytes, totalbytes):
		if (recvbytes - self.last_recvbytes) > 10000:
			self.progress = int(100*(float(recvbytes)/float(totalbytes)))
			self.name = _("Downloading") + ' ' + "%d of %d kBytes" % (recvbytes/1024, totalbytes/1024)
			self.last_recvbytes = recvbytes

	def download_failed(self, failure_instance=None, error_message=""):
		self.error_message = error_message or (failure_instance.getErrorMessage() if failure_instance else "")
		Task.processFinished(self, 1)

	def download_finished(self, string=""):
		Task.processFinished(self, 0 if not self.aborted else 1)
