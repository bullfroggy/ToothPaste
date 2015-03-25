import os,sys,bluetooth,ntpath,subprocess,threading,time,atexit
from shutil import move
from threading import *
from subprocess import Popen, PIPE
from PySide import QtCore, QtGui
from PySide.QtCore import *
from PySide.QtGui import *
bt = False
device_list = []
checking_list = []
stop = False
truecheck = False
fileCount = 0
currentTab = 0

class Thread(threading.Thread):
	def __init__(self, t, *args):
		threading.Thread.__init__(self, target=t, args=args)
		self.start()

class Form(QDialog):
	def __init__(self, parent=None):
		super(Form, self).__init__(parent)
		self.setWindowTitle("Bluetooth")
		self.mainLayout = QtGui.QVBoxLayout()            
		pixmap = QtGui.QPixmap("toothbrush.png")
		toothbrush = QtGui.QLabel(self)
		toothbrush.setPixmap(pixmap)
		self.setMinimumHeight(330)
		self.setMinimumWidth(550)

		self.titleLabel = QtGui.QLabel(self)
		self.titleLabel.setText("ToothPaste")				
		self.titleLabel.setAlignment(QtCore.Qt.AlignHCenter)
		self.titleLabel.setFont(QtGui.QFont("Courier", 22, QtGui.QFont.Bold))
		self.mainLayout.addWidget(self.titleLabel)                

		splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		splitter1.addWidget(toothbrush)
		self.infoBox()
		splitter1.addWidget(self.infoBox)
		self.mainLayout.addWidget(splitter1)
		
		time.sleep(.5)

		tabs = QtGui.QTabWidget()

		btButton = QtGui.QIcon("btbutton.png")
		tabs.addTab(bluetoothTab(), btButton, "Bluetooth")
		tabs.setTabPosition(QtGui.QTabWidget.West)          

		self.mainLayout.addWidget(tabs)

		self.setLayout(self.mainLayout)

	def infoBox(self):
		self.infoBox = QtGui.QGroupBox()
		self.infoBoxLayout = QtGui.QVBoxLayout()

		self.computerNameLabel = QtGui.QLabel(self)
		self.computerName = os.getenv('COMPUTERNAME') # get computer name
		self.computerNameLabel.setText("Computer name: " + self.computerName)

		self.btLabel = QtGui.QLabel(self)
		try:
			sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
			sock.bind(("",19))
			self.bluetoothAddress = sock.getsockname()[0]
			self.btLabel.setText("Your Local Bluetooth Address: " + self.bluetoothAddress)
			sock.close()
		except:
			self.btLabel.setText("Unable to obtain Bluetooth Address")

		self.bluetoothEnabledLabel = QtGui.QLabel(self)
		self.isBtEnabled = checkBtEnabled()
		self.isBtEnabled.checkBt.connect(self.showBluetooth)
		self.isBtEnabled.start()
		time.sleep(0.1)

		self.infoBoxLayout.addWidget(self.computerNameLabel)
		self.infoBoxLayout.addWidget(self.btLabel)
		self.infoBoxLayout.addWidget(self.bluetoothEnabledLabel)

		self.infoBox.setLayout(self.infoBoxLayout)    

	def showBluetooth(self, checkBt):
		global bt
		self.bluetoothEnabledLabel.setText(checkBt)

