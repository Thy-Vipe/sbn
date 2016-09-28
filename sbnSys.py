import pymel.core as pm
import maya.cmds as cmds
import sbnUI
reload(sbnUI)
from sbnUI import Ui_sbnWindow, RenameSubMenu
import constraintGenerator
reload(constraintGenerator)
from constraintGenerator import generateCG
import presetsEdit
reload(presetsEdit)
from presetsEdit import preselsUISys
import sbnObjectAttrs  # Import object classes such as itemAndRow(), UIInfos() and undoObject(), and a few utils functions.
reload(sbnObjectAttrs)
from sbnObjectAttrs import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import maya.OpenMayaUI as omu
import shiboken2
import ctypes
from maya import mel
import os

class SceneItem(object):
	def __init__(self, itemName):
		self.realName = itemName
		self._selectionOrder = -1

	def selectionOrder(self): return self._selectionOrder
	def setSelectionOrder(self, i): self._selectionOrder = i

class ListItem(QListWidgetItem):
	def __init__(self, visibleText, name, **kwargs):
		super(ListItem, self).__init__()
		self.parent = kwargs.get("parent", None)
		self.isParent = kwargs.get("isParent", False)
		self.childrens = kwargs.get("childrens", None)
		self.hierarchyDepth = kwargs.get("hierarchyDepth", 0)
		self.isSeparator = kwargs.get("isSeparator", False)
		self.isType = kwargs.get("isType", "Default")
		self.isChildren = kwargs.get("isChildren", False)
		self.group = kwargs.get("group", None)
		at = kwargs.get("at", None)
		if at is None: self.at = ['Rename','Show Childs', 'Constraint...', 'Show Attrs', 'Delete', 'Max Develop']
		else: self.at = at
		self.setText(visibleText, name)
		self._selectionOrder = -1

	def setText(self, text, realName=None):
		super(ListItem, self).setText(text)
		if realName is None: self.realName = text
		else: self.realName = realName

	def set(self, txt=None, rn=None, at=None, ip=None, c=None, ic=None, p=None, hd=None, isSep=None, isType=None, g=False):
		if txt is not None: self.setText(txt)
		if rn is not None: self.realName = rn
		if at is not None: self.at = at
		if ip is not None: self.isParent = ip
		if c is not None: self.childrens = c
		if ic is not None: self.isChildren = ic
		if p is not None: self.parent = p
		if hd is not None: self.hierarchyDepth = hd
		if isSep is not None: self.isSeparator = isSep
		if isType is not None: self.isType = isType
		if g is not False: self.group = g

	def getValues(self):
		return(self.text(), self.realName, self.at, self.isParent, self.childrens, self.isChildren, self.parent, self.hierarchyDepth, self.isSeparator, self.isType, self.group)

	def flush(self):
		self = ListItem(self.text(), self.realName)

	def redraw(self):
		if self.isSelected():
			if self.group is not None: self.group.shiftStyleSheet('highlighted')
		else:
			if self.group is not None: self.group.shiftStyleSheet('normal')

	def setSelected(self, b):
		super(ListItem, self).setSelected(b)
		self.redraw()

	def setSelectionOrder(self, i): self._selectionOrder = i
	def selectionOrder(self): return self._selectionOrder

