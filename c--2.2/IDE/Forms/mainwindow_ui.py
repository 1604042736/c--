# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\王永健\王永健的文件夹\IntegratedProjects\c--\c--2.2\IDE\Forms\mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 618)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tw_main = QtWidgets.QTabWidget(self.centralwidget)
        self.tw_main.setObjectName("tw_main")
        self.gridLayout.addWidget(self.tw_main, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1000, 23))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_run = QtWidgets.QMenu(self.menubar)
        self.menu_run.setObjectName("menu_run")
        MainWindow.setMenuBar(self.menubar)
        self.new_action = QtWidgets.QAction(MainWindow)
        self.new_action.setObjectName("new_action")
        self.save_action = QtWidgets.QAction(MainWindow)
        self.save_action.setObjectName("save_action")
        self.open_action = QtWidgets.QAction(MainWindow)
        self.open_action.setObjectName("open_action")
        self.run_action = QtWidgets.QAction(MainWindow)
        self.run_action.setObjectName("run_action")
        self.menu.addAction(self.new_action)
        self.menu.addAction(self.save_action)
        self.menu.addAction(self.open_action)
        self.menu_run.addAction(self.run_action)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_run.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "C-- IDE"))
        self.menu.setTitle(_translate("MainWindow", "文件"))
        self.menu_run.setTitle(_translate("MainWindow", "运行"))
        self.new_action.setText(_translate("MainWindow", "新建"))
        self.save_action.setText(_translate("MainWindow", "保存"))
        self.open_action.setText(_translate("MainWindow", "打开"))
        self.run_action.setText(_translate("MainWindow", "运行"))