class bluetoothTab(QtGui.QWidget):
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)

		self.bluetoothLayout = QtGui.QVBoxLayout()

		time.sleep(0.1)
		self.listeningLabel = QtGui.QLabel(self)

		self.listener = ListenBt()
		self.listener.communicateArray.connect(self.acceptBt)
		self.listener.message.connect(self.fileMessage)
		self.listener.start()
		self.listeningLabel.setText("Listening...")


		time.sleep(0.1)

		self.scanner = ScanBt()
		self.scanner.communicateArray.connect(self.acceptBt)
		self.scanner.start()
		time.sleep(0.1)


		self.listeningLabel.setText("Scanning and listening...")
		self.listeningLabel.setAlignment(Qt.AlignTop)
		self.bluetoothLayout.addWidget(self.listeningLabel)

		self.couldNotFindLabel = QtGui.QLabel(self)
		self.couldNotFindLabel.setText("")
		self.bluetoothLayout.addWidget(self.couldNotFindLabel)

		self.setLayout(self.bluetoothLayout)	

	def couldNotFind(self, message):
		self.couldNotFindLabel.setText(message)

	def acceptBt(self, cArray):
		self.allFiles = []
		self.listshow = False

		self.receiver = Receive()
		self.receiver.setArray(cArray)
		self.receiver.message.connect(self.fileMessage)
		self.receiver.isConnected.connect(self.directConnect)
		self.receiver.theConnection.connect(self.acceptConnection)
		time.sleep(0.1)
		self.receiver.start()

		self.btButton = QtGui.QPushButton(cArray[0] + "\n" + cArray[2])
		self.btButton.setIcon(QtGui.QPixmap("computer.png"))
		self.btButton.setVisible(True)
		self.btButton.setMinimumHeight(40)
		self.btButton.setMaximumHeight(40)                

		self.directConnectButton = QtGui.QPushButton("Direct Connect")
		self.directConnectButton.setIcon(QtGui.QPixmap("connect.png"))
		self.dc = DirectConnect()
		self.dc.setArray(cArray)
		self.dc.setDCButton(self.directConnectButton)
		self.directConnectButton.clicked.connect(self.dc.start)

		self.tempMessage = QtGui.QLabel(self)
		self.bluetoothLayout.addWidget(self.tempMessage)

		self.sendButton = QtGui.QPushButton()
		self.sendButton.setIcon(QtGui.QPixmap("send.png"))
		self.sendButton.setToolTip("Send")
		self.sendButton.clicked.connect(lambda self=self: self.sendFileInformation(cArray))
		self.sendButton.setVisible(False)

		self.browseButton = QtGui.QPushButton()
		self.browseButton.setIcon(QtGui.QPixmap("browse.png"))
		self.browseButton.setToolTip("Browse")
		self.browseButton.clicked.connect(lambda self=self: self.browseRequest(cArray))
		self.browseButton.setVisible(False)

		self.scrollArea = QtGui.QScrollArea()
		self.scrollArea.setVisible(False)
		self.scrollArea.setWindowTitle("Public Files")                

		self.receiveButton = QtGui.QPushButton()
		self.receiveButton.setIcon(QtGui.QPixmap("receive.png"))
		self.receiveButton.setToolTip("Download History")
		self.receiveButton.clicked.connect(self.showFileList)
		self.receiveButton.setVisible(False)

		self.closeConnectionButton = QtGui.QPushButton("Close connection")
		self.closeConnectionButton.setIcon(QtGui.QPixmap("close.png"))
		self.closeConnectionButton.setToolTip("Close")
		self.closeConnectionButton.clicked.connect(lambda self=self: self.closeConnection(cArray)) 
		self.closeConnectionButton.setVisible(False)

		self.dcSplitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
		self.dcSplitter.addWidget(self.btButton)
		self.dcSplitter.addWidget(self.directConnectButton)
		self.dcSplitter.addWidget(self.sendButton)
		self.dcSplitter.addWidget(self.browseButton)
		self.dcSplitter.addWidget(self.receiveButton)
		self.dcSplitter.addWidget(self.closeConnectionButton)
		self.bluetoothLayout.addWidget(self.dcSplitter)

		self.fileNameLabel = QtGui.QLabel(self)
		self.fileNameLabel.setText("")
		self.fileNameLabel.setVisible(False)

		self.progressBar = QtGui.QProgressBar()
		self.progressBar.setGeometry(100,100,150,50)
		self.progressBar.setVisible(False)

		self.progressSplitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
		self.progressSplitter.addWidget(self.fileNameLabel)
		self.progressSplitter.addWidget(self.progressBar)
		self.bluetoothLayout.addWidget(self.progressSplitter)
		self.fileList = QtGui.QLabel(self)
		self.fileList.setVisible(False)
		self.bluetoothLayout.addWidget(self.fileList)

		self.receiver.setButtons(self.directConnectButton, self.btButton, self.sendButton, self.browseButton, self.receiveButton, self.closeConnectionButton)

		atexit.register(self.sendDisconnect, cArray)


	def showFileList(self):
		if self.listshow == False:
			self.fileList.setVisible(True)
			self.listshow = True
		else:
			self.fileList.close()
			self.listshow = False

	def browseRequest(self, cArray):
		sock = cArray[1]
		request = bytes("requestingfiles\n", 'utf-8')
		sock.send(request)

	def sendDisconnect(self, cArray):
		sock = cArray[1]
		destroy = bytes("destroy\n", 'utf-8')
		sock.send(destroy)

	def setProgress(self, currentPercent):
		if currentPercent >= 100:
			currentPercent = 100
		self.progressBar.setValue(currentPercent)

	def setFileLabel(self, currentFile):
		self.fileNameLabel.setText(currentFile)

	def setFileList(self, currentFileList):
		self.getTheFiles = currentFileList
		fileArray = []
		for x in currentFileList:
			fileArray.append(x)
		fileString = "\n".join(fileArray)
		self.fileList.setText(fileString)

	def directConnect(self, isConnected):
		if isConnected[0] == "True":
			self.directConnectButton.setVisible(False)
			self.sendButton.setVisible(True)
			self.browseButton.setVisible(True)
			self.receiveButton.setVisible(True)
			self.closeConnectionButton.setVisible(True)

			cArray = isConnected[1]
			self.receiver.setProgressBar(self.progressBar)
			self.receiver.fileInfo.connect(self.chooseToReceiveData)
			self.receiver.requestInfo.connect(self.acceptBrowseRequest)
			self.receiver.replaceInfo.connect(self.replaceFile)                        
			self.receiver.currentPercent.connect(self.setProgress)
			self.receiver.setFileNameLabel(self.fileNameLabel)
			self.receiver.currentFile.connect(self.setFileLabel)
			self.receiver.fileDirectory.connect(self.createBrowseBox)
			self.receiver.setAllFilesList(self.allFiles)
			self.receiver.currentFileList.connect(self.setFileList)
			self.receiver.browseMessage.connect(self.enableBrowse)
			time.sleep(0.1)
		else:
			pass

	def enableBrowse(self, browseMessage):
		print(browseMessage)
		self.scrollArea.setEnabled(True)             

	def createBrowseBox(self, fileDirectory):
		browseBox = QGroupBox()
		sock = fileDirectory[0]
		directory = fileDirectory[1]
		formBox = QtGui.QFormLayout()                
		for x in directory:
			name = x.split("\t")[0]
			size = x.split("\t")[1]
			print(name)
			print(size)
			thisButton = QPushButton("Request File")
			thisButton.clicked.connect(lambda name=name: self.sendButtonInfo(name, sock))
			nameLabel = name + " (" + size + " bytes)"
			formBox.addRow(nameLabel, thisButton)               
		browseBox.setLayout(formBox)
		browseBox.setBackgroundRole(QPalette.Light)
		self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.scrollArea.setWidget(browseBox)
		self.scrollArea.setMaximumHeight(600)
		self.scrollArea.setMinimumHeight(500)
		self.scrollArea.setFixedWidth(browseBox.width()+17)
		self.scrollArea.setBackgroundRole(QPalette.Dark)
		self.scrollArea.setVisible(True)

	def sendButtonInfo(self, x, sock):
		try:
			info = bytes("confirm\n", 'utf-8')		
			fname = bytes("Public Files/" + x + "\n", 'utf-8')
			sock.send(info)
			sock.send(fname)
		except:
			failToSendBox = QtGui.QMessageBox()
			failToSendBox.setText("Could not send file!\n" + str(sys.exc_info()[1]))
			failToSendBox.exec_()

	def sendFileInformation(self, cArray):
		self.friendly = cArray[0]
		self.sock = cArray[1]
		self.address = cArray[2]
		global stop
		try:
			fileName = QFileDialog.getOpenFileName(self, "Open", 
			                                       "c:/python34/Public Files")
			fileName = str(fileName[0])		
			try:
				info = bytes("info\n", 'utf-8')
				fname = bytes(fileName + "\n", 'utf-8')
				size = bytes(str(os.path.getsize(fileName)) + "\n", 'utf-8')
				stop = True
				#server_sock.close()
				self.sock.send(info)
				self.sock.send(fname)
				self.sock.send(size)

			except:
				failToSendBox = QtGui.QMessageBox()
				failToSendBox.setText("Could not send file!\n" + str(sys.exc_info()[1]))
				failToSendBox.exec_()
		except:
			errorBox = QtGui.QMessageBox()
			errorBox.setText("File transfer canceled.")
			errorBox.exec_()

	def chooseToReceiveData(self, fileInfo):
		global stop
		fileName = fileInfo[0]
		friendlyFileName = ntpath.basename(fileName)
		intSize = fileInfo[1]
		size = str(intSize)
		sock = fileInfo[2]
		friendly = fileInfo[3]
		reply = QtGui.QMessageBox.question(self, "File Transfer",
		                                   friendly + " wants to send you a file:\n" 
		                                   + friendlyFileName + " (" + size + " bytes)\n" 
		                                   + "Accept?",
		                                   QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)

		if reply == QtGui.QMessageBox.Yes:
			confirm = bytes("confirm\n", 'utf-8')
			byteFileName = bytes((fileName + "\n"), 'utf-8')
			sock.send(confirm)
			sock.send(byteFileName)
		else:
			deny = bytes("deny\n", 'utf-8')
			sock.send(deny)
			self.allFiles.append(friendlyFileName + " (" + size + " bytes) - Denied\n")
			self.setFileList(self.allFiles)

	def replaceFile(self, replaceInfo):
		newFile = replaceInfo[0]
		oldFile = replaceInfo[1]
		reply = QtGui.QMessageBox.question(self, "File Transfer",
		                                   "File " + oldFile + " already exists.\nDo you wish to overwrite it?" ,
		                                   QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)

		if reply == QtGui.QMessageBox.Yes:
			os.remove(oldFile)
			move(newFile, oldFile)                        
		elif reply == QtGui.QMessageBox.No:
			pass
		else:
			os.remove(newFile)

	def acceptConnection(self, cArray):
		global truecheck
		friendly = cArray[0]
		sock = cArray[1]
		address = cArray[2]
		while not truecheck:
			#print("In while loop - " + str(truecheck))
			continue
		print("OUT OF WHILE LOOP! - " + str(truecheck))
		reply = QtGui.QMessageBox.question(self, "Direct Connect",
		                                   friendly + " wants to Direct Connect. Accept?",
		                                   QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)	
		if reply == QtGui.QMessageBox.Yes:
			accepter = bytes("accepted\n", 'utf-8')
			sock.send(accepter)
			isConnected = []
			isConnected.append("True")
			isConnected.append(cArray)
			self.directConnect(isConnected)
		else:
			denier = bytes("denied\n", 'utf-8')
			sock.send(denier)

	def acceptBrowseRequest(self, requestInfo):
		sock = requestInfo[0]
		friendly = requestInfo[1]		
		reply = QtGui.QMessageBox.question(self, "Browse Request",
		                                   friendly + " is requesting to browse your files. Accept?",
		                                   QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)	
		if reply == QtGui.QMessageBox.Yes:
			fileList = []
			out = os.listdir("Public Files")
			out = "\n".join(out)
			out = out.split("\n")
			for x in out:
				size = os.path.getsize("Public Files/" + x)
				fileList.append(x + "\t" + str(size))
			fileList = "\n".join(fileList) + "\r"
			allow = bytes("sendingfilelist\n", 'utf-8')
			out = bytes(fileList, 'utf-8')			
			sock.send(allow)
			sock.send(out)					
		else:
			denier = bytes("browsedenied\n", 'utf-8')
			sock.send(denier)		

	def fileMessage(self, message):
		fileMsgBox = QtGui.QMessageBox()
		fileMsgBox.setText(message)
		fileMsgBox.exec_()
		if "instance" in message:
			os._exit(1)


	def closeConnection(self, cArray):
		connClose = QtGui.QMessageBox()
		connClose.setText("Connection has been closed")
		connClose.exec_()
		global stop

		self.directConnectButton.setVisible(True)
		self.directConnectButton.setEnabled(True)
		self.directConnectButton.setText("Direct Connect")
		self.sendButton.setVisible(False)
		self.browseButton.setVisible(False)
		self.receiveButton.setVisible(False)
		self.closeConnectionButton.setVisible(False)	
		self.progressBar.setVisible(False)
		self.fileList.setVisible(False)

		closeConn = bytes("closeconn\n", 'utf-8')
		self.sock = cArray[1]
		self.sock.send(closeConn)
		stop = False
		truecheck = False

