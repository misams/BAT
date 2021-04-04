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
        self.lineEdit_pcd = self.findChild(QtWidgets.QLineEdit, "lineEdit_pcd")
        self.buttonBox = self.findChild(QtWidgets.QDialogButtonBox, "buttonBox")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.close)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.click_apply)

    def click_apply(self):
        self.toBeModified.setText("blabla")