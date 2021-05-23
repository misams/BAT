from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QTextEdit, QSizePolicy, QScrollArea, QAction
from PyQt5 import QtGui, QtCore
from PyQt5.Qt import Qt
"""
Image-Info-Window

Simply plots image as help info
"""
class ImageInfoWindow(QMainWindow):
    def __init__(self, image_path=None, width=700, height=600, title=""):
        super(ImageInfoWindow, self).__init__()
        self.scaleFactor = 1.0
        # image label where image is placed
        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)
        # scrollArea
        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Light)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(True)
        # set centralWidget
        self.setCentralWidget(self.scrollArea)
        # add image to label
        self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(image_path)))
        self.imageLabel.show()
        self.imageLabel.adjustSize()
        # set window title and size
        self.setWindowTitle(title)
        self.resize(width, height)

    # zoom with mouse wheel
    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if event.angleDelta().y() > 0 and modifiers == QtCore.Qt.ControlModifier:
            self.zoomOut()
        elif event.angleDelta().y() < 0 and modifiers == QtCore.Qt.ControlModifier:
            self.zoomIn()

    def zoomIn(self):
        self.scaleImage(1.1)

    def zoomOut(self):
        self.scaleImage(0.9)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)