class Receive(QtCore.QThread):
	isConnected = QtCore.Signal(list)
	theConnection = QtCore.Signal(list)
	fileInfo = QtCore.Signal(list)
	requestInfo = QtCore.Signal(list)
	replaceInfo = QtCore.Signal(list)
	message = QtCore.Signal(str)
	currentPercent = QtCore.Signal(int)
	currentFile = QtCore.Signal(str)
	currentFileList = QtCore.Signal(list)
	fileDirectory = QtCore.Signal(list)
	browseMessage = QtCore.Signal(str)

	def setArray(self, cArray):
		self.cArray = cArray
		self.friendly = cArray[0]
		self.sock = cArray[1]
		self.address = cArray[2]

	def setAllFilesList(self, allFiles):
		self.allFiles = allFiles

	def setProgressBar(self, progressBar):
		self.progressBar = progressBar

	def setFileNameLabel(self, fileNameLabel):
		self.fileNameLabel = fileNameLabel

	def setButtons(self, directConnectButton, btButton, sendButton, browseButton, receiveButton, closeButton):
		self.directConnectButton = directConnectButton
		self.btButton = btButton
		self.sendButton = sendButton
		self.browseButton = browseButton
		self.receiveButton = receiveButton
		self.closeButton = closeButton

	def run(self):
		global stop
		self.infoArray = []
		while True:
			print("RECEIVING BYTES")
			try:
				beginArray = []
				dat = True
				while(dat):
					data = self.sock.recv(1)
					data = data.decode("utf-8")
					if(data == '\n'):
						dat = False
					elif(data == ""):
						dat = False
					else:
						beginArray.append(data)
				beginArray = str(''.join(beginArray))
				print("Received: " + beginArray)
				if beginArray == "info":
					stop = True
					#server_sock.close()
					print("Received 'info'")
					self.infoArray = []
					nameArray = []
					sizeArray = []
					dat = True
					while(dat):
						data = self.sock.recv(1)
						data = data.decode("utf-8")
						if(data == '\n'):
							dat = False
						else:
							nameArray.append(data)
					nameArray = str(''.join(nameArray))

					dat = True
					while(dat):
						data = self.sock.recv(1)
						data = data.decode("utf-8")
						if(data == '\n'):
							dat = False
						else:
							sizeArray.append(data)
					sizeArray = str(''.join(sizeArray))
					sizeArray = int(sizeArray)

					self.infoArray.append(nameArray)
					self.infoArray.append(sizeArray)
					self.infoArray.append(self.sock)
					self.infoArray.append(self.friendly)
					self.fileInfo.emit(self.infoArray)

				elif beginArray == "zerobyte":
					self.message.emit("Cannot receive a file with 0 bytes")

				elif beginArray == "data":
					self.sendButton.setEnabled(False)
					self.browseButton.setEnabled(False)
					#self.receiveButton.setEnabled(False)
					self.closeButton.setEnabled(False)
					self.fileNameLabel.setVisible(True)
					self.progressBar.setVisible(True)
					print("Received 'data'")
					total = 0

					dat = True
					stop = True
					fpath = []
					fsize = []
					while(dat):
						data = self.sock.recv(1)
						data = data.decode("utf-8")
						print(data)
						if(data == '\n'):
							dat = False
						elif(data == ""):
							dat = False
						else:
							fpath.append(data)

					fpath = str(''.join(fpath))
					dat = True
					while(dat):
						data = self.sock.recv(1)
						data = data.decode("utf-8")
						print(data)
						if(data == '\n'):
							dat = False
						elif(data == ""):
							dat = False
						else:
							fsize.append(data)
					size = str(''.join(fsize))
					dat = True
					if int(size) != 0:
						self.currentFile.emit("Receiving File: " + fpath)
						dataArray = []
						fname = "Public Files/" + ntpath.basename(fpath)
						replace = False
						if os.path.isfile(fname):
							replace = True
							x = 1
							fname = "Public Files/" + os.path.splitext(ntpath.basename(fpath))[0] + " (" + str(x) + ")" + os.path.splitext(ntpath.basename(fpath))[1]
							while os.path.isfile("Public Files/" + os.path.splitext(ntpath.basename(fpath))[0] + " (" + str(x) + ")" + os.path.splitext(ntpath.basename(fpath))[1]):
								x = x + 1
								fname = "Public Files/" + os.path.splitext(ntpath.basename(fpath))[0] + " (" + str(x) + ")" + os.path.splitext(ntpath.basename(fpath))[1]                                          

						f = open(fname, "wb")                                                  
						while dat:                                                      
							data = self.sock.recv(512000)
							f.write(data)
							val = len(data)			
							total = total + val
							percent = (total/int(size))*100
							self.currentPercent.emit(percent)
							if total == int(size):
								complete = bytes("transfercomplete\n", 'utf-8')
								self.sock.send(complete)
								f.close()
								self.currentPercent.emit(100)
								self.allFiles.append(ntpath.basename(fpath) + " (" + str(size) + " bytes) - Complete\n")
								self.currentFileList.emit(self.allFiles)
								self.progressBar.close()
								self.fileNameLabel.close()
								self.sendButton.setEnabled(True)
								self.browseButton.setEnabled(True)
								self.receiveButton.setEnabled(True)
								self.closeButton.setEnabled(True)
								message = "File Transfer Complete!"
								self.browseMessage.emit(message)
								print(fname)
								print("Public Files/" + ntpath.basename(fpath))
								if replace:
									replaceInfoArray = [fname, "Public Files/" + ntpath.basename(fpath)]
									self.replaceInfo.emit(replaceInfoArray)
								dat = False                                                                
							if val == 0:
								#self.message.emit(self.friendly + " has closed the program.")
								if self.address in device_list:
									device_list.remove(self.address)
								if self.address in checking_list:
									checking_list.remove(self.address)
								self.fileNameLabel.close()
								self.btButton.close()
								self.sendButton.close()
								self.browseButton.close()
								self.receiveButton.close()
								self.closeButton.close()
								self.directConnectButton.close()
								self.progressBar.close()
								self.allFiles = []
								self.currentFileList.emit(self.allFiles)
								stop = False
								truecheck = False
								dat = False

					else:
						self.message.emit("Cannot receive a file with 0 bytes.")

				elif beginArray == "browsedenied":
					self.message.emit("User has denied browse request")

				elif beginArray == "requestingfiles":
					requestArray = []
					requestArray.append(self.sock)
					requestArray.append(self.friendly)
					self.requestInfo.emit(requestArray)

				elif beginArray == "confirm":
					self.fileNameLabel.setVisible(True)
					self.progressBar.setVisible(True)
					print("Received 'confirm'")
					confirmedFilePath = []
					dat = True
					while(dat):
						data = self.sock.recv(1)
						data = data.decode("utf-8")
						if(data == '\n'):
							dat = False
						else:
							confirmedFilePath.append(data)
					confirmedFilePath = str(''.join(confirmedFilePath))
					self.currentFile.emit("Sending File: " + confirmedFilePath)
					print(confirmedFilePath)

					dataSend = bytes("data\n", 'utf-8')
					bytesFilePath = bytes(confirmedFilePath + "\n", 'utf-8')
					size = os.path.getsize(confirmedFilePath)
					byteSize = bytes(str(size) + "\n", 'utf-8')				

					if size == 0:
						self.message.emit("Cannot send 0 byte file")
					else:
						self.sock.send(dataSend)
						self.sock.send(bytesFilePath)
						self.sock.send(byteSize)						
						self.sendButton.setEnabled(False)
						self.browseButton.setEnabled(False)
						#self.receiveButton.setEnabled(False)
						self.closeButton.setEnabled(False)						
						f = open(confirmedFilePath, "rb")
						total = 0
						while True:
							l = f.read(512000)
							total = total + len(l)
							self.sock.send(l)
							percent = (total/size)*100
							self.currentPercent.emit(percent)                                                        
							if total == size:
								self.allFiles.append(confirmedFilePath + " (" + str(size) + " bytes) - Sent Successfully\n") 
								self.currentFileList.emit(self.allFiles)
								self.progressBar.close()
								self.fileNameLabel.close()                                                               
								break
						f.close()

				elif beginArray == "deny":
					print("Received 'deny'")
					self.message.emit("User denied the file.")

				elif beginArray == "sendingfilelist":
					fileListArray = []
					dat = True
					while(dat):
						data = self.sock.recv(1)
						data = data.decode("utf-8")
						if(data == '\r'):
							dat = False
						else:
							fileListArray.append(data)
					fileListArray = ''.join(fileListArray).split("\n")
					socketAndFileArray = []
					socketAndFileArray.append(self.sock)
					socketAndFileArray.append(fileListArray)
					self.fileDirectory.emit(socketAndFileArray)

				elif beginArray == "transfercomplete":
					self.sendButton.setEnabled(True)
					self.browseButton.setEnabled(True)
					self.receiveButton.setEnabled(True)
					self.closeButton.setEnabled(True)						

				elif beginArray == "closeconn":
					self.message.emit(self.friendly + " has closed the connection.")
					self.directConnectButton.setVisible(True)
					self.directConnectButton.setEnabled(True)
					self.directConnectButton.setText("Direct Connect")
					self.sendButton.close()
					self.browseButton.close()
					self.receiveButton.close()
					self.closeButton.close()
					#self.progressBar.setVisible(False)
					self.fileNameLabel.close()
					stop = False
					truecheck = False

				elif beginArray == "directconnect":
					self.theConnection.emit(self.cArray)
					stop = True
					#server_sock.close()
					continue
				elif beginArray == "connect":
					device_list.append(self.address)
					print("Successfully connected to " + self.address)
					continue
				elif beginArray == "disconnect":
					print("Already in list.")
					if self.address in device_list:
						device_list.remove(self.address)
					if self.address in checking_list:
						checking_list.remove(self.address)
					self.sock.close()
					break
				elif beginArray == "confirmdc":
					self.directConnectButton.setEnabled(True)

				elif beginArray == "destroy":
					self.message.emit(self.friendly + " has closed the program.")
					if self.address in device_list:
						device_list.remove(self.address)
					if self.address in checking_list:
						checking_list.remove(self.address)
					self.btButton.close()
					self.sendButton.close()
					self.browseButton.close()
					self.receiveButton.close()
					self.closeButton.close()
					self.directConnectButton.close()
					self.allFiles = []
					self.currentFileList.emit(self.allFiles)
					self.sock.close()			
					stop = False
					truecheck = False
					break

				elif beginArray == "accepted":
					self.fullConnection = []
					self.fullConnection.append("True")
					self.fullConnection.append(self.cArray)
					self.isConnected.emit(self.fullConnection)
					confirmDC = bytes("confirmdc\n", 'utf-8')
					self.sock.send(confirmDC)

				elif beginArray == "denied":
					self.message.emit("User denied the Direct Connect.")
					self.directConnectButton.setEnabled(True)
					stop = False
					truecheck = False

				elif beginArray == "":
					self.message.emit(self.friendly + " has closed the program.")
					if self.address in device_list:
						device_list.remove(self.address)
					if self.address in checking_list:
						checking_list.remove(self.address)
					self.btButton.close()
					self.sendButton.close()
					self.browseButton.close()
					self.receiveButton.close()
					self.closeButton.close()
					self.directConnectButton.close()
					self.progressBar.close()				
					self.allFiles = []
					self.currentFileList.emit(self.allFiles)
					self.sock.close()
					stop = False
					truecheck = False
					break				


				else:
					print("Error! You received: " + beginArray)
					print("In bytes, that means " + str(bytes(beginArray, 'utf-8')))

			except:
				print(sys.exc_info()[1])
				break


