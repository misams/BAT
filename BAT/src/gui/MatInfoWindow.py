from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
"""
Material-Info-Window
"""
class MatInfoWindow(QWidget):
    def __init__(self, materials=None):
        super(MatInfoWindow, self).__init__()
        #
        # material database
        self.materals = materials
        #
        # set window title
        self.setWindowTitle("Material Data Info")
        #
        layout = QVBoxLayout()
        self.label = QLabel("Used material data:")
        self.mat_table = QTableWidget()
        layout.addWidget(self.label)
        layout.addWidget(self.mat_table)
        self.setLayout(layout)
        #
        # fill and format material table
        self.mat_table.setColumnCount(7) # init material-info-table
        #self.mat_table.insertRow(0)
        self.mat_table.setHorizontalHeaderLabels(\
            ["Material-ID", "Young's\nModulus\n[MPa]", "Ultimate\nStrength\n[MPa]", "Yield\nStrength\n[MPa]",\
             "CTE\n[1/K]", "Ultimate\nShear Strength\n[MPa]", "Yield\nShear Strength\n[MPa]"])
        # fill table
        for i, value in enumerate(self.materals.materials.values()):
            self.mat_table.insertRow(i)
            self.mat_table.setItem(i, 0, QTableWidgetItem(value.name))