
import sys
import os

from PyQt5 import QtWidgets, uic
import sys

# inherit correct QMainWindow class as defined in UI file
class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        print(os.listdir(os.curdir))
        uic.loadUi('BAT/BAT/src/gui/bat_gui.ui', self)
        self.show()

app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()