class DirectConnect(QtCore.QThread):

	def setDCButton(self, directConnectButton):
		self.directConnectButton = directConnectButton

	def setArray(self, cArray):
		self.friendly = cArray[0]
		self.sock = cArray[1]
		self.address = cArray[2]

	def run(self):
		global stop
		global truecheck
		try:
			stop = True
			dc = bytes("directconnect\n", 'utf-8')
			while not truecheck:
				pass
			print("IN DIRECT CONNECT WITH TRUE!")
			self.sock.send(dc)
			self.directConnectButton.setEnabled(False)
			#server_sock.close()
		except:
			self.directConnectButton.setEnabled(True)
			print("direct connect")
			print(sys.exc_info()[1])

class ScanBt(QtCore.QThread):
	communicateArray = QtCore.Signal(list)
	#show = QtCore.Signal(bool)

	def run(self):
		addresses = []
		global stop
		global truecheck
		while True:
			try:
				if not stop:			
					for address in bluetooth.discover_devices(flush_cache=False):
						addresses.append(address)
					for address in addresses:
						if address not in checking_list:
							self.addressCheck(address)	                                

				else:
					truecheck = True
					time.sleep(2)
			except:
				time.sleep(2)

	def addressCheck(self, address):
		#print("in address check with " + address)
		if address not in device_list:
			checking_list.append(address)
			if not stop:
				#print("BACK IN LOOP")
				sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
				a = Thread(self.connecting, sock, address)
				self.timer(sock, address, a)                                   
			else:
				#print("OUT OF LOOP")
				truecheck = True
				checking_list.remove(address)

	def timer(self, sock, address, a):
		time.sleep(1)
		if address in checking_list:
			checking_list.remove(address)
			try:    
				a._is_stopped = True
				a._tstate_lock = None
				a._stop()
				a._delete()
				sock.close()
				#print("Could not connect with " + address)
			except:
				print(sys.exc_info()[1])

	def connecting(self, sock, address):
		try:
			#print("Connecting to " + address)
			sock.connect((address, 17))
			friendly = bluetooth.lookup_name(address, 10)
			print("Able to connect to " + friendly)
			self.cArray = []
			self.cArray.append(friendly)
			self.cArray.append(sock)
			self.cArray.append(address)
			self.cArray.append("Sent the connection")
			self.communicateArray.emit(self.cArray)
			checking_list.remove(address)
		except:
			#print("Could not connect with " + address)
			#print(sys.exc_info()[1])
			if address in checking_list:
				checking_list.remove(address)
				sock.close()

