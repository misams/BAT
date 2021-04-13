from PyQt5 import QtWidgets, uic
"""
Bolted-Flange-Window
"""
class FlangeWindow(QtWidgets.QMainWindow):
    def __init__(self, toBeModified):
        super(FlangeWindow, self).__init__()
        # item to be modified in main-window
        self.toBeModified = toBeModified
        # load *.ui file
        uic.loadUi("/home/sams/git/BAT/BAT/src/gui/bat_flange.ui", self)
        #
        # set window title
        #
        self.setWindowTitle("Bolted Flange Definition")
        #
        # set widgets pointers and connections
        #
        self.nmbrBolts = self.findChild(QtWidgets.QSpinBox, "nmbrBolts")
        self.lineEditPcd = self.findChild(QtWidgets.QLineEdit, "lineEditPcd")
        self.forceCompTable = self.findChild(QtWidgets.QTableWidget, "forceCompTable")
        self.forceLocTable = self.findChild(QtWidgets.QTableWidget, "forceLocTable")
        #
        # button box (bottom)
        self.buttonBox = self.findChild(QtWidgets.QDialogButtonBox, "buttonBox")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.close)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.click_apply)
        #
        # INIT GUI
        self.init_gui()

    # init gui - default settings
    def init_gui(self):
        # force components table init
        self.forceCompTable.setColumnCount(4)
        self.forceCompTable.insertRow(0)
        self.forceCompTable.setHorizontalHeaderLabels(\
            ["FX\n[N]", "FY\n[N]", "FZ\n[N]", "Remark"])
        self.forceCompTable.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.forceCompTable.setItem(0,0,QtWidgets.QTableWidgetItem("0.0"))
        self.forceCompTable.setItem(0,1,QtWidgets.QTableWidgetItem("0.0"))
        self.forceCompTable.setItem(0,2,QtWidgets.QTableWidgetItem("0.0"))
        self.forceCompTable.setItem(0,3,QtWidgets.QTableWidgetItem("e.g. 1000kg + 1.2g down"))

        # force location table init
        self.forceLocTable.setColumnCount(3)
        self.forceLocTable.insertRow(0)
        self.forceLocTable.setHorizontalHeaderLabels(\
            ["X\n[mm]", "Y\n[mm]", "Z\n[mm]"])
        self.forceLocTable.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.forceLocTable.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.forceLocTable.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.forceLocTable.setItem(0,0,QtWidgets.QTableWidgetItem("0.0"))
        self.forceLocTable.setItem(0,1,QtWidgets.QTableWidgetItem("0.0"))
        self.forceLocTable.setItem(0,2,QtWidgets.QTableWidgetItem("0.0"))


    # BUTTON - click apply
    def click_apply(self):
        self.toBeModified.setText("blabla")