from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import CG_sbnUI
reload(CG_sbnUI)
from CG_sbnUI import Ui_CG
from maya import mel
import sbnSys
import pymel.core as pm


class generateCG(QMainWindow, Ui_CG, object):
	def __init__(self, parent, mainWindow):

		self.sbnUI = mainWindow # "Connect" sbnUI to the generated widget.

		super(generateCG, self).__init__(parent)
		self.setupUi(self)
		self.show()
		self.isOpen = True
		self.vecButtons = [self.buAimX, self.buAimY, self.buAimZ,\
							self.buUpX, self.buUpY, self.buUpZ,\
							self.buWUX, self.buWUY, self.buWUZ]
		self.chkbs = [[self.skipTchkbX, self.skipTchkbY, self.skipTchkbZ],\
						[self.skipRchkbX, self.skipRchkbY, self.skipRchkbZ]]
		self.vecVals = [self.vecAimX, self.vecAimY, self.vecAimZ,\
							self.vecUpX, self.vecUpY, self.vecUpZ,\
							self.vecWUX, self.vecWUY, self.vecWUZ]
		for chkbT, chkbR, name in zip(self.chkbs[0], self.chkbs[1], ["x","y","z"]):
			chkbT.checkBoxName = name
			chkbR.checkBoxName = name

		for button, name in zip(self.vecButtons, range(0,9)):
			button.emittedName = name
			button.buttonName.connect(self.setValue)
																		# VecVals :
		for i in [0, 4, 7]: self.vecVals[i].setValue(1.00)				#  Aim |0|1|2|
																		#  Up  |3|4|5|
		self.wutCB.setCurrentIndex(3)									#  WUp |6|7|8|
		self.aToA.setChecked(True)
		self.buApply.clicked.connect(self.createConstraint)
		self.constraintCB.currentIndexChanged.connect(self.updateGui)	
		self.wutCB.currentIndexChanged.connect(self.updateGui)
		self.buQueryVec.clicked.connect(self.queryVector)
		self.MCchkb.clicked.connect(self.updateGui)
		self.aToA.toggled.connect(self.updateGui)
		self.AToO.toggled.connect(self.updateGui)
		self.buClose.clicked.connect(self.close)
		self.constraintType = None
		self.worldUpType = None
		self.__opacity = 1.0
		# self.loadMode = 0


		self.waitForApply = QWaitCondition()
		self.mutex = QMutex()
		self.updateGui()

	# def keyPressEvent(self, event):
	# 	if event.key() == Qt.Key_L and self.loadMode == 1:
	# 		print "Loading from Search by Name."
	# 		self.loadMode = 0
	# 	elif event.key() == Qt.Key_L and self.loadMode == 0:
	# 		print "Loading from scene."
	# 		self.loadMode = 1
	# 	else:
	# 		pass
	def wheelEvent(self, event):
		if event.delta() < 0:
			if self.__opacity > 0.15:
				self.__opacity -= 0.05

		elif event.delta() > 0:
			if self.__opacity <= 1.0:
				self.__opacity += 0.05

		self.setWindowOpacity(self.__opacity)

	def closeEvent(self, event):
		self.isOpen = False
		event.accept()

	def resetValue(self, rangeX):
		for btn in rangeX: self.vecVals[btn.emittedName].setValue(0.00)		

	def setValue(self, btnName):
		if btnName < 3: self.resetValue(self.vecButtons[0:3])
		elif btnName < 6: self.resetValue(self.vecButtons[3:6])
		else: self.resetValue(self.vecButtons[6:9])

		self.vecVals[btnName].setValue(1.00)

	def querySkippedAxises(self):
		"""
		Query the axises that will be skipped during the execution of the creation of the constraint. 
		Each checkboxes have a name that is emitted when their state changes. The signal isn't used here, but
		we query the name of the checkbox. The name can either be [x], [y] or [z], depending of the axis they're 
		supposed to define. 
		"""
		sr, st = [], []
		for chkbT, chkbR in zip(self.chkbs[0], self.chkbs[1]):
			if chkbR.isChecked(): sr.append(chkbR.checkBoxName)
			if chkbT.isChecked(): st.append(chkbT.checkBoxName)

		return st, sr

	def updateGui(self):
		"""
		This function updates the user interface when some events occur. Everything is pretty straight-forward,
		no need to explain in depth.
		"""
		self.constraintType = self.constraintCB.currentText()
		self.worldUpType = self.wutCB.currentText()

		if self.MCchkb.isChecked():
			self.aToA.setEnabled(True)
			self.AToO.setEnabled(True)
		else:
			self.aToA.setEnabled(False)
			self.AToO.setEnabled(False)				

		if self.constraintType == 'pointConstraint':
			for box in self.chkbs[1]: box.setEnabled(False)
			for box in self.chkbs[0]: box.setEnabled(True)
			for value in self.vecVals: value.setEnabled(False)
			for button in self.vecButtons: button.setEnabled(False)
			self.translateL.setText('Translate:')
			self.lineEdit.setEnabled(False)
			self.buQueryVec.setEnabled(False)
			self.wutCB.setEnabled(False)

		elif self.constraintType == 'orientConstraint':
			for box in self.chkbs[1]: box.setEnabled(True)
			for box in self.chkbs[0]: box.setEnabled(False)
			for value in self.vecVals: value.setEnabled(False)
			for button in self.vecButtons: button.setEnabled(False)
			self.translateL.setText('Translate:')
			self.lineEdit.setEnabled(False)
			self.buQueryVec.setEnabled(False)
			self.wutCB.setEnabled(False)

		elif self.constraintType == 'scaleConstraint':
			for box in self.chkbs[1]: box.setEnabled(False)
			for box in self.chkbs[0]: box.setEnabled(True)
			for value in self.vecVals: value.setEnabled(False)
			for button in self.vecButtons: button.setEnabled(False)
			self.translateL.setText('Scale:')
			self.lineEdit.setEnabled(False)
			self.buQueryVec.setEnabled(False)
			self.wutCB.setEnabled(False)

		elif self.constraintType == 'aimConstraint':
			for box in self.chkbs[1]: box.setEnabled(False)
			for box in self.chkbs[0]: box.setEnabled(False)
			if self.wutCB.currentText() == 'Object Rotation' or self.wutCB.currentText() == 'Vector': x = 9
			else: x = 6
			for button in self.vecButtons[0:x]: button.setEnabled(True)
			for value in self.vecVals[0:x]: value.setEnabled(True)
			for value in self.vecVals[x:]: value.setEnabled(False)
			for button in self.vecButtons[x:]: button.setEnabled(False)
			self.translateL.setText('Translate:')
			if (self.wutCB.currentText() == 'Object' or self.wutCB.currentText() == 'Object Rotation') and self.mode():
				self.buQueryVec.setEnabled(True)
				self.lineEdit.setEnabled(True)
			else:
				self.buQueryVec.setEnabled(False)
				self.lineEdit.setEnabled(False)				
			self.wutCB.setEnabled(True)	

		elif self.constraintType == 'parentConstraint':
			for box in self.chkbs[1]: box.setEnabled(True)
			for box in self.chkbs[0]: box.setEnabled(True)
			for value in self.vecVals: value.setEnabled(False)
			for button in self.vecButtons: button.setEnabled(False)
			self.translateL.setText('Translate:')
			self.lineEdit.setEnabled(False)
			self.buQueryVec.setEnabled(False)
			self.wutCB.setEnabled(False)

	def mode(self):
		if self.MCchkb.isChecked() and self.aToA.isChecked(): return False
		elif (self.MCchkb.isChecked() and self.AToO.isChecked()) or not self.MCchkb.isChecked(): return True

	def queryVector(self):
		"""
		Query worldUpObject. Called when clicking the button next to the worldUpObject lineEdit. Ignored
		if multimode enabled.
		"""
		mod = pm.getModifiers()
		if (mod & 4): # if CTRL is hit.
			item = self.sbnUI.resultsLW.selectedItems()[0] if len(self.sbnUI.resultsLW.selectedItems()) >= 1 else None
			if item:
				self.lineEdit.setText(item.realName)
		else:
			sel = pm.ls(sl=1)
			
			if len(sel) != 0: self.lineEdit.setText(str(sel[0]))
			else: pm.warning("You need to select an object to query.")

	def getDictionnary(self):

		"""
		This function builds a dictionnary corresponding to the requested constraint and used mode..   
		"""
		weight = self.weightSB.value()
		aimVector = tuple([vec.value() for vec in self.vecVals[0:3]])
		upVector = tuple([vec.value() for vec in self.vecVals[3:6]])
		worldUpVector = tuple([vec.value() for vec in self.vecVals[6:9]])
		if self.MOchkb.isChecked() : maintainOffset = 1
		else: maintainOffset = 0
		skippedAxises = self.querySkippedAxises()
		print skippedAxises
		lenT = len(skippedAxises[0])
		lenR = len(skippedAxises[1])

		if self.constraintType == 'aimConstraint':
			constraint = pm.aimConstraint
			if self.worldUpType == 'Object':
				dic = {'aim':aimVector, 'mo':maintainOffset, 'u':upVector, 'wut':self.worldUpType, 'w':weight}

			elif self.worldUpType == 'Object Rotation':
				dic = {'aim':aimVector, 'mo':maintainOffset, 'u':upVector, 'wut':self.worldUpType, 'wu':worldUpVector, 'w':weight}

			elif self.worldUpType == 'Vector':
				dic = {'aim':aimVector, 'mo':maintainOffset, 'u':upVector, 'wut':self.worldUpType, 'wu':worldUpVector, 'w':weight}

			elif self.worldUpType == 'Scene':
				dic = {'aim':aimVector, 'mo':maintainOffset, 'u':upVector, 'wut':self.worldUpType, 'w':weight}

		elif self.constraintType == 'orientConstraint':
			constraint = pm.orientConstraint
			if lenR == 0:
				dic = {'mo':maintainOffset, 'w':weight}
			else:
				dic = {'mo':maintainOffset, 'w':weight, 'skip':skippedAxises[1]}

		elif self.constraintType == 'pointConstraint':
			constraint = pm.pointConstraint
			if lenT == 0:
				dic = {'mo':maintainOffset, 'w':weight}
			else:
				dic = {'mo':maintainOffset, 'w':weight, 'skip':skippedAxises[0]}			

		elif self.constraintType == 'parentConstraint':
			constraint = pm.parentConstraint
			if lenT == 0 and lenR == 0:
				dic = {'mo':maintainOffset, 'w':weight}
			elif lenT > 0 and lenR == 0:
				dic = {'mo':maintainOffset, 'w':weight, 'skipTranslate':skippedAxises[0]}
			elif lenT == 0 and lenR > 0:
				dic = {'mo':maintainOffset, 'w':weight, 'skipRotate':skippedAxises[1]}	
			elif lenT > 0 and lenR > 0:
				dic = {'mo':maintainOffset, 'w':weight, 'skipTranslate':skippedAxises[0], 'skipRotate':skippedAxises[1]}	

		elif self.constraintType == 'scaleConstraint':
			constraint = pm.scaleConstraint
			if lenT == 0:
				dic = {'mo':maintainOffset, 'w':weight}
			else:
				dic = {'mo':maintainOffset, 'w':weight, 'skip':skippedAxises[0]}

		elif self.constraintType == 'poleVectorConstraint':
			constraint = pm.poleVectorConstraint
			dic = {'w':weight}

		return constraint, dic

	def createConstraint(self):
		"""
		Create constraint on chosen objects.
		"""
		objects = pm.ls(sl=1)
		lenObjs = len(objects)
		command = self.getDictionnary()
		pm.undoInfo(ock=1)
		if self.MCchkb.isChecked():
			if self.aToA.isChecked():
				if self.constraintType == 'aimConstraint' and self.wutCB.currentText() in ('Object', 'Object Rotation'): requiredArgs = 3
				else: requiredArgs = 2

				if lenObjs% 3 == 0 and requiredArgs == 3 and lenObjs != 0:
					for parent, slave, vec in splitList(objects, 3):
						command[0](parent, slave, wuo=vec, **command[1])

				elif lenObjs% 2 == 0 and requiredArgs == 2 and lenObjs != 0:
					for parent, slave in splitList(objects, 2):
						command[0](parent, slave, **command[1])

				else:
					if self.constraintType == 'aimConstraint': txt = ' with "' + self.wutCB.currentText() + '"'
					else: txt = ''
					pm.warning('The mode "%s"%s requires exactly %d objects for each loop. Selection is invalid.'%(self.constraintType, txt, requiredArgs))

			elif self.AToO.isChecked():
				parent = objects[0]
				slaves = objects[1:]
				worldUpObj = self.lineEdit.text()

				if self.constraintType == 'aimConstraint' and self.wutCB.currentText() in ('Object', 'Object Rotation'): 
					for slave in slaves:
						command[0](parent, slave, wuo=worldUpObj, **command[1])

				else:
					for slave in slaves:
						command[0](parent, slave, **command[1])

		else:
			if lenObjs == 3 and self.wutCB.currentText() in ('Object', 'Object Rotation'):
				parent = objects[0]
				slave = objects[1]
				worldUpObj = objects[2]
				command[0](parent, slave, wuo=worldUpObj, **command[1])

			elif lenObjs == 2:
				parent = objects[0]
				slave = objects[1]
				command[0](parent, slave, **command[1])

			else:
				pm.warning("Selection is invalid compared to your settings.")

	pm.undoInfo(cck=1)


def splitList(listObj, n):
	output = []
	while len(listObj) != 0:
		content = []
		for i in range(n):
			content.append(listObj.pop(0))
		output.append(tuple(content))

	return output