class ListenBt(QtCore.QThread):
	message = QtCore.Signal(str)
	communicateArray = QtCore.Signal(list)

	def run(self):
		print("LISTENING BT")
		global bt
		global stop
		global currentTab
		if bt:
			sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
			try:
				sock.bind(("",17))
			except:
				self.message.emit("Cannot have multiple instances of program open")
			while True:
				try:
					sock.listen(1)
					client_sock, address = sock.accept()
					checking_list.append(address)
					if address[0] in device_list:
						print(address[0] + " is in device list. Sending 'disconnect'")
						conn = bytes("disconnect\n", 'utf-8')
						client_sock.send(conn)
						client_sock.close()
						checking_list.remove(address)
					else:
						print(address[0] + " is not in device list. Sending connect!")
						conn = bytes("connect\n", 'utf-8')
						client_sock.send(conn)
						device_list.append(address[0])
						self.cArray = []
						self.cArray.append(bluetooth.lookup_name(address[0], 10))
						self.cArray.append(client_sock)
						self.cArray.append(address[0])
						self.cArray.append("Listened and accepted")
						self.communicateArray.emit(self.cArray)
				except OSError:
					print("In listen OS ERROR")
					print(sys.exc_info())
					break
				except:
					print("In listen except")
					print(sys.exc_info()[1])
					break
			print("NOT LISTENING ANYMORE")
		else:
			self.message.emit("Bluetooth is disabled.")

class checkBtEnabled(QtCore.QThread):
	checkBt = QtCore.Signal(str)

	def run(self):
		global bt
		while(1):
			command = 'netsh interface set interface name="Bluetooth Network Connection" admin=enabled'
			process = self.launchWithoutConsole(command)
			out = process.communicate()[0]
			out = out.decode('utf-8')

			if out == "\r\n":
				self.checkBt.emit("Bluetooth Enabled")
				bt = True
			elif "Run as administrator" in out:
				self.checkBt.emit("Bluetooth Enabled")
				bt = True
			else:
				self.checkBt.emit("Bluetooth Disabled")
				bt = False
			time.sleep(1)

	def launchWithoutConsole(self, command):
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		return subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == '__main__':
	# Create the Qt Application
	app = QApplication(sys.argv)
	# Create and show the form
	form = Form()
	form.show()
	# Run the main Qt loop
	sys.exit(app.exec_())