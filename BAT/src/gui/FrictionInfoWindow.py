from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QTextEdit, QSizePolicy, QScrollArea
from PyQt5 import QtGui
"""
Friction-Info-Window
"""
class FrictionInfoWindow(QMainWindow):
    def __init__(self, fric_info_table_path=None):
        super(FrictionInfoWindow, self).__init__()
        # image label where image is placed
        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)
        # scrollArea
        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(True)
        # set centralWidget
        self.setCentralWidget(self.scrollArea)
        # add image to label
        pic = fric_info_table_path
        self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(pic)))
        self.imageLabel.show()
        self.imageLabel.adjustSize()
        # set window title and size
        self.setWindowTitle("Friction Info Window")
        self.resize(770, 600)
