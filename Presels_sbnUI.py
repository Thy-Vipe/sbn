# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Presels_sbnUI.ui'
#
# Created: Sat Nov 21 15:30:26 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtWidgets

class Ui_preselsGUI(object):
    def setupUi(self, preselsGUI):
        preselsGUI.setObjectName("preselsGUI")
        preselsGUI.resize(241, 112)
        preselsGUI.setMaximumSize(241,112)
        preselsGUI.setMinimumSize(241,112)
        self.gridLayoutWidget = QtWidgets.QWidget(preselsGUI)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 50, 141, 61))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.buttonColumn = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.buttonColumn.setContentsMargins(0, 0, 0, 0)
        self.buttonColumn.setVerticalSpacing(0)
        self.buttonColumn.setObjectName("buttonColumn")
        self.ce_presBtn = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.ce_presBtn.setMinimumSize(QtCore.QSize(130, 30))
        self.ce_presBtn.setMaximumSize(QtCore.QSize(130, 30))
        self.ce_presBtn.setObjectName("ce_presBtn")
        self.buttonColumn.addWidget(self.ce_presBtn, 0, 0, 1, 1)
        self.del_presBtn = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.del_presBtn.setObjectName("del_presBtn")
        self.buttonColumn.addWidget(self.del_presBtn, 1, 0, 1, 1)
        self.gridLayoutWidget_2 = QtWidgets.QWidget(preselsGUI)
        self.gridLayoutWidget_2.setGeometry(QtCore.QRect(0, 0, 241, 51))
        self.gridLayoutWidget_2.setObjectName("gridLayoutWidget_2")
        self.nameGrid = QtWidgets.QGridLayout(self.gridLayoutWidget_2)
        self.nameGrid.setContentsMargins(9, -1, 4, -1)
        self.nameGrid.setObjectName("nameGrid")
        self.filnenameLabel = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.filnenameLabel.setObjectName("filnenameLabel")
        self.nameGrid.addWidget(self.filnenameLabel, 0, 0, 1, 1)
        self.name_LE = QtWidgets.QLineEdit(self.gridLayoutWidget_2)
        self.name_LE.setInputMask("")
        self.name_LE.setText("")
        self.name_LE.setObjectName("name_LE")
        self.nameGrid.addWidget(self.name_LE, 0, 1, 1, 1)
        self.verticalLayoutWidget = QtWidgets.QWidget(preselsGUI)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(140, 80, 101, 31))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.cancelLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.cancelLayout.setContentsMargins(11, -1, -1, -1)
        self.cancelLayout.setObjectName("cancelLayout")
        self.cancelBtn = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.cancelBtn.setMinimumSize(QtCore.QSize(80, 23))
        self.cancelBtn.setMaximumSize(QtCore.QSize(80, 23))
        self.cancelBtn.setObjectName("cancelBtn")
        self.cancelLayout.addWidget(self.cancelBtn)

        self.retranslateUi(preselsGUI)
        QtCore.QMetaObject.connectSlotsByName(preselsGUI)

    def retranslateUi(self, preselsGUI):
        preselsGUI.setWindowTitle("Create preselection")
        self.ce_presBtn.setText("Create/edit preselection")
        self.del_presBtn.setText("Delete selected file(s)")
        self.filnenameLabel.setText("Filename: ")
        self.name_LE.setPlaceholderText("No extent")
        self.cancelBtn.setText("Close")

