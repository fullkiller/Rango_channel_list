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

def is_path_safe(destination, member_name):
	dest_path = os.path.realpath(destination)
	target_path = os.path.realpath(os.path.join(destination, member_name))
	if os.path.commonpath([dest_path, target_path]) != dest_path:
		return False
	if dest_path == '/':
		allowed_prefixes = ['/usr', '/etc', '/tmp', '/var', '/media']
		if not any(target_path.startswith(p) for p in allowed_prefixes):
			return False
	return True

def safe_tar_extract(tar_path, dest_path, **kwargs):
	if not os.path.exists(dest_path):
		os.makedirs(dest_path)
	t = tarfile.open(tar_path, 'r:gz')
	try:
		for member in t.getmembers():
			if not is_path_safe(dest_path, member.name):
				print("[RangoUpdater] Refusing to extract unsafe member: %s" % member.name)
				continue
			t.extract(member, path=dest_path, **kwargs)
	finally:
		t.close()

def safe_zip_extract(zip_path, dest_path):
	if not os.path.exists(dest_path):
		os.makedirs(dest_path)
	z = zipfile.ZipFile(zip_path, 'r')
	try:
		for member in z.infolist():
			if not is_path_safe(dest_path, member.filename):
				print("[RangoUpdater] Refusing to extract unsafe member: %s" % member.filename)
				continue
			z.extract(member, path=dest_path)
	finally:
		z.close()

