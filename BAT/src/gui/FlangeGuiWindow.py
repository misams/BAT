from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
"""
Bolted-Flange-Window
"""
class FlangeWindow(QMainWindow):
    def __init__(self):
        super(FlangeWindow, self).__init__()
        # load *.ui file
        uic.loadUi("/home/sams/git/BAT/BAT/src/gui/bat_flange.ui", self)
        #
        # set window title
        #
        self.setWindowTitle("Bolted Flange Definition")

