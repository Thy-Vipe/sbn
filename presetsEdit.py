from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import Presels_sbnUI
reload(Presels_sbnUI)
from Presels_sbnUI import Ui_preselsGUI
import pymel.core as pm

class preselsUISys(QMainWindow, Ui_preselsGUI, object):
	newFile = Signal(str)
	windowState = Signal(bool)
	def __init__(self, parent, mainWindow):

		self.sbnUI = mainWindow

		super(preselsUISys, self).__init__(parent)
		self.setupUi(self)
		self.show()
		self.isOpen = True
		self.timer = self.startTimer(250)
		self.cancelBtn.clicked.connect(self.closeWindow)
		self.ce_presBtn.clicked.connect(self.createNewFile)
		self.name_LE.textChanged.connect(self.checkSyntax)
		self.installEventFilter(self)
		self.move(QPoint(354, 187))

	def eventFilter(self, obj, event):
		if event.type() == QEvent.WindowActivate: 
			self.setWindowOpacity(1)
			return True
		elif event.type() == QEvent.WindowDeactivate: 
			self.setWindowOpacity(0.45)
			return True

		return False

	def checkSyntax(self):
		for s in self.name_LE.text():
			if s not in self.sbnUI.alphabet:
				self.name_LE.setText(self.name_LE.text().replace(s, ''))

	def closeWindow(self):
		self.windowState.emit(False)
		self.close()

	def closeEvent(self, event):
		event.accept()	

	def createNewFile(self):
		if self.name_LE.text() != '': self.newFile.emit(self.name_LE.text())
		else: pm.warning("Empty name!")