def reloadChannelList():
	try:
		print ("[ChannelListUpdate] reloading channel list")
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
		print ("[ChannelListUpdate] error reloading channel list !")
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

		#### TODO read correctly installed channel list version....
		try:
			self.channelListVersion = open('/etc/enigma2/userbouquet.version').read().split('\n')[0]
		except:
			self.channelListVersion = 'nieznana'

		self["newVersion1x"] = Label("sprawdzam...")
		self["newVersion2x"] = Label("sprawdzam...")

		#self.reloadUrlList()

		self["key_red"] = Label("Pobierz")
		self["key_green"] = Label("Pobierz")

		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"red": self.red, "green": self.green, "cancel": self.close , "ok": self.close}, -1)

	def red(self):
		self["status"].show()
		try:
			if self.url1x != '' and self.canDownload == 1:
				self["status"].setText('Status: Pobieranie listy')
				downloadPage(self.url1x, '/tmp/chList1x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList1x1.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
			self.reloadUrlList()

	def green(self):
		self["status"].show()
		try:
			if self.url2x != '' and self.canDownload == 1:
				self["status"].setText('Status: Pobieranie listy')
				downloadPage(self.url2x, '/tmp/chList2x1.tgz').addCallback(self.downloadCallBack, "/tmp/chList2x1.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
			self.reloadUrlList()

	def reloadUrlList(self, url1, url2):
		# Little dirty, but I assume that we can try to get channel list urls one more time
		self.url1 = url1
		self.url2 = url2

		getPage(self.url1).addCallback(self.versionInfoCallBack, "1x").addErrback(self.errorUpdate)
		getPage(self.url2).addCallback(self.versionInfoCallBack, "2x").addErrback(self.errorUpdate)

	def versionInfoCallBack(self, html, ltype="1x"):
		try:
			if isinstance(html, bytes):
				html = html.decode('utf-8')
			new = dict([ l.split(':',1) for l in html.split("\n") if l.find(":") > 0])
			if 'version' in new:
				self["newVersion%s" % ltype].setText(new['version'])
				if ltype == "1x":
					self.url1x = new['url']
					self.newVersion1 = new['version']
				else:
					self.url2x = new['url']
					self.newVersion2 = new['version']
					self.canDownload = 1
		except Exception as error:
			 print(error)
		#except:  FIXED it did nothing acypaczom
		#	pass FIXED acypaczom

	def downloadCallBack(self, html, plik = "/tmp/chList1x1.tgz"):
		try:
			for f in glob.glob('/etc/enigma2/*.tv'):
				os.remove(f)
			for f in glob.glob('/etc/enigma2/*.radio'):
				os.remove(f)
			for f in ('lamedb', 'satellites.xml', 'whitelist', 'blacklist', 'revision'):
				if os.path.exists('/etc/enigma2/' + f):
					os.remove('/etc/enigma2/' + f)
			self["status"].setText('Status: Rozpakowywanie')
			safe_tar_extract(plik, "/")
			reloadChannelList()
			self["status"].setText('Status: Zainstalowano nową wersję listy kanałów')
			os.remove(plik)
		except:
			self["status"].setText('Status: Błąd archiwum !')

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
			file = open("/etc/enigma2/revision", 'r')
			content = file.read()
			paths = content.split("\n")
			for path in paths:
				self.curVersion = path.split("=")[1]
		except:
			return self.curVersion
		return self.curVersion

	def getNewChListVersion(self, html):
		try:
			file = open("/tmp/revision", 'r')
			content = file.read()
			file.close()
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
			#self.downloadFromUpload()
			self.downloadFromPKT()
		else:
		# let's try to connect server one more time
			self.reloadUrlList()

	def reloadUrlList(self):
		downloadPage("http://addon.pkteam.pl/channel_lists_e2/revision", '/tmp/revision').addCallback(self.getNewChListVersion).addErrback(self.errorUpdate)

	def downloadFromUpload(self, html=None):
		self["status"].setText("Status: Pobieranie listy " + self.chooseList)
		downloadPage("http://upload.sat-elita.net.pl/download.php?id=" + self.chID, '/tmp/lista.zip').addCallback(self.installChList).addErrback(self.errorUpdate)

	def downloadFromPKT(self):
		self["status"].setText("Status: Alternatywne pobieranie listy " + self.chooseList)
		downloadPage("http://addon.pkteam.pl/channel_lists_e2/enigma2_list_by_djcrash-" + self.newVersion + ".zip", '/tmp/lista.zip').addCallback(self.installChList).addErrback(self.downloadFromUpload)

	def installChList(self, html):
		self["status"].setText('Status: Rozpakowywanie')
		try:
			safe_zip_extract("/tmp/lista.zip", "/tmp/chList/")
		except:
			self["status"].setText('Status: Błąd archiwum !')
			return

		self["status"].setText('Status: Instalowanie')

		for f in glob.glob('/etc/enigma2/*.tv'):
			os.remove(f)
		for f in glob.glob('/etc/enigma2/*.radio'):
			os.remove(f)
		for f in ('lamedb', 'satellites.xml', 'whitelist', 'blacklist', 'revision'):
			if os.path.exists('/etc/enigma2/' + f):
				os.remove('/etc/enigma2/' + f)

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
		if os.path.exists('/tmp/chList'):
			shutil.rmtree('/tmp/chList')
		self.setTitle(_("Listy kanałów DjCrash - zainstalowana wersja: " + self.getCurrentChListVersion()))
		self["status"].setText('Status: Zainstalowano nową wersję listy kanałów')

	def errorUpdate(self, html):
		self["status"].show()
		# Let's try to get again correct URLS
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

		#### TODO read correctly installed picon list version....
		try:
			self.piconListVersion = open('/etc/enigma2/picon.version').read().split('\n')[0]
		except:
			self.piconListVersion = 'nieznana'

		self["newVersion1x"] = Label("sprawdzam...")
		self["newVersion2x"] = Label("sprawdzam...")

		#self.reloadUrlList()

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
		(mycf, myusb, myusb2, myusb3, mysd, myhdd, myhdd2) = ('', '', '', '', '', '', '')
		menu = []
		if fileExists('/proc/mounts'):
			fileExists('/proc/mounts')
			f = open('/proc/mounts', 'r')
			for line in f.readlines():
				if line.find('/media/cf') != -1:
					mycf = '/media/cf/'
					continue
				if line.find('/media/usb') != -1:
					myusb = '/media/usb/'
					continue
				if line.find('/media/usb2') != -1:
					myusb2 = '/media/usb2/'
					continue
				if line.find('/media/usb3') != -1:
					myusb3 = '/media/usb3/'
					continue
				if line.find('/media/card') != -1:
					mysd = '/media/card/'
					continue
				if line.find('/hdd') != -1:
					myhdd = '/media/hdd/'
					continue
				if line.find('/hdd2') != -1:
					myhdd = '/media/hdd2/'
					continue
			f.close()

		if mycf:
			menu.append((_("Compact Flash (/media/cf/"+self.piconTypeToInstall + "/picon)"), mycf + "/" + self.piconTypeToInstall))
		else:
		      mycf
		if myusb:
			menu.append((_("USB-1 (/media/usb/"+self.piconTypeToInstall + "/picon)"), myusb+ "/" + self.piconTypeToInstall))
			menu.append((_("USB-1 (/media/usb/picon)"), myusb))
		else:
			myusb
		if myusb2:
			menu.append((_("USB-2 (/media/usb2/"+self.piconTypeToInstall + "/picon)"), myusb2+ "/" + self.piconTypeToInstall))
			menu.append((_("USB-2 (/media/usb2/picon)"), myusb2))
		else:
			myusb2
		if myusb3:
			menu.append((_("USB-3 (/media/usb3/"+self.piconTypeToInstall + "/picon)"), myusb3+ "/" + self.piconTypeToInstall))
			menu.append((_("USB-3 (/media/usb3/picon)"), myusb3))
		else:
			myusb3
		if mysd:
			menu.append((_("SD Card (/media/card/"+self.piconTypeToInstall + "/picon)"), mysd+ "/" + self.piconTypeToInstall))
		else:
			mysd
		if myhdd:
			menu.append((_("HDD (/media/hdd/"+self.piconTypeToInstall + "/picon)"), myhdd+ "/" + self.piconTypeToInstall))
			menu.append((_("HDD (/media/hdd/picon)"), myhdd))
		else:
			myhdd
		if myhdd2:
			menu.append((_("HDD2 (/media/hdd2/"+self.piconTypeToInstall + "/picon)"), myhdd2+ "/" + self.piconTypeToInstall))
			menu.append((_("HDD2 (/media/hdd2/picon)"), myhdd2))
		else:
			myhdd2

		if self.piconTypeToInstall not in ("MasterPicon", "ZZPiconGLASS", "ZZPiconBLACK", "ZZPiconRJ", "ZZPiconChristmas" , ):
			menu.append((_("Flash (/"+self.piconTypeToInstall + "/picon)"), "/" + self.piconTypeToInstall))
			menu.append((_("Flash (/usr/share/"+self.piconTypeToInstall + "/picon)"), "/usr/share/enigma2"+ "/" + self.piconTypeToInstall))
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
		print ("==============================")
		print (self.baseUrl)
		print (self.piconPositionToInstall)
		print (self.piconTypeToInstall)
		print ("==============================")
		self.finalUrl = self.baseUrl + "/" + self.piconPositionToInstall + "/" + self.piconTypeToInstall + "/"+ self.piconTypeToInstall + self.piconPositionToInstall + ".tar.gz"

		print (self.finalUrl)
		self["status"].show()
		try:
			if self.finalUrl != '' and self.canDownload == 1:
				self["status"].setText('Status: Pobieranie piconów')
				downloadPage(self.finalUrl, '/tmp/picon.tgz').addCallback(self.downloadCallBack, "/tmp/picon.tgz").addErrback(self.errorUpdate)
		except:
			self["status"].setText('Status: Nie mogę się połączyć z serwerem !')
			self.reloadUrlList()

	def red(self):
		self.piconPositionToInstall = "130"
		self.choiceBoxPiconSize()

	def green(self):
		self.piconPositionToInstall = "192"
		self.choiceBoxPiconSize()

	def reloadUrlList(self, baseUrl, url1, url2, url3):
		# Little dirty, but I assume that we can try to get channel list urls one more time

		self.baseUrl = baseUrl
		self.url1 = url1
		self.url2 = url2
		self.url3 = url3

		getPage(self.url1).addCallback(self.versionInfoCallBack, "1x").addErrback(self.errorUpdate)
		getPage(self.url2).addCallback(self.versionInfoCallBack, "2x").addErrback(self.errorUpdate)

	def versionInfoCallBack(self, html, ltype="1x"):
		try:
			if isinstance(html, bytes):
				html = html.decode('utf-8')
			new = dict([ l.split(':',1) for l in html.split("\n") if l.find(":") > 0])
			if 'version' in new:
				self["newVersion%s" % ltype].setText(new['version'])
				if ltype == "1x":
					self.newVersion1 = new['version']
				else:
					self.newVersion2 = new['version']
				self.canDownload = 1
		except Exception as error:
			print(error)
	 #	except:
	#		pass

	def downloadCallBack(self, html, plik = "/tmp/picon.tgz"):
		try:
			self["status"].setText('Status: Rozpakowywanie')

			print ("Instalowanie piconów do: ", self.piconLocationToInstall)
			if self.piconTypeToInstall in ("ZZPiconGLASS"):
				self.piconLocationToInstall = self.piconLocationToInstall.replace("ZZPiconGLASS", "ZZPicon")
			if self.piconTypeToInstall in ("ZZPiconBLACK"):
				self.piconLocationToInstall = self.piconLocationToInstall.replace("ZZPiconBLACK", "ZZPicon")
			if self.piconTypeToInstall in ("ZZPiconRJ"):
				self.piconLocationToInstall = self.piconLocationToInstall.replace("ZZPiconRJ", "ZZPicon")
			if self.piconTypeToInstall in ("ZZPiconChristmas"):
				self.piconLocationToInstall = self.piconLocationToInstall.replace("ZZPiconChristmas", "ZZPicon")
			if self.piconTypeToInstall in ("XPiconsBLACK"):
				self.piconLocationToInstall = self.piconLocationToInstall.replace("XPiconsBLACK","XPicons")
			if self.piconTypeToInstall in ("SetoXPicons"):
				self.piconLocationToInstall = self.piconLocationToInstall.replace("SetoXPicons","XPicons")

			picon_dir = os.path.join(self.piconLocationToInstall, "picon")
			if not os.path.exists(picon_dir):
				os.makedirs(picon_dir)

			self["status"].setText('Status: Instalowanie')
			safe_tar_extract(plik, self.piconLocationToInstall)
			self["status"].setText('Status: Zainstalowano nową wersję piconów')
			os.remove(plik)
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
		self["newVersion1x"].setText("Błąd")
		self["newVersion2x"].setText("Błąd")

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
		self.download = downloadWithProgress(self.url,self.path)
		self.download.addProgress(self.download_progress)
		self.download.start().addCallback(self.download_finished).addErrback(self.download_failed)
		print ("[ChannelListDownloadTask] downloading", self.url, "to", self.path)

	def abort(self):
		print ("[ChannelListDownloadTask] aborting", self.url)
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
