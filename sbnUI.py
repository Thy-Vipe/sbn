import ctypes
from PySide2 import QtCore, QtWidgets
import os

# Adresses for each buttons
BUTTON_ENUM = {
    "Rename":0xA01,
    "Show Childs":0xA02,
    "Constraint...":0xA03,
    "Show Attrs":0xA04,
    "Max Develop":0xA06,
    "Show Content":0xB02,
    "Delete":0xB03,
    "Edit..":0xB04,
    "Delete":0xC01
}

BUTTON_TOOLTIP = {
    "Rename":"Rename one or several object(s) at once.\nOpens up a renaming interface. \n",
    "Show Childs":"Display/hide item's childs at depth 1. \n",
    "Constraint...":"Allows creating quick constraints. <WIP> \n",
    "Show Attrs":"Display/hide item's transform attributes.\n",
    "Max Develop":"Will list all children relatives to max. \n",
    "Show Content":"Displays file's content. \n",
    "Delete":"Delete file. \n",
    "Edit..":"Opens File editor. \n",
    "Delete":"Deletes selected item(s) from scene. \n"
}

class RenameSubMenu(QtWidgets.QFrame):
    """
    Popup allowing the user to rename decently their selected items. Subclass of a QFrame object. 
    """

    renamingAsked = QtCore.Signal(str, str, str, str, int) #Signal sent by the popup to the ListWidget. Contains <prefix,name,suffix,padding value str,allow padding bool>
    closed = QtCore.Signal()
    def __init__(self, parent, pos, alphabet):
        super(RenameSubMenu, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setLineWidth(2)
        with open(os.path.abspath(os.path.dirname(__file__)) + '\\renameWidget.qss', 'r') as rwStyleSheet:
            self.setStyleSheet(rwStyleSheet.read())
            rwStyleSheet.close()

        self.setGeometry(QtCore.QRect(pos.x(), pos.y(), 210, 80))

        self.enablePaddingChkb = QtWidgets.QCheckBox(self)
        self.enablePaddingChkb.setGeometry(QtCore.QRect(10, 52, 100, 15))
        self.enablePaddingChkb.setText("Enable Padding")
        newNameLE = QtWidgets.QLineEdit(self)
        newNameLE.setGeometry(QtCore.QRect(10, 10, 115, 20))
        newNameLE.setToolTip(QtWidgets.QApplication.translate("contentWidget", "<html><head/><body><p>Add \'{}\' in any of the fields for number position.</p></body></html>",\
         None, QtWidgets.QApplication.UnicodeUTF8))
        newNameLE.setPlaceholderText("New name...")
        self.renameBtn = QtWidgets.QPushButton(self)
        self.renameBtn.setGeometry(QtCore.QRect(112, 54, 51, 23))
        self.renameBtn.setObjectName("renameBtn")
        self.renameBtn.setText("Rename")
        self.renameBtn.setToolTip(QtWidgets.QApplication.translate("Dialog", "<html><head/><body><p>You can also directly press Enter/Return.</p></body></html>", None, QtWidgets.QApplication.UnicodeUTF8))
        self.closeBtn = QtWidgets.QPushButton(self)
        self.closeBtn.setGeometry(QtCore.QRect(167, 54, 41, 23))
        self.closeBtn.setObjectName("closeBtn")
        self.closeBtn.setText("Close")
        self.paddingSB = QtWidgets.QSpinBox(self)
        self.paddingSB.setGeometry(QtCore.QRect(187, 10, 19, 22))
        self.paddingSB.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.paddingSB.setObjectName("paddingSB")
        self.paddingSB.setValue(1)
        self.paddingLabel = QtWidgets.QLabel(self)
        self.paddingLabel.setGeometry(QtCore.QRect(140, 10, 46, 20))
        self.paddingLabel.setObjectName("paddingLabel")
        self.paddingLabel.setText("Padding: ")
        preLE = QtWidgets.QLineEdit(self)
        preLE.setGeometry(QtCore.QRect(10, 31, 55, 20))
        preLE.setPlaceholderText("Prefix")
        sufLE = QtWidgets.QLineEdit(self)
        sufLE.setGeometry(QtCore.QRect(69, 31, 55, 20))
        sufLE.setPlaceholderText("Suffix")
        self.startSB = QtWidgets.QSpinBox(self)
        self.startSB.setGeometry(QtCore.QRect(170, 33, 36, 17))
        self.startSB.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.startSB.setMaximum(999999999)
        self.startSB.setValue(1)
        self.startSB.setObjectName("startSB")
        self.startLabel = QtWidgets.QLabel(self)
        self.startLabel.setGeometry(QtCore.QRect(142, 33, 29, 17))
        self.startLabel.setObjectName("startLB")
        self.startLabel.setText("Start:")

        self.renameBtn.clicked.connect(self.renameObjectMessage)
        self.closeBtn.clicked.connect(self.closedMessage)

        self.textEditors = [preLE, newNameLE, sufLE]
        self.alphabet = alphabet
        self.success = False

        for lineEdit, name in zip(self.textEditors, ['preLE', 'newNameLE', 'sufLE']):
            lineEdit.setObjectName(name)
            lineEdit.returnPressed.connect(self.renameObjectMessage)
            lineEdit.textChanged.connect(self.renameSyntaxCheck)

        self.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.renameObjectMessage()

    def mouseDoubleClickEvent(self, event):
        self.closedMessage()

    def renameObjectMessage(self):
        if self.enablePaddingChkb.isChecked(): padvalue = str(self.paddingSB.value())
        else: padvalue = ''
        self.renamingAsked.emit(self.textEditors[0].text(), self.textEditors[1].text(), self.textEditors[2].text(), padvalue, self.startSB.value())
        if self.success: self.closedMessage()

    def closedMessage(self):
        self.closed.emit()

    def renameSyntaxCheck(self):
        for lineEdit in self.textEditors:
            content = lineEdit.text()
            cp = lineEdit.cursorPosition()
            if lineEdit.objectName() == 'preLE':
                try:
                    start = content[0]
                    if start.isdigit():
                        pm.warning("Prefix can not start by a number.")
                        content = content.replace(start, "")
                        lineEdit.setText(newText)
                except:
                    pass
            for letter in content:
                if letter not in self.alphabet and letter not in ['{', '}']:
                    content = content.replace(letter, "")
            lineEdit.setText(content)
            lineEdit.setCursorPosition(cp)

class SubMenuBtn(QtWidgets.QPushButton):
    Clicked = QtCore.Signal(int)
    Released = QtCore.Signal(int)
    def __init__(self, parent, buttonName, styleSheet=None):
        super(SubMenuBtn, self).__init__(parent)

        if styleSheet is not None: self.setStyleSheet(styleSheet)
        self.setText(buttonName)
        btnIndex = BUTTON_ENUM[buttonName]
        self.setObjectName("QPButton#{}".format(btnIndex))
        self.setToolTip(BUTTON_TOOLTIP[buttonName])
        self.btnID = btnIndex

    def mousePressEvent(self, event):
        super(SubMenuBtn, self).mousePressEvent(event)
        self.Clicked.emit(self.btnID)

    def mouseReleaseEvent(self, event):
        super(SubMenuBtn, self).mouseReleaseEvent(event)
        self.Released.emit(self.btnID)

class SubMenuContent:
    def __init__(self, parent, buttonTexts):
        self.widget = QtWidgets.QWidget(parent)
        self.widget.setGeometry(parent.lineWidth(), parent.lineWidth(), parent.width()-parent.lineWidth(), parent.height()-parent.lineWidth())
        self.widgetLayout = QtWidgets.QVBoxLayout(self.widget)
        self.widgetLayout.setSpacing(1)
        self.widgetLayout.setContentsMargins(2, 4, 4, 4)
        self.content = []
        with open(os.path.abspath(os.path.dirname(__file__)) + '\\subMenuButtons.qss', 'r') as btnStyleSheet:
            styleSheet = btnStyleSheet.read()
            btnStyleSheet.close()

        for optionBtn in buttonTexts:
            btn = SubMenuBtn(self.widget, optionBtn, styleSheet)
            self.content.append(btn)
            self.widgetLayout.addWidget(self.content[len(self.content)-1])

class ListSubMenu(QtWidgets.QFrame):
    def __init__(self, parent, pos, buttonTexts, hitboxOffset=20):
        super(ListSubMenu, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setLineWidth(2)
        self.setStyleSheet("background-color: #444; border: 2px solid #7297A3; border-radius: 4px")

        if parent.rect().contains(pos.x()+85, pos.y()+135) \
        and parent.rect().contains(pos.x(), pos.y()): 
            self.setGeometry(QtCore.QRect(pos.x(), pos.y(), 85, 135))
            deltaX, deltaY = 0, 0
        else:
            if pos.x()+85 > parent.width() or pos.x()+85 < 0 : deltaX = parent.width()-(pos.x()+85)
            else: deltaX = 0
            if pos.y()+135 > parent.height() or pos.y()+135 < 0: deltaY = parent.height()-(pos.y()+135)
            else: deltaY = 0 

            self.setGeometry(QtCore.QRect(pos.x()+deltaX, pos.y()+deltaY, 85, 135))

        self.virtualGeometry = QtCore.QRect(pos.x()-hitboxOffset+deltaX, pos.y()-hitboxOffset+deltaY, self.width()+hitboxOffset*2, self.height()+hitboxOffset*2)
        self.setObjectName("SBN_subMenu")
        self.menuObject = SubMenuContent(self, buttonTexts)
        for btn in self.menuObject.content: btn.Released.connect(self.close)
        self.show()


class GroupZone(QtWidgets.QFrame):
    def __init__(self, parent, pos, w, h):
        super(GroupZone, self).__init__(parent)
        self.styleSheet = {
            "normal":"background-color: #009ACD; border: 1px solid #104E8B; border-radius: 2px", 
            "highlighted":"background-color: #222; border: 1px solid #EE7600; border-radius: 2px"
            }
        self.setStyleSheet(self.styleSheet["normal"])
        self.setGeometry(QtCore.QRect(pos.x(), pos.y(), w, h))

        self.show()

    def shiftStyleSheet(self, name):
        self.setStyleSheet(self.styleSheet[name])
        self.update()

class SbnListWidget(QtWidgets.QListWidget):

    mouseRelease = QtCore.Signal()
    widgetDoubleClicked = QtCore.Signal()
    keyPressed = QtCore.Signal(QtCore.QEvent)
    CGCalled = QtCore.Signal(bool)
    FxPressed = QtCore.Signal(QtCore.QEvent)
    noAdding = QtCore.Signal()
    subMenuButtonClicked = QtCore.Signal(int)
    subMenuCalled = QtCore.Signal()
    getsFocus = QtCore.Signal(bool)

    def __init__(self, parent, frameGeometry):
        super(SbnListWidget, self).__init__(parent)
        self.mouseReleased = True
        self.controlPressed = False
        self.subMenu = None
        self.hierarchyDrawingWid = None
        self.objectFrame = QtCore.QRect(0, 0, frameGeometry[0], frameGeometry[1])
        self.setMouseTracking(True)
        self.indentLenght = 12
        self.groups = []

    def setIndentLenght(self, string):
        value = len(string)
        self.indentLenght = 3*value

    def focusInEvent(self, event):
        self.getsFocus.emit(True)

    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_C and event.modifiers() == QtCore.Qt.AltModifier:
            # self.CGCalled.emit(True)
            pass

        elif event.key() == QtCore.Qt.Key_F1 or event.key() == QtCore.Qt.Key_F2:
            self.FxPressed.emit(event)
        else:
            self.keyPressed.emit(event)

    def mouseReleaseEvent(self, event):
        self.mouseReleased = True
        self.updateGroups()
        self.mouseRelease.emit()

    def mousePressEvent(self, event):
        self.mouseReleased = False 

        if QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.ControlModifier and not QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier and\
         self.subMenu is None and event.button() != QtCore.Qt.RightButton:
            self.clearSelection()
            self.noAdding.emit()

        if len(self.selectedItems()) == 0 or event.button() == QtCore.Qt.LeftButton: super(SbnListWidget, self).mousePressEvent(event) # To not overwrite the original function.
        if (event.button() == QtCore.Qt.RightButton and self.currentItem() is not None):
            if self.subMenu is not None: self.subMenu.close()
            self.subMenu = ListSubMenu(self.viewport(), event.pos(), self.currentItem().at)
            self.__initSubMenuContent()
        else:
            if self.subMenu is not None: 
                self.subMenu.close()
                self.subMenu = None

    def mouseMoveEvent(self, event):
        if self.subMenu is not None:
            pos = event.pos()
            if not self.subMenu.virtualGeometry.contains(pos.x(), pos.y()) and not self.visualItemRect(self.currentItem()).contains(pos.x(), pos.y()):
                self.subMenu.close()
                self.subMenu = None

        super(SbnListWidget, self).mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.widgetDoubleClicked.emit()
         # To overwrite the original function. Wherever the user clicks, it now clears the selection.

    def __initSubMenuContent(self):
        self.mouseReleased = True
        self.mouseRelease.emit()
        items = self.selectedItems()
        item = items.pop() if len(items) != 0 else self.currentItem()
        # self.clearSelection()
        item.setSelected(True)
        self.setCurrentItem(item)

        for btn in self.subMenu.menuObject.content:
            btn.Clicked.connect(self.__passSignal)

        self.subMenuCalled.emit()

    def __passSignal(self, btnID):
        self.subMenuButtonClicked.emit(btnID)

    def updateGroups(self):
        content = [self.item(i) for i in xrange(self.count())]

        for item in content:
            item.redraw()

    def drawGroups(self):
        content = [self.item(i) for i in xrange(self.count())]
        self.groups = []
        for item in content:
            if item.isParent:
                if item.group is not None: item.group.close()
                lenghtU = 3+ self.indentLenght*(item.hierarchyDepth)
                lenghtV = self.visualItemRect(item.childrens[len(item.childrens)-1]).bottomLeft().y() - self.visualItemRect(item).bottomLeft().y()
                basePos = self.visualItemRect(item).bottomLeft()
                basePos += QtCore.QPoint(lenghtU,1)
                line = GroupZone(self.viewport(), basePos, 5, lenghtV)
                self.groups.append(line)
                item.set(g=line)

    def clear(self):
        super(SbnListWidget, self).clear()
        self.clearGrps()
    
    def clearGrps(self):
        for item in self.groups:
            item.close()
        self.groups = []

    def clearSelection(self):
        super(SbnListWidget, self).clearSelection()
        self.updateGroups()

class Ui_sbnWindow(object):
    defaultWidth = 301 #For the window itself
    defaultHeight = 750 #Only for the QListWidget
    infos = ["aimConstraint","orientConstraint","parentConstraint","pointConstraint","scaleConstraint","shape","poleVectorConstraint","constraint",\
            "pointOnCurveInfo","clusterHandle","camera","distanceDimShape","expression","follicle","ikHandle","ikEffector"]
    def userResolution():
        user32 = ctypes.windll.user32
        usr = [float(user32.GetSystemMetrics(0)), float(user32.GetSystemMetrics(1))]
        ratioX = usr[0]/1920.0
        ratioY = usr[1]/1080.0
        return ratioX, ratioY  

    def setupUi(self, sbnWindow, res=userResolution()):
        sbnWindow.setObjectName("sbnWindow")
        sbnWindow.resize(302, 600)
        sbnWindow.setMinimumSize(QtCore.QSize(self.defaultWidth, 600))
        sbnWindow.setMaximumSize(QtCore.QSize(self.defaultWidth, 16777215))
        sbnWindow.setFocusPolicy(QtCore.Qt.StrongFocus) 
        self.gridLayoutWidget = QtWidgets.QWidget(sbnWindow)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 20, 301, 61))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.res1LE = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.res1LE.setMinimumSize(QtCore.QSize(146, 25))
        self.res1LE.setObjectName("res1LE")
        self.gridLayout.addWidget(self.res1LE, 0, 0, 1, 1)
        self.res2LE = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.res2LE.setMinimumSize(QtCore.QSize(146, 25))
        self.res2LE.setObjectName("res2LE")
        self.gridLayout.addWidget(self.res2LE, 0, 1, 1, 1)
        self.ex1LE = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.ex1LE.setMinimumSize(QtCore.QSize(146, 25))
        self.ex1LE.setObjectName("ex1LE")
        self.gridLayout.addWidget(self.ex1LE, 1, 0, 1, 1)
        self.ex2LE = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.ex2LE.setMinimumSize(QtCore.QSize(146, 25))
        self.ex2LE.setObjectName("ex2LE")
        self.gridLayout.addWidget(self.ex2LE, 1, 1, 1, 1)
        self.horizontalLayoutWidget = QtWidgets.QWidget(sbnWindow)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 80, 301, 21))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.aoCHKB = QtWidgets.QCheckBox(self.horizontalLayoutWidget)
        self.aoCHKB.setMaximumSize(QtCore.QSize(74, 18))
        self.aoCHKB.setObjectName("aoCHKB")
        self.horizontalLayout.addWidget(self.aoCHKB)
        self.transformsCHKB = QtWidgets.QCheckBox(self.horizontalLayoutWidget)
        self.transformsCHKB.setMaximumSize(QtCore.QSize(75, 18))
        self.transformsCHKB.setObjectName("transformsCHKB")
        self.horizontalLayout.addWidget(self.transformsCHKB)
        self.jointsCHKB = QtWidgets.QCheckBox(self.horizontalLayoutWidget)
        self.jointsCHKB.setEnabled(True)
        self.jointsCHKB.setMaximumSize(QtCore.QSize(54, 18))
        self.jointsCHKB.setObjectName("jointsCHKB")
        self.horizontalLayout.addWidget(self.jointsCHKB)
        self.constraintsCHKB = QtWidgets.QCheckBox(self.horizontalLayoutWidget)
        self.constraintsCHKB.setMaximumSize(QtCore.QSize(79, 18))
        self.constraintsCHKB.setObjectName("constraintsCHKB")
        self.horizontalLayout.addWidget(self.constraintsCHKB)
        self.verticalLayoutWidget = QtWidgets.QWidget(sbnWindow)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 301, 21))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.currentStateLABEL = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.currentStateLABEL.setAlignment(QtCore.Qt.AlignCenter)
        self.currentStateLABEL.setObjectName("currentStateLABEL")
        self.verticalLayout.addWidget(self.currentStateLABEL)
        self.listLayoutWidget = QtWidgets.QWidget(sbnWindow)
        self.listLayoutWidget.setGeometry(QtCore.QRect(0, 170, 301, int(self.defaultHeight*res[1])))
        self.listLayoutWidget.setObjectName("listLayoutWidget")
        self.LWLayout = QtWidgets.QVBoxLayout(self.listLayoutWidget)
        self.LWLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.LWLayout.setContentsMargins(0, 0, 0, 0)
        self.LWLayout.setObjectName("LWLayout")
        self.resultsLW = SbnListWidget(self.listLayoutWidget, (301,int(self.defaultHeight*res[1])))
        self.resultsLW.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.resultsLW.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.resultsLW.setObjectName("resultsLW")
        self.LWLayout.addWidget(self.resultsLW)
        self.horizontalLayoutWidget_2 = QtWidgets.QWidget(sbnWindow)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(0, self.fitUser(), 301, 31))
        self.horizontalLayoutWidget_2.setObjectName("horizontalLayoutWidget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(140, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.swWindowBTN = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
        self.swWindowBTN.setMinimumSize(QtCore.QSize(150, 25))
        self.swWindowBTN.setObjectName("swWindowBTN")
        self.horizontalLayout_2.addWidget(self.swWindowBTN)
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(sbnWindow)
        self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(0, 100, 161, 71))
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.advFilteringLayout1 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.advFilteringLayout1.setContentsMargins(-1, -1, -1, 4)
        self.advFilteringLayout1.setObjectName("advFilteringLayout1")
        self.advFilteringLW = QtWidgets.QListWidget(self.verticalLayoutWidget_3)
        self.advFilteringLW.setMinimumSize(QtCore.QSize(150, 56))
        self.advFilteringLW.setMaximumSize(QtCore.QSize(150, 56))
        self.advFilteringLW.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.advFilteringLW.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)        
        self.advFilteringLW.setObjectName("advFilteringLW")
        for i in range(16):
            QtWidgets.QListWidgetItem(self.advFilteringLW)

        self.advFilteringLayout1.addWidget(self.advFilteringLW)
        self.gridLayoutWidget_2 = QtWidgets.QWidget(sbnWindow)
        self.gridLayoutWidget_2.setGeometry(QtCore.QRect(160, 110, 141, 62))
        self.gridLayoutWidget_2.setObjectName("gridLayoutWidget_2")
        self.advFilteringLayout2 = QtWidgets.QGridLayout(self.gridLayoutWidget_2)
        self.advFilteringLayout2.setContentsMargins(5, 2, 0, 0)
        self.advFilteringLayout2.setVerticalSpacing(0)
        self.advFilteringLayout2.setObjectName("advFilteringLayout2")
        self.liLABEL = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.liLABEL.setMinimumSize(QtCore.QSize(135, 25))
        self.liLABEL.setMaximumSize(QtCore.QSize(135, 25))
        self.liLABEL.setMargin(6)
        self.liLABEL.setObjectName("liLABEL")
        self.advFilteringLayout2.addWidget(self.liLABEL, 0, 0, 1, 1)
        self.itemLN = QtWidgets.QLineEdit(self.gridLayoutWidget_2)
        self.itemLN.setMinimumSize(QtCore.QSize(135, 20))
        self.itemLN.setMaximumSize(QtCore.QSize(135, 20))
        self.itemLN.setPlaceholderText("")
        self.itemLN.setObjectName("itemLN")
        self.advFilteringLayout2.addWidget(self.itemLN, 1, 0, 1, 1)
        self.numberOfItemsLABEL = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.numberOfItemsLABEL.setMinimumSize(QtCore.QSize(135, 20))
        self.numberOfItemsLABEL.setMaximumSize(QtCore.QSize(135, 20))
        self.numberOfItemsLABEL.setAlignment(QtCore.Qt.AlignCenter)
        self.numberOfItemsLABEL.setObjectName("numberOfItemsLABEL")
        self.advFilteringLayout2.addWidget(self.numberOfItemsLABEL, 2, 0, 1, 1)

        self.retranslateUi(sbnWindow)
        QtCore.QMetaObject.connectSlotsByName(sbnWindow)

    def fitUser(self, res=userResolution()):
        size = int((170+self.defaultHeight*res[1])-1)
        return size

    def retranslateUi(self, sbnWindow):
        sbnWindow.setWindowTitle("Search by name")
        self.res1LE.setToolTip("<html><head/><body><p>You can type &quot;@all&quot; to get all the items that match the filters/excluded strings, or &quot;@pre&quot to access to your preselections.</p></body></html>")
        self.res1LE.setPlaceholderText("Research term #1...")
        self.res2LE.setPlaceholderText("Research term #2...")
        self.ex1LE.setPlaceholderText("Exclude term #1...")
        self.ex2LE.setPlaceholderText("Exclude term #2...")
        self.aoCHKB.setText("All objects")
        self.transformsCHKB.setText("Transforms")
        self.jointsCHKB.setText("Joints")
        self.constraintsCHKB.setText("Constraints")
        self.currentStateLABEL.setText("Waiting for keywords...")
        self.swWindowBTN.setText("Undock window...")
        __sortingEnabled = self.advFilteringLW.isSortingEnabled()
        self.advFilteringLW.setSortingEnabled(False)
        for param, i in zip(self.infos, range(16)):
            self.advFilteringLW.item(i).setText(param)

        self.advFilteringLW.setSortingEnabled(__sortingEnabled)
        self.liLABEL.setText("Look into:")
        self.numberOfItemsLABEL.setText("-- potential items found.")