class SbnWidget(QMainWindow, Ui_sbnWindow):
	def userResolution(): 												# This function is made to check that the user has a correct screen. 
		user32 = ctypes.windll.user32									# sbnUI also has a function like that one but that calculates the ratio (according to FHD) to make the window fit the user's screen.
		usr = [user32.GetSystemMetrics(0),user32.GetSystemMetrics(1)]	# In fact, only the results QListWidget is resized, the rest can hardly be smaller, and don't need to get bigger.
		return usr

	def mayaMainWindow(): # Query Maya's window, for parenting purposes.  
		ptr = omu.MQtUtil.mainWindow()
		return shiboken2.wrapInstance(long(ptr), QMainWindow)

	def __init__(self, parent=mayaMainWindow(), res=userResolution()):

		if pm.window('MayaWindow|sbnWindow', exists=1):			# Delete a previous possible instance of the window.
			pm.deleteUI('MayaWindow|sbnWindow')
		if pm.dockControl('MayaWindow|sbnDock', exists=1):		# Delete a previous possible instance of the window's dock.
			pm.deleteUI('MayaWindow|sbnDock')

		super(SbnWidget, self).__init__(parent) # Merge the GUI with the system functions.
		self.setupUi(self)
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.dkCtrl = pm.dockControl('sbnDock', aa=['right','left'], a='left', content=self.objectName(), w=300, label='Search by name [dk]')	

		# self.renamedOnSceneUpdater = pm.scriptJob(event=["NameChanged", self.startSearching], p=self.dkCtrl) # --> I honnestly don't think that this is really usefull. If you are checking the code, you can activate it if you want. (^u^)
		self.sceneChangedUpdater = pm.scriptJob(event=["SceneOpened", self.resetUI], p=self.dkCtrl)
		self.selectionChangedUpdater = pm.scriptJob(event=["SelectionChanged", self.keepWindowUpdated], p=self.dkCtrl)
		self.chkbs = [self.aoCHKB, self.transformsCHKB, self.jointsCHKB, self.constraintsCHKB]
		self.advWidgets = [self.liLABEL, self.itemLN, self.numberOfItemsLABEL, self.advFilteringLW]
		self.research = [self.res1LE, self.res2LE, self.ex1LE, self.ex2LE]
		self.childrens = [self.resultsLW, self.res1LE, self.res2LE, self.ex1LE, self.ex2LE, self.itemLN,\
						 self.advFilteringLW, self.aoCHKB, self.transformsCHKB, self.jointsCHKB, self.constraintsCHKB]
						 
		self.alphabet = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_1234567890') # The accepted Maya's ASCII string.
		self.currentState = 'Docked' # Will be used later on. 
		self.UIInfos = UIInfos()
		self.scndLastList = undoObject() # Allows undo
		self.firstObject = ''
		self.secondObject = ''			
		self.spacing = '    ' # Can be modified, but that distance looks pretty nice to me. Made for childs indent base while using searchForChilds() [line 693-773]
		self.separator = '----			         ----'
		self.referenceList = rebuiltList()
		self.currentSelection = []
		self.fileContent = []
		self.files = []
		self.CGIsOpen = False
		self.PreIsOpen = False
		self.itemIndex = 0
						 
		self.timer = self.startTimer(250)
		self.advWidgets[3].itemSelectionChanged.connect(self.updateUI1)
		self.advWidgets[1].editingFinished.connect(self.findPotentialItems)
		self.chkbs[0].stateChanged.connect(self.updateUI1)
		self.swWindowBTN.setEnabled(False) # An update may be done later on, to convert the ui into a non dockable version automatically.
		self.resultsLW.itemSelectionChanged.connect(self.LWManager)
		self.resultsLW.keyPressed.connect(self.keyPressedInWidget)
		self.resultsLW.mouseRelease.connect(self.LWManager)
		self.resultsLW.widgetDoubleClicked.connect(self.clearSelectedList)
		self.resultsLW.CGCalled.connect(self.openCG)
		self.resultsLW.FxPressed.connect(self.keyGotPressed)
		self.resultsLW.noAdding.connect(self.clearSelectedObjectsOnScene)
		self.resultsLW.subMenuButtonClicked.connect(self.sortCallings)
		self.resultsLW.subMenuCalled.connect(self.updateSubMenu)
		self.resultsLW.getsFocus.connect(self.LWManager)
		self.resultsLW.setIndentLenght(self.spacing)

		self.path = os.path.dirname(os.path.realpath(__file__))
		self.root = pm.workspace(q=1, rd=1).replace('/', '\\')

		self.presetsPath = '%spreselections\\'%(self.root)
		if not os.path.exists(self.presetsPath): os.makedirs(self.presetsPath)
		self.files = sorted(os.listdir(self.presetsPath))
		self.usrmsg = open(self.path+'\\sbnmsg.sbn', "r")
		self.presetsUI = None
		self.CGWindow = None
		self.renameWidget = None


		for i in range(4):
			self.research[i].editingFinished.connect(self.startSearching)
			self.research[i].textChanged.connect(self.checkSyntax)			
			self.advWidgets[i].setEnabled(False)
			if i > 0:
				self.chkbs[i].setChecked(True)
				self.chkbs[i].stateChanged.connect(self.startSearching)

		print '\n'
		mel.eval('print ("Press F1 to get informations about the hotkeys.")')
		if res[0] < 1360 and res[1] < 768:	
			pm.warning("Your screen is too small to use the docked version easily.") # An update may be done later on, to convert the ui into a non dockable widget automatically.			

	def updateSubMenu(self):
		if self.resultsLW.currentItem().isParent:
			self.resultsLW.subMenu.menuObject.content[1].setText("Hide Childs")
			self.resultsLW.subMenu.menuObject.content[5].setEnabled(False)
			
	def sortCallings(self, ID):
		"""
		The ID sent by the button will define what this button does. For instance if ID=0xA01, function called is "Rename item".
		### ID structure : 0x[cc][id1|id2]
		###				  0x<class content><buttonID>	
		>> 0xA01 Rename
		>> 0xA02 display relatives (childrens)
		>> 0xA06 display all relatives
		>> 0xA03 open up Constraint editor

		>> 0xB02 display file content
		>> 0xB03 delete file(s)
		>> 0xB04 edit file

		"""
		if ID == 0xA01: 
			self.newNameFromList()
			if len(self.resultsLW.selectedItems()) > 1:
				self.renameWidget.enablePaddingChkb.setChecked(True)
		elif ID == 0xA02: 
			self.searchForChilds()
			self.resultsLW.drawGroups()
		elif ID == 0xA06: 
			self.searchForChilds(maxLoad=True)
			self.resultsLW.drawGroups()
		elif ID == 0xA03: self.openCG(True)

		elif ID == 0xC01: self.deleteItems() 

	def clearSelectedObjectsOnScene(self):
		pm.select(cl=1)

	def clearSelectedList(self, force=False):
		self.resultsLW.clearSelection()
		self.clearSelectedObjectsOnScene()

	def keyPressedInWidget(self, event): # This allows connecting the QListWidget keyPressEvents to sbnWindow.
		if event.type() == QEvent.KeyPress and not self.CGIsOpen:
			if self.UIInfos.userDisabledKeyEventForQlist and event.text() not in self.alphabet and event.key() != (Qt.Key_Space and Qt.Key_F1 and Qt.Key_F2):
				self.keyboardControl(event)
				return True

			elif event.key() == Qt.Key_Space: # The user resets the selection using Space.
				self.clearSelectedList()
				return True

			elif not self.UIInfos.userDisabledKeyEventForQlist or (event.key() == Qt.Key_F1 or event.key() == Qt.Key_F2):
				if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:		# This is just to allow both Enter and Return, because I personally am used to hit Return instead of Enter.
					enterPressed = True												# In fact, it mixes up both events into the same one, that's all.
				else:
					enterPressed = False	
				
				if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier: # The user selects all in list using CTRL+A.
					self.selectAllInList()
					return True

				elif event.modifiers() == Qt.ShiftModifier: # The user enabled shift selection mode.
					self.UIInfos.selectShiftJumpEnabled = True
					return True

				elif event.key() == Qt.Key_R or self.UIInfos.persistentEditorOpen: # I may implement a chain renaming mode later on.| The user started to rename an object.
					return(self.newNameFromList(event, enterPressed))

				elif event.key() != (Qt.Key_A and Qt.Key_Space and  Qt.Key_C and  Qt.Key_R)\
				and event.modifiers() != (Qt.ControlModifier and Qt.ShiftModifier)\
				and not enterPressed and not self.UIInfos.persistentEditorOpen:						# Those are for the UI itself, shape mode, adv filtering, etc. 
					self.keyGotPressed(event)
					return True	

				else:
					return False

			elif self.UIInfos.userDisabledKeyEventForQlist:
				self.toNextLetter(event)
				return True	
			else:
				return False	

		elif self.CGIsOpen:
			pass # Will do stuff later
		else:		
		 	return False			
	
	def openCG(self, enabled):
		if not self.CGIsOpen:
			self.CGWindow = generateCG(self, self)
			self.CGIsOpen = enabled
		else: 
			pm.warning("Constraint editor is already open.")

	def keyboardControl(self, key): # For up arrow and down arrow. Had to redo the function because it looks like it was blocked by the event filter.
		if not self.UIInfos.persistentEditorOpen:
			if len(self.resultsLW.selectedItems()) != 0:
				item = itemAndRow()
				item.item = self.resultsLW.selectedItems()[len(self.resultsLW.selectedItems())-1]
				item.row = self.resultsLW.row(item.item)
				if key.key() == Qt.Key_Up:
					if item.row != 0:
						if key.modifiers() != Qt.AltModifier:
							self.resultsLW.clearSelection()
						self.resultsLW.item(item.row - 1).setSelected(True)
						self.resultsLW.scrollToItem(self.resultsLW.item(item.row + 1))

				if key.key() == Qt.Key_Down:
					if item.row != self.resultsLW.count() - 1:
						if key.modifiers() != Qt.AltModifier:
							self.resultsLW.clearSelection()
						self.resultsLW.item(item.row + 1).setSelected(True)
						self.resultsLW.scrollToItem(self.resultsLW.item(item.row + 1))
		else:
			self.currentStateLABEL.setText('Validate the new name, or abort\n by pressing CTRL+Return/Enter')
			pm.warning("Please validate your edition before doing anything. Press Return to validate the new name, or CTRL+Return/Enter to abort the edition.")									

	def toNextLetter(self, key): # Had to redo that one too, here, it makes sense because some keys are used for executing functions inside the list... 
		if not self.UIInfos.persistentEditorOpen:	# Go to the object that has its first letter that matches the letter hit on the keyboard, Capital or not.
			if key.text() in self.alphabet:
				items = itemAndRow()
				items.item = [self.resultsLW.item(i) for i in xrange(self.resultsLW.count())]
				items.row = [self.resultsLW.row(i) for i in items.item]
				items.uni = [i.text() for i in items.item]

				ins = []
				for i, r, hexa in zip(items.uni, items.row, items.item):
					keyPressed = [key.text(), key.text()]
					if keyPressed[0] in i[0] or keyPressed[1].upper() in i[0]:
						ins.append(r)
				self.scndLastList.possibleLenght = len(ins)-1
				if len(ins) != 0:
					if key.text() != self.scndLastList.lastKey or self.scndLastList.lastItem+1 > self.scndLastList.possibleLenght:
						if key.modifiers() != Qt.AltModifier or type(key.text()) == 'int':
							self.resultsLW.clearSelection()
						self.scndLastList.lastKey = str(key.text())
						self.scndLastList.lastItem = 0
						self.resultsLW.item(ins[self.scndLastList.lastItem]).setSelected(True)
						self.resultsLW.scrollToItem(self.resultsLW.item(ins[self.scndLastList.lastItem]))
						
					else:
						if key.modifiers() != Qt.AltModifier:
							self.resultsLW.clearSelection()
						self.resultsLW.item(ins[self.scndLastList.lastItem+1]).setSelected(True)
						self.resultsLW.scrollToItem(self.resultsLW.item(ins[self.scndLastList.lastItem+1]))
						self.scndLastList.lastKey = key.text()
						self.scndLastList.lastItem += 1
		else:
			self.currentStateLABEL.setText('Validate the new name, or abort\n by pressing CTRL+Return/Enter')
			pm.warning("Please validate your edition before doing anything. Press Return/Enter to validate the new name, or CTRL+Return/Enter to abort the edition.")				

	def newNameFromList(self, pre=None, txt=None, suf=None, padding=None, startFrom=None):
		if self.renameWidget is None:
			posRect = self.resultsLW.visualItemRect(self.resultsLW.currentItem())
			pos = QPoint(posRect.x()+self.listLayoutWidget.geometry().x()+50, posRect.y()+self.listLayoutWidget.geometry().y())
			self.renameWidget = RenameSubMenu(self, pos, self.alphabet)
			self.renameWidget.renamingAsked.connect(self.newNameFromList)
			self.renameWidget.closed.connect(self.renameWidgetKilled)
		elif (suf and txt and pre and padding and startFrom) != None:
			selection = self.resultsLW.selectedItems()
			newName = pre + txt + suf # TestName, to check if syntax is ok.
			if newName == "":
				pm.warning("Fields are empty!")
				return
			if checkStrSyntax(newName):
				pm.warning('Invalid Syntax!')
				return
			if padding.isdigit(): pad = startFrom
			else: pad = ""
			if txt == "": newName = "{prefix}{itemName}{suffix}"
			else: newName = "{prefix}{objectName}{suffix}" 
			pm.undoInfo(ock=True)
			for item in selection:
				if item.isType == "Default":
					currentRealName = item.realName
					outputName = newName.format(prefix=pre, objectName=txt, suffix=suf, itemName=currentRealName)
					if '{}' not in outputName: outputName = "%s%s"%(outputName,str(pad))
					else: outputName = outputName.format(pad)

					if outputName == "":
						pm.warning('Invalid Syntax!')
						return
					try:
						item.setText(item.text().replace(currentRealName, outputName), outputName)
						pm.rename(currentRealName, outputName)
					except RuntimeError:
						pm.warning("One of the selected objects is a protected/readOnly node, skipped.")

					if padding.isdigit(): pad += int(padding)


				else:
					if txt == "": newName = "{prefix}{itemName}{suffix}"
					else: newName = "{prefix}{objectName}{suffix}"
					currentRealName = item.realName
					outputName = newName.format(prefix=pre, objectName=txt, suffix=suf, itemName=currentRealName)
					if '{}' not in outputName: outputName = "%s%s"%(newName,str(pad))
					else: outputName = outputName.format(pad)

					if outputName == "":
						pm.warning('Invalid Syntax!')
						return
					try:
						item.setText(item.text().replace(currentRealName, outputName), outputName)
						os.rename(self.presetsPath + currentRealName + '.sbn', self.presetsPath + outputName + '.sbn')
					except RuntimeError:
						pm.warning("An error occured while renaming <{}>, skipped. Make sure your syntax is correct".format(currentRealName))

					if padding.isdigit(): pad += int(padding)

			pm.undoInfo(cck=True)
			self.renameWidget.success = True
			self.resultsLW.clearSelection()

	def renameWidgetKilled(self):
		self.renameWidget.close()
		self.renameWidget = None

	def selectAllInList(self):
		for obj in xrange(self.resultsLW.count()):
			try:
				self.resultsLW.item(obj).setSelected(True)
			except AttributeError:
				self.startSearching()
				self.selectAllInList()
				return False

		self.LWManager()
		self.UIInfos.enableUpdating = False
		self.UIInfos.resetIfEnabled = True	

	def checkSyntax(self):
		for lineEdit in self.research:
			string = lineEdit.text()
			a = False
			qt = len(string)
			for r, i in zip(string, range(qt)):
				if r not in self.alphabet and not (r == '@' and i == 0):
					if string[0] == '@':
						a = True					
					string = string.replace(r, '')
					if '@' not in string and a:
						string = '@' + string
					cp = lineEdit.cursorPosition()
					lineEdit.setText(string)
					lineEdit.setCursorPosition(cp)

	def resetUI(self):
		for obj in self.research:
			obj.setText('')
		self.resultsLW.clear()
		self.presetsPath = '%s\\preselections\\'%(self.root)
		if not os.path.exists(self.presetsPath): os.makedirs(self.presetsPath)
		self.currentStateLABEL.setText('Waiting for keywords...')
		print '\n\n\n\n\n\n\n'
		mel.eval('print "sbnWindow was reset, a scene change was detected"')
		print '\n\n\n\n\n\n\n'

	def aChildHasFocus(self):
		focused = False
		for child in self.childrens:
			if child.hasFocus(): return True

	def timerEvent(self, event):
		if not self.hasFocus() and not self.aChildHasFocus():
			if len(self.resultsLW.selectedItems()) > 800 and not self.UIInfos.userEnabledAbsoluteUpdating:
				self.UIInfos.enableUpdating = False
			else:	
				self.UIInfos.enableUpdating = True

			self.UIInfos.isFocused = False
			self.UIInfos.wasUpdatedAfterFocus = False

		else:
			self.UIInfos.isFocused = True
			if not self.UIInfos.wasUpdatedAfterFocus:
				self.keepWindowUpdated()
				self.UIInfos.wasUpdatedAfterFocus = True


		if self.CGIsOpen:
			if not self.CGWindow.isOpen:
				mel.eval('print "Constraint editor has been closed."')
				self.CGIsOpen = False

	def selectShiftJump(self):
		if self.UIInfos.selectShiftJumpEnabled:		
			if str(self.firstObject) == '':				# Now it's gonna do the whole selection at once.
				try:
					self.firstObject = self.resultsLW.selectedItems()[0] 
				except IndexError:
					self.firstObject = ''											# This function allows doing a shift selection, the user choose one point, then an other,
			if str(self.secondObject) == '':										# and then every item which is between the first and last selected object, gets selected. 
				i = len(self.resultsLW.selectedItems()) - 1 						# This function might be improved to do smart selection. 
				if i >= 1: 															#
					try:
						self.secondObject = self.resultsLW.selectedItems()[i]
					except IndexError:
						self.secondObject = ''
				if str(self.firstObject) != '' and str(self.secondObject) != '':
					rowsRange = [self.resultsLW.row(self.firstObject), self.resultsLW.row(self.secondObject)]

					if rowsRange[0] < rowsRange[1]: pass
					else: rowsRange.reverse()
					items = [self.resultsLW.row(self.resultsLW.item(i)) for i in range(rowsRange[0], rowsRange[1])]

					for row in items: self.resultsLW.item(row).setSelected(True)

			self.UIInfos.selectShiftJumpEnabled = False
			self.firstObject = ''
			self.secondObject = ''
			self.currentSelection = self.resultsLW.selectedItems()
			self.LWManager()				




	def writePresets(self, filename, objects=None, editMode=False):

		if QApplication.keyboardModifiers() == Qt.ControlModifier or editMode:
			
			if objects is None:
				objects = self.fileContent[self.files.index("%s.sbn"%filename)]
				for item in pm.ls(sl=1): objects.append(str(item))
				items = objects
			else:
				currentContent = self.fileContent[self.files.index("%s.sbn"%filename)]
				for item in objects: currentContent.append(item)
				items = currentContent  

		else:
			if objects is None: items = [str(obj) for obj in pm.ls(sl=1)]
			else: items = objects

		if len(items) > 0: 
			new = open('%s\\%s.sbn'%(self.presetsPath, filename), 'wb')
			new.write(str(items).encode('utf-8'))
			new.close()
			self.showPresets()
		else: 
			pm.warning('Empty selection!')

	def deletePresets(self):
		selectedFiles = self.resultsLW.selectedItems()

		for f in selectedFiles:
			if f.text() in self.files:
				currentFile = f.text() + '.sbn'
				os.remove('%s\\%s'%(self.presetsPath, currentFile))

		self.startSearching()

	def rebuildFile(self, objects, currentFile):
		new = []
		for item in objects:
			if pm.objExists(item):
				new.append(item)

		if len(new) > 0: self.writePresets(currentFile, objects=new)
		else: 
			pm.warning("No matching objects were found on this scene. File <{}> was not edited as it could be a name matching error.".format(currentFile))
			ans = QMessageBox.question(None, "File <{}>".format(currentFile), \
				"The content from file <{}> cannot be found on this scene.\nWould you like to delete the file?".format(currentFile),\
				QMessageBox.Yes, QMessageBox.No)
			if ans == QMessageBox.Yes:
				os.remove(self.presetsPath + currentFile + '.sbn')
				self.files.pop(self.files.index(str(currentFile)))


	def showPresets(self):
		self.files = sorted(os.listdir(self.presetsPath))
		self.resultsLW.clear()
		self.fileContent = []
		for filename in self.files:
			try:
				f = open('%s%s'%(self.presetsPath, filename), 'rb')
				fn = filename.replace('.sbn', '')

				try:
					exec('cnt = '+f.read().decode('utf-8'))
				except:
					f.close()
					os.remove(self.presetsPath + filename)
					raise RuntimeError, "File {} contains broken content, file removed.".format(filename)
					
				try:
					pm.select(cnt)
					self.clearSelectedList(force=True)
					self.fileContent.append(cnt)
					fnItem = ListItem(fn, fn, at=["Rename", "Show Content", "Delete", "Edit.."], isType="File")
					self.resultsLW.addItem(fnItem)
					f.close()

				except:
					f.close()
					pm.warning('Deprecated file found! Trying to update file: {}.'.format(filename))
					self.rebuildFile(cnt, fn)
			except IOError:
				pass

	def onPresetCalled(self):
		if not self.PreIsOpen:
			self.presetsUI = preselsUISys(self, self)
			self.presetsUI.newFile.connect(self.writePresets)
			self.presetsUI.windowState.connect(self.currentWindowState)
			self.presetsUI.del_presBtn.clicked.connect(self.deletePresets)
			self.PreIsOpen = True

	def currentWindowState(self, isOpen):
		self.PreIsOpen = isOpen

		if not isOpen:
			try:
				self.presetsUI.newFile.disconnect(self.writePresets)
				self.presetsUI.windowState.disconnect(self.currentWindowState)
				self.presetsUI.del_presBtn.clicked.disconnect(self.deletePresets)
			except RuntimeError:
				pass




	def selectObjects(self):
		selectedObjects = self.resultsLW.selectedItems()
		selection = []
		for item in selectedObjects:
			if not item.isSeparator and item.text() not in self.files:
				selection.append(item.realName)

		try:
			pm.select(selection, add=1)
		except TypeError:
			self.startSearching()
			pm.warning("An error occured, some objects may have been deleted recently. List was updated.")	

	def LWManager(self, force=False):
		pm.undoInfo(ock=1)
		self.selectionChanged = True
		if (self.UIInfos.isFocused or force) and not querySC(self.research)[4]:
			self.selectShiftJump()
			if self.resultsLW.mouseReleased: #User stopped dragging, function is executed.
				self.selectObjects()

		elif querySC(self.research)[4]:
			items = self.resultsLW.selectedItems()

			if (pm.getModifiers() & 4) and self.resultsLW.mouseReleased:
				if len(items) != 0:
					item = items[0]
					if self.spacing not in item.text():
						fc = []
						for node in self.fileContent[self.resultsLW.row(item)]:
							fc.append(self.spacing + node)

						self.resultsLW.insertItems(self.resultsLW.row(item)+1, fc)
						self.buildReferenceList(1)

			elif self.resultsLW.mouseReleased:
				for item in items:
					if self.spacing not in item.text():
						pm.select(self.fileContent[self.resultsLW.row(item)], add=1)
					else:
						self.selectObjects()

		pm.undoInfo(cck=1)

	def findPotentialItems(self):
		items = []
		if self.advWidgets[1].text() != '' and self.advWidgets[1].text() != 'shape' and self.advWidgets[1].text() != 'constraint':
			items = pm.ls(et=str(self.advWidgets[1].text()))
		elif self.advWidgets[1].text() == 'constraint':
			items = pm.ls(typ=str(self.advWidgets[1].text()))
		elif self.advWidgets[1].text() == 'shape':
			items = pm.ls(s=1)
		lenght = len(items)	
		if lenght > 1:
			self.advWidgets[2].setText('%d potential items found.'%lenght)
		else:
			self.advWidgets[2].setText('%d potential item found.'%lenght)
		if querySC(self.research)[0] and self.advWidgets[1].text() != '':
			self.startSearching()

	def nextItem(self):
		self.itemIndex += 1
		return self.itemIndex-1

	def startSearching(self):
		filteredTuple = ()
		self.referenceList = rebuiltList()
		noFilter = False
		defaultFilters = ['transform','joint', 'constraint']
		search = [self.research[i].text() for i in range(0,4)]

		if self.UIInfos.userAllowsShapes: self.UIInfos.allowShapes = True
		else: self.UIInfos.allowShapes = False	

		if querySC(self.research)[0]:
			if not querySC(self.research)[4]:
				if self.UIInfos.advancedFilteringIsEnabled and self.advWidgets[1].text() != '':
					filteredTuple = tuple([self.advWidgets[1].text()])
					if 'SHAPE' in str(self.advWidgets[1].text()).upper():
						self.UIInfos.allowShapes = True
					elif not self.UIInfos.userAllowsShapes:
						self.UIInfos.allowShapes = False	

				elif self.UIInfos.advancedFilteringIsEnabled and self.advWidgets[1].text() == '':
					pm.warning("You need to specify the filter in Advanced filtering mode. There are a few examples in the listWidget next to the text field.")

				elif self.chkbs[0].isChecked():
					noFilter = True

				else:	
					for obj, i in zip(defaultFilters, range(1,4)): # This will define the filters. 
						if self.chkbs[i].isChecked():
							filteredTuple = filteredTuple + tuple([obj])

				if not str(filteredTuple) == '()'\
				or (self.chkbs[0].isChecked() and self.advWidgets[1].text() != '' and self.UIInfos.advancedFilteringIsEnabled)\
				or (self.chkbs[0].isChecked() and not self.UIInfos.advancedFilteringIsEnabled):

					empty = querySC(self.research)[2] # Query the fields that are filled and the ones that aren't 
					for em in empty:
						em = int(em)
						if em != 1 and em != 0: search[em] = '#!@@!#'

					if noFilter:
						if self.UIInfos.allowAbsEverythin: lookIn = pm.ls()
						else: lookIn = pm.ls(ext=['animCurveTL', 'animCurveTU', 'objectMultiFilter', 'objectTypeFilter', 'objectScriptFilter'])
					else: lookIn = pm.ls(typ=filteredTuple)

					self.resultsLW.clear()

					allObjects = querySC(self.research)[3]
					# if allObjects:
					# 	for f in self.files:
					# 		self.resultsLW.addItem(f)
					nodes = ['joint','Constraint','Shape']
					for inst in lookIn:
						instance = str(inst)
						
						if self.UIInfos.ignoreCapital:
							instance = instance.upper()
							for i in range(4):
								search[i] = search[i].upper()
								if i < 3 and i > 0: #skip the joint and stop after Shape
									nodes[i] = nodes[i].upper()

						if ((search[0] in instance and search[1] in instance) or allObjects) and (search[2] not in instance and search[3] not in instance):
							if pm.nodeType(inst) == nodes[0] and not self.chkbs[2].isChecked():
								pass
							elif nodes[1] in instance and not self.chkbs[3].isChecked():
								pass
							elif nodes[1] in instance and self.chkbs[3].isChecked():
								newItem = ListItem(str(inst), str(inst))
								self.resultsLW.addItem(newItem)
							else:	
								if nodes[2] in instance and self.UIInfos.allowShapes:
									newItem = ListItem(str(inst), str(inst))
									self.resultsLW.addItem(newItem)
								elif nodes[2] not in instance:
									newItem = ListItem(str(inst), str(inst))
									self.resultsLW.addItem(newItem)
									
								if nodes[2] not in instance and self.UIInfos.allowShapes and not noFilter:
									if pm.nodeType(inst) == 'transform':
										try :
											instanceShape = ListItem(str(pm.listRelatives(inst, s=1)[0]), str(pm.listRelatives(inst, s=1)[0]))
											self.resultsLW.addItem(instanceShape)
										except IndexError:
											pass	
											
				self.updateLabel()
				self.keepWindowUpdated()

			else:
				self.showPresets()

		else:
			self.currentStateLABEL.setText('Waiting for keywords...')
			self.UIInfos.currentNumberOfObjects = 0
			self.resultsLW.clear()						

	def searchForChilds(self, selection=None, maxLoad=False):
		if selection is None:
			selection = self.resultsLW.selectedItems()
			self.resultsLW.clearSelection()

		for item in selection:
			if not item.isParent:
				childs = pm.listRelatives(item.realName, s=self.UIInfos.allowShapes, c=True)

				childData = []
				currentIndex = self.resultsLW.row(item)+1
				for child in childs:
					childItem = ListItem(self.spacing*(item.hierarchyDepth+1) + str(child), str(child), isChildren=True, parent=item, hierarchyDepth=item.hierarchyDepth+1)	
					self.resultsLW.insertItem(currentIndex, childItem)
					childData.append(self.resultsLW.item(currentIndex))
					currentIndex += 1

				if len(childs) > 0: 
					item.set(c=childData, ip=True)

			else:
				childs = item.childrens
				for child in childs:
					if child.isParent: self.searchForChilds(selection=[child])
					self.resultsLW.takeItem(self.resultsLW.row(child))
				
				item.group.close()

				item.set(c=[], ip=False, g=None)

			if maxLoad: self.searchForChilds(selection=item.childrens, maxLoad=True)

		self.updateLabel()



	def updateLabel(self):
		total = self.resultsLW.count()
		self.UIInfos.currentNumberOfObjects = total
		if total > 1:
			self.currentStateLABEL.setText('%d objects were found.'%total)
		elif total == 1:
			self.currentStateLABEL.setText('%d object was found.'%total)
		elif total == 0:
			self.UIInfos.currentNumberOfObjects = 0
			self.currentStateLABEL.setText('Nothing matches this.')
			pm.warning("Nothing matches your research, try to modify the filters or the keywords.")	

			self.UIInfos.isFocused = False
			self.UIInfos.enableUpdating = True
			if len(pm.ls(sl=1)) > 0:
			 	self.keepWindowUpdated()
			self.UIInfos.isFocused = True
			self.scndLastList = undoObject()


	def deleteItems(self):
		items = self.resultsLW.selectedItems()
		self.resultsLW.clearSelection()
		items.reverse()
		redrawUi = False
		parents = []
		itemsToRemove = []
		pm.undoInfo(ock=True)
		for item in items:
			skip = False
			if 'Shape' in item.realName or 'shape' in item.realName: skip = True #Causes crash for no reason if shapes aint excluded.

			if not skip:
				try:
					pm.delete(item.realName)
				except:
					pm.warning("Failed to delete item: '%s', skipped."%item.realName)
					skip = True

			if not skip:
				if item.isChildren: 
					if not redrawUi: redrawUi = True
					parents.append(item.parent)
				elif item.isParent:
					self.searchForChilds(selection=[item]) #Clear childrens, since we removed the parent.
					self.resultsLW.drawGroups()
					itemsToRemove.append(self.resultsLW.row(item))
				else:
					itemsToRemove.append(self.resultsLW.row(item))

		itemsToRemove.sort()
		itemsToRemove.reverse() # To avoid index issues, since this stupid list widget takes indexes for item removal.
		for i in itemsToRemove:
			self.resultsLW.takeItem(i)

		if redrawUi:
			for p in parents:
				self.searchForChilds(selection=[p]) #Clear childrens
				self.searchForChilds(selection=[p]) #Reload childrens
				self.resultsLW.drawGroups()

		pm.undoInfo(cck=True)

	def keepWindowUpdated(self): 
		if (self.UIInfos.enableUpdating and self.UIInfos.userEnabledUpdating and not self.hasFocus() and not self.aChildHasFocus()) and self.resultsLW.subMenu is None:						   
			objs = [str(obj) for obj in pm.ls(sl=1)]
			if len(objs) == 0:
				self.resultsLW.clearSelection()

			else:
				listContent = [self.resultsLW.item(i) for i in range(self.resultsLW.count())]
				for obj in listContent:
					if obj.realName in objs:
						obj.setSelected(True)
						self.resultsLW.scrollToItem(obj)
					else:
						try:
							obj.setSelected(False)
						except ValueError:
							pass	

	def keyPressEvent(self, event):
		"""
		Send keyEvents to a general function that is called by the window and its childs. (function is right after this one)
		"""
		self.keyGotPressed(event)

	def keyGotPressed(self, pressedKey):
		"""
		Yep. This function DOES look bad, but eh, there is not twelve thousands solutions for that kind of stuff. 
		It's no more than a keyEvents function that does cool stuff when something matches. 
		"""

		if pressedKey.key() == Qt.Key_P:
			self.onPresetCalled()

		if pressedKey.key() == Qt.Key_F and pressedKey.modifiers() == Qt.ControlModifier:
			self.enableAdvancedFiltering()
			if self.advWidgets[1].text() != '':
				self.startSearching()

		if pressedKey.key() == Qt.Key_M and not self.UIInfos.ignoreCapital:
			self.UIInfos.ignoreCapital = True
			self.startSearching()
			print '\n'
			mel.eval('print ("Upper and Lower cases are ignored, any object that contains the given infos will be listed.")')
		elif pressedKey.key() == Qt.Key_M and self.UIInfos.ignoreCapital:
			self.UIInfos.ignoreCapital = False
			self.startSearching()
			print '\n'
			mel.eval('print ("Upper and Lower cases took in account, object must contains the exact given infos.")')	
		
		if pressedKey.key() == Qt.Key_S and not self.UIInfos.userAllowsShapes:
			self.UIInfos.userAllowsShapes = True
			self.startSearching()
			print '\n'
			mel.eval('(print "Shapes are now allowed.");')
		elif pressedKey.key() == Qt.Key_S and self.UIInfos.userAllowsShapes:
			self.UIInfos.userAllowsShapes = False
			self.startSearching()
			print '\n'
			mel.eval('print ("Shapes are now not allowed.");')

		if pressedKey.key() == Qt.Key_Z and not self.UIInfos.allowAbsEverythin:
			self.UIInfos.allowAbsEverythin = True
			self.startSearching()
			print '\n'
			mel.eval('print ("Everything is now allowed");')
		elif pressedKey.key() == Qt.Key_Z and self.UIInfos.allowAbsEverythin:
			self.UIInfos.allowAbsEverythin = False
			self.startSearching()	
			print '\n'
			mel.eval('print ("systemNodes are now disabled");')

		if pressedKey.key() == Qt.Key_U and not self.UIInfos.userEnabledUpdating and pressedKey.modifiers() != Qt.ControlModifier:
			self.UIInfos.userEnabledUpdating = True
			print '\n'
			mel.eval('print ("The window will now update according to what is selected via the viewport.");')
		elif pressedKey.key() == Qt.Key_U and self.UIInfos.userEnabledUpdating and pressedKey.modifiers() != Qt.ControlModifier:
			self.UIInfos.userEnabledUpdating = False
			print '\n'
			mel.eval('print ("The window will not update anymore according to what is selected via the viewport.");')

		if pressedKey.key() == Qt.Key_U and self.UIInfos.userEnabledAbsoluteUpdating and pressedKey.modifiers() == Qt.ControlModifier:
			self.UIInfos.userEnabledAbsoluteUpdating = False
			print '\n'
			mel.eval('print ("The window will not update for a huge List, excepted when it will get focus.")')
		elif pressedKey.key() == Qt.Key_U and not self.UIInfos.userEnabledAbsoluteUpdating and pressedKey.modifiers() == Qt.ControlModifier:
			self.UIInfos.userEnabledAbsoluteUpdating = True	
			print '\n'
			mel.eval('print ("The window will now update, even for a huge List. WARNING: Can cause performance issues.")')	

		if pressedKey.key() == Qt.Key_F2 and not self.UIInfos.userDisabledKeyEventForQlist:
			self.UIInfos.userDisabledKeyEventForQlist = True
			self.scndLastList.lastItem = 0
			self.scndLastList.lastKey = ''
			print '\n'
			mel.eval('print ("Results list widget keyEvents tracking is now activated. That also means that you cannot use the implemented commands using R, CTRL+A, etc...But can find items by hitting any letter on the keyboard.")')
		elif pressedKey.key() == Qt.Key_F2 and self.UIInfos.userDisabledKeyEventForQlist:
			self.UIInfos.userDisabledKeyEventForQlist = False
			print '\n'
			mel.eval('print ("Results list widget keyEvents tracking is now deactivated. That also means that you can use the implemented commands using R, CTRL+A, etc...But cannot find items by hitting any letter on the keyboard.")')	

		if pressedKey.key() == Qt.Key_F1:
			print '\n\n\n'
			for line in self.usrmsg.readlines():
				line = line.replace('\r\n', '')
				print line

			mel.eval('print ("Check out the script editor for the hotkeys.");')	

	def enableAdvancedFiltering(self):
		"""
		This function updates the gui to its second mode.
		"""
		if self.UIInfos.advancedFilteringIsEnabled == False:
			self.UIInfos.advancedFilteringIsEnabled = True
			for i in range(0,4):
				self.advWidgets[i].setEnabled(True)
				self.chkbs[i].setEnabled(False)
		else:
			self.UIInfos.advancedFilteringIsEnabled = False
			self.advWidgets[3].clearSelection()
			for i in range(0,4):
				self.advWidgets[i].setEnabled(False)
				self.chkbs[i].setEnabled(True)		

	def closeEvent(self, event):
		pm.deleteUI(self.dkCtrl)
		self.usrmsg.close()
		print "SBN has been closed."

		if self.CGIsOpen: self.CGWindow.close()
		event.accept()
		self = None	

	def updateUI1(self):
		if self.chkbs[0].isChecked():
			for i in range(1,4):
				self.chkbs[i].setEnabled(False)
		else:
			for i in range(1,4):
				self.chkbs[i].setEnabled(True)

		if len(self.advWidgets[3].selectedItems()) != 0:
			self.advWidgets[1].setText(str(self.advWidgets[3].selectedItems()[0].text()))
			self.findPotentialItems()

		self.startSearching()		
