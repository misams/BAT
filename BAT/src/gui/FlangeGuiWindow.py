from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
"""
For test purposes --> will include "Bolted-Flange"-Window
"""
class AnotherWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Bolted-Flange Window TEST")
        layout.addWidget(self.label)
        self.setLayout(layout)