from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QTextEdit
from PyQt5 import QtGui
"""
Bolt-Info-Window
"""
class BoltInfoWindow(QWidget):
    def __init__(self, db_path=None):
        super(BoltInfoWindow, self).__init__()
        # database path
        bolt_info_file = db_path + "/bolt.info"
        # set window title
        self.setWindowTitle("Bolt Info")
        # set layout and add widgets
        layout = QVBoxLayout()
        label = QLabel("Bolt-Info Text: {0:^}".format(str(bolt_info_file)))
        layout.addWidget(label)
        self.setLayout(layout)
        self.resize(800, 500) # resize window
        # add QTextEdit for file display
        textEdit = QTextEdit()
        # read "bolt.info" file
        bolt_info_text = ''
        with open(bolt_info_file) as fid:
            line = fid.readline() # first line in file
            while line:
                if line[0]=='#':
                    pass # ignore comment lines --> more elegant version of while/if??
                else:
                    bolt_info_text += line
                line = fid.readline()
        textEdit.setText(bolt_info_text)
        textEdit.setReadOnly(True)
        layout.addWidget(textEdit)
        # close window button
        Quit = QPushButton('Close', self) #button object
        Quit.setGeometry(10, 10, 60, 35) # Set the position and size of the button
        Quit.setStyleSheet("font-weight: bold") # Set the style and color of the button
        Quit.clicked.connect(self.close) # Close the window after clicking the button
        layout.addWidget(Quit)